from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import psycopg2
import os
import json
from datetime import datetime
import uuid
import base64
import io
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

# CORS - السماح لجميع الطلبات (مؤقتاً للتشخيص)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Rate Limiting - منع الإغراق
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per minute", "1000 per hour"]
)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create clients table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            client_code VARCHAR(50) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create projects table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            client_code VARCHAR(50) NOT NULL,
            project_name VARCHAR(255) NOT NULL,
            project_data TEXT NOT NULL,
            thumbnail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

# Initialize database on startup
with app.app_context():
    try:
        init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database init error: {e}")

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Despro API is running!"})

@app.route('/api/health')
@limiter.exempt  # بدون rate limiting للـ health check
def health_check():
    """Lightweight health check for uptime monitoring"""
    return "OK", 200

@app.route('/api/all-projects')
def get_all_projects():
    """Get all projects (admin only - for debugging)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT id, client_code, project_name, created_at 
            FROM projects 
            ORDER BY created_at DESC
            LIMIT 50
        ''')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        projects = []
        for row in rows:
            projects.append({
                "id": row[0],
                "client_code": row[1],
                "project_name": row[2],
                "created_at": row[3].isoformat() if row[3] else None
            })
        
        return jsonify({"success": True, "count": len(projects), "projects": projects})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/client/register', methods=['POST'])
def register_client():
    """Register a new client with unique code"""
    data = request.json
    client_code = data.get('client_code')
    
    if not client_code:
        # Generate random code
        client_code = str(uuid.uuid4())[:8].upper()
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO clients (client_code) VALUES (%s) ON CONFLICT (client_code) DO NOTHING RETURNING client_code',
            (client_code,)
        )
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "client_code": client_code,
            "message": "تم التسجيل بنجاح"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/project/save', methods=['POST'])
def save_project():
    """Save a project for a client"""
    data = request.json
    client_code = data.get('client_code')
    project_name = data.get('project_name', 'مشروع بدون اسم')
    project_data = data.get('project_data')  # JSON string of canvas data
    thumbnail = data.get('thumbnail', '')  # Base64 image
    
    if not client_code or not project_data:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Ensure client exists
        cur.execute(
            'INSERT INTO clients (client_code) VALUES (%s) ON CONFLICT (client_code) DO NOTHING',
            (client_code,)
        )
        
        # Save project
        cur.execute('''
            INSERT INTO projects (client_code, project_name, project_data, thumbnail)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (client_code, project_name, project_data, thumbnail))
        
        project_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "project_id": project_id,
            "message": "تم حفظ المشروع بنجاح"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/project/update/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update an existing project"""
    data = request.json
    client_code = data.get('client_code')
    project_name = data.get('project_name')
    project_data = data.get('project_data')
    thumbnail = data.get('thumbnail')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            UPDATE projects 
            SET project_name = COALESCE(%s, project_name),
                project_data = COALESCE(%s, project_data),
                thumbnail = COALESCE(%s, thumbnail),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND client_code = %s
            RETURNING id
        ''', (project_name, project_data, thumbnail, project_id, client_code))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if result:
            return jsonify({"success": True, "message": "تم تحديث المشروع"})
        else:
            return jsonify({"success": False, "error": "Project not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/projects/<client_code>', methods=['GET'])
def get_projects(client_code):
    """Get all projects for a client"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT id, project_name, thumbnail, created_at, updated_at
            FROM projects
            WHERE client_code = %s
            ORDER BY updated_at DESC
        ''', (client_code,))
        
        projects = []
        for row in cur.fetchall():
            projects.append({
                "id": row[0],
                "name": row[1],
                "thumbnail": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "updated_at": row[4].isoformat() if row[4] else None
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "projects": projects,
            "count": len(projects)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/project/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a single project by ID"""
    client_code = request.args.get('client_code')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT id, project_name, project_data, thumbnail, created_at, updated_at
            FROM projects
            WHERE id = %s AND client_code = %s
        ''', (project_id, client_code))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            return jsonify({
                "success": True,
                "project": {
                    "id": row[0],
                    "name": row[1],
                    "data": row[2],
                    "thumbnail": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                    "updated_at": row[5].isoformat() if row[5] else None
                }
            })
        else:
            return jsonify({"success": False, "error": "Project not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/project/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    client_code = request.args.get('client_code')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            DELETE FROM projects
            WHERE id = %s AND client_code = %s
            RETURNING id
        ''', (project_id, client_code))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if result:
            return jsonify({"success": True, "message": "تم حذف المشروع"})
        else:
            return jsonify({"success": False, "error": "Project not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# === Server-Side A4 PDF Generation (iOS Fix) ===
# ============================================

@app.route('/api/generate-a4-pdf', methods=['POST'])
@limiter.limit("10 per minute")  # حد 10 طلبات في الدقيقة
def generate_a4_pdf():
    """
    Generate A4 PDF with repeated card images - Server Side Rendering
    This bypasses iOS Safari canvas memory limits
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # استخراج البيانات
        image_base64 = data.get('image')  # صورة البطاقة بصيغة Base64
        card_width = data.get('cardWidth', 300)  # عرض البطاقة بالبكسل
        card_height = data.get('cardHeight', 200)  # ارتفاع البطاقة بالبكسل
        copies = data.get('copies', 1)  # عدد النسخ المطلوبة
        show_cut_lines = data.get('showCutLines', False)  # خطوط القص
        is_transparent = data.get('isTransparent', False)  # خلفية شفافة
        
        if not image_base64:
            return jsonify({"success": False, "error": "No image provided"}), 400
        
        # تحويل Base64 إلى صورة
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        image_data = base64.b64decode(image_base64)
        card_image = Image.open(io.BytesIO(image_data))
        
        # تحويل إلى RGB إذا كانت RGBA وليست شفافة
        if card_image.mode == 'RGBA' and not is_transparent:
            background = Image.new('RGB', card_image.size, (255, 255, 255))
            background.paste(card_image, mask=card_image.split()[3])
            card_image = background
        elif card_image.mode != 'RGB' and card_image.mode != 'RGBA':
            card_image = card_image.convert('RGB')
        
        # أبعاد A4 بدقة 300 DPI
        A4_WIDTH_PX = 2480
        A4_HEIGHT_PX = 3508
        GAP = 40  # الفراغ بين البطاقات
        
        # حساب التوزيع الأمثل (portrait vs landscape)
        portrait_cols = (A4_WIDTH_PX + GAP) // (card_width + GAP)
        portrait_rows = (A4_HEIGHT_PX + GAP) // (card_height + GAP)
        portrait_count = portrait_cols * portrait_rows
        
        landscape_cols = (A4_HEIGHT_PX + GAP) // (card_width + GAP)
        landscape_rows = (A4_WIDTH_PX + GAP) // (card_height + GAP)
        landscape_count = landscape_cols * landscape_rows
        
        # اختيار الاتجاه الأفضل
        if landscape_count > portrait_count:
            canvas_w, canvas_h = A4_HEIGHT_PX, A4_WIDTH_PX
            cols, rows = landscape_cols, landscape_rows
            orientation = 'landscape'
        else:
            canvas_w, canvas_h = A4_WIDTH_PX, A4_HEIGHT_PX
            cols, rows = portrait_cols, portrait_rows
            orientation = 'portrait'
        
        max_copies = cols * rows
        actual_copies = min(copies, max_copies)
        
        # إنشاء صورة A4
        if is_transparent:
            a4_image = Image.new('RGBA', (canvas_w, canvas_h), (255, 255, 255, 0))
        else:
            a4_image = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
        
        # حساب نقطة البداية للتوسيط
        total_w = cols * card_width + (cols - 1) * GAP
        total_h = rows * card_height + (rows - 1) * GAP
        start_x = (canvas_w - total_w) // 2
        start_y = (canvas_h - total_h) // 2
        
        # تغيير حجم البطاقة إذا لزم الأمر
        if card_image.size != (card_width, card_height):
            card_image = card_image.resize((card_width, card_height), Image.Resampling.LANCZOS)
        
        # رسم البطاقات
        drawn = 0
        for row in range(rows):
            for col in range(cols):
                if drawn >= actual_copies:
                    break
                
                x = start_x + col * (card_width + GAP)
                y = start_y + row * (card_height + GAP)
                
                if card_image.mode == 'RGBA':
                    a4_image.paste(card_image, (x, y), card_image)
                else:
                    a4_image.paste(card_image, (x, y))
                
                drawn += 1
            if drawn >= actual_copies:
                break
        
        # رسم خطوط القص إذا مطلوبة
        if show_cut_lines:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(a4_image)
            cut_color = (200, 200, 200)  # رمادي فاتح
            dash_length = 15
            
            drawn_lines = 0
            for row in range(rows):
                for col in range(cols):
                    if drawn_lines >= actual_copies:
                        break
                    
                    x = start_x + col * (card_width + GAP)
                    y = start_y + row * (card_height + GAP)
                    
                    # خط علوي
                    for dx in range(0, card_width, dash_length * 2):
                        draw.line([(x + dx, y), (x + min(dx + dash_length, card_width), y)], fill=cut_color, width=1)
                    
                    # خط سفلي
                    for dx in range(0, card_width, dash_length * 2):
                        draw.line([(x + dx, y + card_height), (x + min(dx + dash_length, card_width), y + card_height)], fill=cut_color, width=1)
                    
                    # خط يسار
                    for dy in range(0, card_height, dash_length * 2):
                        draw.line([(x, y + dy), (x, y + min(dy + dash_length, card_height))], fill=cut_color, width=1)
                    
                    # خط يمين
                    for dy in range(0, card_height, dash_length * 2):
                        draw.line([(x + card_width, y + dy), (x + card_width, y + min(dy + dash_length, card_height))], fill=cut_color, width=1)
                    
                    drawn_lines += 1
                if drawn_lines >= actual_copies:
                    break
        
        # إنشاء PDF
        pdf_buffer = io.BytesIO()
        
        # تحديد اتجاه الصفحة
        if orientation == 'landscape':
            page_size = (A4[1], A4[0])  # A4 مقلوبة
        else:
            page_size = A4
        
        c = canvas.Canvas(pdf_buffer, pagesize=page_size)
        
        # تحويل الصورة لـ buffer
        img_buffer = io.BytesIO()
        if is_transparent:
            a4_image.save(img_buffer, format='PNG')
        else:
            a4_image.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        
        # رسم الصورة على PDF
        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, 0, 0, width=page_size[0], height=page_size[1])
        
        c.save()
        pdf_buffer.seek(0)
        
        # إرجاع الملف
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'design-A4-{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        print(f"A4 PDF Generation Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/a4-info', methods=['POST'])
def get_a4_info():
    """
    Get A4 layout information without generating PDF
    Returns: max copies, orientation, etc.
    """
    try:
        data = request.get_json()
        
        card_width = data.get('cardWidth', 300)
        card_height = data.get('cardHeight', 200)
        
        A4_WIDTH_PX = 2480
        A4_HEIGHT_PX = 3508
        GAP = 40
        
        # Portrait
        portrait_cols = (A4_WIDTH_PX + GAP) // (card_width + GAP)
        portrait_rows = (A4_HEIGHT_PX + GAP) // (card_height + GAP)
        portrait_count = portrait_cols * portrait_rows
        
        # Landscape
        landscape_cols = (A4_HEIGHT_PX + GAP) // (card_width + GAP)
        landscape_rows = (A4_WIDTH_PX + GAP) // (card_height + GAP)
        landscape_count = landscape_cols * landscape_rows
        
        if landscape_count > portrait_count:
            return jsonify({
                "success": True,
                "maxCopies": landscape_count,
                "cols": landscape_cols,
                "rows": landscape_rows,
                "orientation": "landscape"
            })
        else:
            return jsonify({
                "success": True,
                "maxCopies": portrait_count,
                "cols": portrait_cols,
                "rows": portrait_rows,
                "orientation": "portrait"
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
