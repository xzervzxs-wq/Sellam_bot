# 🎨 استوديو المصممين - Despro

**Professional Design Studio for Arabic Typography & Designs**

## 📁 Project Structure

```
despro/
├── index.html          # Main HTML file with complete UI structure
├── css/
│   └── style.css      # All styling (responsive, Tailwind-compatible)
├── js/
│   └── app.js         # Main application logic (5200+ lines)
├── assets/            # Future: User assets, templates
└── Official.json      # Quranic data library (24MB)
```

## ✨ Key Features

### 🖼️ Image & Design Tools
- ✅ Image distortion from side handles (stretch/compress)
- ✅ Gradient application to all images (no restrictions)
- ✅ Colored image stretching support
- ✅ Smart text/shape/assets insertion

### 📱 Mobile & Export Optimization
- ✅ iPhone A4 export fixes:
  - Font loading via `document.fonts.ready`
  - Image to Base64 conversion (iOS compatibility)
  - Warm-up render technique for reliability
- ✅ PDF/A4 Export with:
  - Dynamic format selection (PNG for transparent, JPEG 85% for opaque)
  - Aspect ratio preservation
  - Smart DPI reduction (200 DPI)
  - File size: 5-25 MB (down from 33 MB)

### 🎭 Design Features
- ✅ Transparent background mode with checkerboard pattern
- ✅ Button/control scaling with zoom bounds
- ✅ CSS variables for theme customization (`--card-zoom`, `--primary-color`, etc.)
- ✅ Multiple Arabic fonts (37 fonts from Google Fonts)

### 🔐 Authentication & Integration
- ✅ Premium code verification system
- ✅ Telegram bot integration
- ✅ WhatsApp login links
- ✅ GitHub API integration for Official.json updates

## 🚀 Getting Started

### Local Development
```bash
# Simply open index.html in a browser
# No build process needed

# For development with live reload:
# Use VS Code Live Server or similar
```

### Required Files
- `index.html` - Main application file
- `css/style.css` - All styling (linked externally)
- `js/app.js` - All application logic (linked externally)
- `Official.json` - Quranic data (fetched from GitHub)

## 📊 Code Statistics
- **Original**: 1 monolithic HTML file (6593 lines)
- **Restructured**:
  - `index.html`: 851 lines (HTML structure)
  - `style.css`: 476 lines (CSS styling)
  - `app.js`: 5263 lines (JavaScript logic)

## 🔧 Browser Compatibility
- ✅ Chrome/Chromium (desktop & mobile)
- ✅ Safari (iOS 14+)
- ✅ Firefox
- ✅ Edge

## 📦 External Dependencies (CDN)
- Tailwind CSS
- html2canvas
- html-to-image
- jsPDF
- Font Awesome 6.4
- Google Fonts (37 Arabic fonts)
- PDF.js

## 🔄 Planned Improvements
- [ ] Split `app.js` into modular files (ui.js, canvas.js, export.js, etc.)
- [ ] Build system setup (Webpack/Vite)
- [ ] Premium/Subscription system
- [ ] Database integration
- [ ] Custom domain hosting
- [ ] PWA support

## 🛡️ Safety Notes
- ✅ Original file backed up: `Dalal_studio_lasso.backup.20260123_175753.html`
- ✅ All functionality preserved from original
- ✅ CSS fully extracted (no inline styles remaining)
- ✅ JavaScript extracted (only external app.js loaded)

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
