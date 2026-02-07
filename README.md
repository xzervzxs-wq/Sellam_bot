# 📖 المصحف الرقمي التفاعلي | Interactive Digital Quran

**مشروع مفتوح المصدر للقرآن الكريم مع إحداثيات الآيات التفاعلية**

[![القرآن الكريم](https://img.shields.io/badge/القرآن-الكريم-green?style=for-the-badge)](https://github.com/xzervzxs-wq/Sellam_bot)
[![عدد الصفحات](https://img.shields.io/badge/الصفحات-604-gold?style=for-the-badge)](https://github.com/xzervzxs-wq/Sellam_bot/tree/main/quran/pages)
[![عدد الآيات](https://img.shields.io/badge/الآيات-6236-blue?style=for-the-badge)](https://github.com/xzervzxs-wq/Sellam_bot/blob/main/quran/ayat_map)

## 🌟 المميزات الرئيسية

### 📱 عارض المصحف التفاعلي
- ✅ **604 صفحة SVG** عالية الجودة (مصحف المدينة المنورة)
- ✅ **إحداثيات 6236 آية** للنقر المباشر على أي آية
- ✅ **السحب للتنقل** بين الصفحات (Swipe Navigation)
- ✅ **الوضع الليلي** (Dark Mode) لراحة العين
- ✅ **شريط الأجزاء** للانتقال السريع بين الأجزاء الـ 30
- ✅ **البحث في القرآن** بالسورة أو رقم الصفحة

### 🎧 الاستماع والتفسير
- ✅ **7 قراء** (الشريم، السديس، العفاسي، الحصري، المنشاوي، ...)
- ✅ **4 تفاسير** (الجلالين، ابن كثير، الميسر، البغوي)
- ✅ **نقر على الآية** = استماع + تفسير + حفظ

### 🔖 العلامات والحفظ
- ✅ **حفظ آخر صفحة** تلقائياً
- ✅ **علامات مرجعية** متعددة
- ✅ **شريط تقدم القراءة**

### 📐 إحداثيات الآيات (Ayat Coordinates)
ملف `ayat_map` يحتوي على إحداثيات كل آية في كل صفحة بتنسيق JSON:
```json
{
  "1": [
    {"surah": 1, "ayah": 1, "path": "M100,50 L200,50..."},
    {"surah": 1, "ayah": 2, "path": "M100,80 L200,80..."}
  ]
}
```

## 📁 هيكل المشروع

```
quran/
├── index.html          # الملف الرئيسي للمصحف التفاعلي
├── ayat_map            # إحداثيات جميع الآيات (JSON)
└── pages/              # 604 صفحة SVG
    ├── 001.svg         # سورة الفاتحة
    ├── 002.svg
    ├── ...
    └── 604.svg         # سورة الناس
```

## 🚀 طريقة الاستخدام

### للمطورين
```bash
# استنساخ المشروع
git clone https://github.com/xzervzxs-wq/Sellam_bot.git

# فتح المصحف
open quran/index.html
```

### للاستخدام المباشر
- **الرابط**: [المصحف الرقمي](https://sellam-bot.vercel.app/quran/)

## 🔗 الموارد المتاحة

| المورد | الرابط | الوصف |
|--------|--------|-------|
| صفحات المصحف | `quran/pages/` | 604 صفحة SVG |
| إحداثيات الآيات | `quran/ayat_map` | خريطة النقر التفاعلي |
| التطبيق الكامل | `quran/index.html` | المصحف التفاعلي |

## 🔍 الكلمات المفتاحية (للبحث)

`القرآن الكريم` `المصحف الرقمي` `Quran SVG` `Quran Coordinates` `إحداثيات الآيات` `ayat map` `quran interactive` `مصحف المدينة` `تفسير القرآن` `استماع القرآن` `quran api` `quran json` `صفحات القرآن` `digital mushaf` `quran pages svg` `arabic quran` `holy quran` `quran reader` `quran app` `تطبيق قرآن` `مصحف تفاعلي`

## 📊 الإحصائيات

- **عدد السور**: 114 سورة
- **عدد الآيات**: 6,236 آية
- **عدد الصفحات**: 604 صفحة
- **عدد الأجزاء**: 30 جزء
- **عدد الأحزاب**: 60 حزب

## 🤝 المساهمة

نرحب بأي مساهمة لتحسين المشروع:
- إضافة تفاسير جديدة
- إضافة قراء جدد
- تحسين إحداثيات الآيات
- إصلاح الأخطاء

## 📜 الترخيص

هذا المشروع مفتوح المصدر لنشر القرآن الكريم.  
**﴿وَرَتِّلِ الْقُرْآنَ تَرْتِيلًا﴾**

## 🙏 الدعاء

اللهم اجعل هذا العمل خالصاً لوجهك الكريم، واجعله صدقة جارية لنا ولوالدينا.

---

**صنع بـ ❤️ لخدمة كتاب الله**

## 📝 License
All rights reserved © 2024 Sellam_bot

---

**Next Step**: Consider splitting `js/app.js` into:
- `js/app.js` - Initialization
- `js/ui.js` - UI element handling
- `js/canvas.js` - Canvas drawing
- `js/export.js` - PDF/image export
- `js/state.js` - Undo/Redo & localStorage
- `js/auth.js` - Premium code verification
- `js/utils.js` - Helper functions
