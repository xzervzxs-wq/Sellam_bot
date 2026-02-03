from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import psycopg2
import os
import json
from datetime import datetime
import uuid
import requests
import base64
from io import BytesIO

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
# === Image Proxy for iOS CORS Issues ===
# ============================================

@app.route('/api/image-proxy', methods=['POST'])
@limiter.limit("30 per minute")
def image_proxy():
    """
    Proxy لجلب الصور وتحويلها لـ Base64
    يحل مشكلة CORS على iOS Safari
    """
    try:
        data = request.get_json()
        image_url = data.get('url')
        
        if not image_url:
            return jsonify({"success": False, "error": "URL مطلوب"}), 400
        
        # التحقق من أن الرابط هو صورة
        if not any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', 'image']):
            # لا نمنع، قد تكون صورة بدون امتداد واضح
            pass
        
        # جلب الصورة من السيرفر الخارجي
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'image/*,*/*',
            'Referer': image_url
        }
        
        response = requests.get(image_url, headers=headers, timeout=15, stream=True)
        
        if response.status_code != 200:
            return jsonify({"success": False, "error": f"فشل جلب الصورة: {response.status_code}"}), 400
        
        # تحويل لـ Base64
        content_type = response.headers.get('Content-Type', 'image/png')
        if 'image' not in content_type:
            content_type = 'image/png'
        
        image_data = response.content
        base64_data = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:{content_type};base64,{base64_data}"
        
        return jsonify({
            "success": True,
            "dataUrl": data_url,
            "contentType": content_type,
            "size": len(image_data)
        })
        
    except requests.Timeout:
        return jsonify({"success": False, "error": "انتهت مهلة الاتصال"}), 408
    except requests.RequestException as e:
        return jsonify({"success": False, "error": f"خطأ في الاتصال: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/batch-image-proxy', methods=['POST'])
@limiter.limit("10 per minute")
def batch_image_proxy():
    """
    Proxy لجلب عدة صور دفعة واحدة
    أكثر كفاءة من طلب كل صورة على حدة
    """
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls or not isinstance(urls, list):
            return jsonify({"success": False, "error": "قائمة URLs مطلوبة"}), 400
        
        if len(urls) > 20:
            return jsonify({"success": False, "error": "الحد الأقصى 20 صورة"}), 400
        
        results = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'image/*,*/*'
        }
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', 'image/png')
                    if 'image' not in content_type:
                        content_type = 'image/png'
                    base64_data = base64.b64encode(response.content).decode('utf-8')
                    results[url] = {
                        "success": True,
                        "dataUrl": f"data:{content_type};base64,{base64_data}"
                    }
                else:
                    results[url] = {"success": False, "error": f"Status {response.status_code}"}
            except Exception as e:
                results[url] = {"success": False, "error": str(e)}
        
        return jsonify({
            "success": True,
            "results": results,
            "processed": len(results)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

