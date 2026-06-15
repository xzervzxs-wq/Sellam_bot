#!/bin/bash

# 🚀 Deploy Preparation Script
# يحضر مجلد despro للنشر على الاستضافة

echo "🎨 ============================================"
echo "   استوديو المصممين - Despro Deployment"
echo "=============================================="
echo ""

# تحقق من وجود المجلد
if [ ! -d "/workspaces/Sellam_bot/despro" ]; then
    echo "❌ خطأ: مجلد despro غير موجود!"
    exit 1
fi

cd /workspaces/Sellam_bot

echo "📦 جاري إنشاء ملف مضغوط..."
echo ""

# حذف أي ملف zip قديم
rm -f despro-deployment.zip 2>/dev/null

# إنشاء ملف zip
zip -r despro-deployment.zip despro/ \
    -x "despro/.git/*" \
    -x "despro/node_modules/*" \
    -x "despro/.DS_Store" \
    -x "despro/.gitignore"

echo ""
echo "✅ تم إنشاء الملف المضغوط بنجاح!"
echo ""
echo "📊 معلومات الملف:"
ls -lh despro-deployment.zip
echo ""
echo "📁 محتويات المجلد:"
cd despro
find . -type f -not -path "./.git/*" | wc -l | xargs echo "   - عدد الملفات:"
du -sh . | awk '{print "   - الحجم الكلي: " $1}'
echo ""
echo "📋 الملفات الأساسية:"
ls -lh index.html 2>/dev/null | awk '{print "   ✓ " $9 " (" $5 ")"}'
ls -lh Official.json 2>/dev/null | awk '{print "   ✓ " $9 " (" $5 ")"}'
ls -lh js/app.js 2>/dev/null | awk '{print "   ✓ js/" $9 " (" $5 ")"}'
ls -lh css/style.css 2>/dev/null | awk '{print "   ✓ css/" $9 " (" $5 ")"}'
echo ""
echo "🌐 خطوات النشر:"
echo "   1. حمّل ملف despro-deployment.zip"
echo "   2. ارفعه على cPanel الخاص بك"
echo "   3. فك الضغط في public_html"
echo "   4. افتح الموقع: https://yourdomain.com"
echo ""
echo "📖 للمزيد من التفاصيل، راجع: despro/DEPLOYMENT_GUIDE.md"
echo ""
echo "✨ جاهز للنشر! 🚀"
echo ""
