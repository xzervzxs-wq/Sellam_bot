// ==========================================
//  صانع بطاقات الخصومات (Discount Card Maker)
//  يستخدم addAssetToCanvas مثل الباركود والسوشيال
// ==========================================

let discountCurrentTemplate = 1;
let discountUploadedImage = null;

function openDiscountModal() {
    const modal = document.getElementById('discountModal');
    modal.style.display = 'flex';
    // Reset form
    document.getElementById('discountProdName').value = '';
    document.getElementById('discountProdPrice').value = '';
    document.getElementById('discountProdOldPrice').value = '';
    document.getElementById('discountImgPreview').classList.add('hidden');
    document.getElementById('discountUploadPlaceholder').classList.remove('hidden');
    discountUploadedImage = null;
    selectDiscountTemplate(1);
    
    // إظهار/إخفاء شارة Premium
    const badge = document.getElementById('discount-pro-badge');
    if (badge) {
        if (typeof userTier !== 'undefined' && userTier === 'premium') {
            badge.classList.add('hidden');
        } else {
            badge.classList.remove('hidden');
        }
    }
}

function closeDiscountModal() {
    document.getElementById('discountModal').style.display = 'none';
}

function handleDiscountImg(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = new Image();
            img.onload = () => {
                discountUploadedImage = img;
                document.getElementById('discountImgPreview').src = e.target.result;
                document.getElementById('discountImgPreview').classList.remove('hidden');
                document.getElementById('discountUploadPlaceholder').classList.add('hidden');
            };
            img.src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
}

function selectDiscountTemplate(id) {
    discountCurrentTemplate = id;
    document.querySelectorAll('.discount-template-btn').forEach(btn => btn.classList.remove('active', 'border-indigo-600', 'bg-indigo-50', 'opacity-100', 'ring-2', 'ring-indigo-100', 'shadow-md'));
    const activeBtn = document.getElementById('discount-tmpl-' + id);
    if (activeBtn) {
        activeBtn.classList.add('active', 'border-indigo-600', 'bg-indigo-50', 'opacity-100', 'ring-2', 'ring-indigo-100', 'shadow-md');
    }
    
    const colorInput = document.getElementById('discountCardColor');
    const borderColorInput = document.getElementById('discountBorderColor');

    if(id === 3) {
        colorInput.value = "#1f2937";
        borderColorInput.value = "#fbbf24";
    } else if(id === 1) {
        colorInput.value = "#fffbeb";
        borderColorInput.value = "#b45309";
    } else {
        colorInput.value = "#ffffff"; 
        borderColorInput.value = "#4f46e5";
    }
}

function generateDiscountCard() {
    const name = document.getElementById('discountProdName').value || "اسم المنتج";
    const price = document.getElementById('discountProdPrice').value || "00";
    const oldPrice = document.getElementById('discountProdOldPrice').value;
    const bgColor = document.getElementById('discountCardColor').value;
    const borderColor = document.getElementById('discountBorderColor').value;
    
    if (!discountUploadedImage) {
        alert("يرجى اختيار صورة للمنتج أولاً 📸");
        return;
    }

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    const cardW = 600;
    const cardH = 800;
    const scale = 4; // دقة عالية للطباعة
    
    canvas.width = cardW * scale;
    canvas.height = cardH * scale;
    ctx.scale(scale, scale);
    
    function roundRect(x, y, w, h, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + w - radius, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
        ctx.lineTo(x + w, y + h - radius);
        ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
        ctx.lineTo(x + radius, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }

    // حساب لون النص بناءً على الخلفية
    const hex = bgColor.replace('#','');
    const r = parseInt(hex.substring(0,2), 16);
    const g = parseInt(hex.substring(2,4), 16);
    const b = parseInt(hex.substring(4,6), 16);
    const isDark = (r * 0.299 + g * 0.587 + b * 0.114) < 128;
    const mainTextColor = isDark ? "#ffffff" : "#1f2937";
    const accentColor = borderColor;

    // === القالب 1: فخامة (Luxury) ===
    if (discountCurrentTemplate === 1) {
        // الخلفية
        ctx.shadowColor = "rgba(0,0,0,0.15)";
        ctx.shadowBlur = 20;
        ctx.shadowOffsetY = 10;
        ctx.fillStyle = bgColor;
        roundRect(20, 20, cardW - 40, cardH - 40, 40);
        ctx.fill();
        ctx.shadowColor = "transparent";
        
        // الإطار الذهبي
        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 3;
        ctx.strokeRect(50, 50, cardW - 100, cardH - 100);
        
        // الصورة (دائرية)
        ctx.save();
        ctx.beginPath();
        ctx.arc(cardW/2, 280, 200, 0, Math.PI*2);
        ctx.clip();
        ctx.drawImage(discountUploadedImage, cardW/2 - 200, 80, 400, 400);
        ctx.restore();

        const contentY = 530;
        ctx.textAlign = "center";
        
        ctx.font = "bold 50px 'Cairo', sans-serif";
        ctx.fillStyle = mainTextColor;
        ctx.fillText(name, cardW/2, contentY);
        
        ctx.font = "900 65px 'Cairo', sans-serif";
        ctx.fillStyle = accentColor;
        ctx.fillText(price + " ر.س", cardW/2, contentY + 90);
        
        if(oldPrice) {
            ctx.font = "40px 'Cairo', sans-serif";
            ctx.fillStyle = "#9ca3af"; 
            const oldP = oldPrice + " ر.س";
            ctx.fillText(oldP, cardW/2, contentY + 150);
            const w = ctx.measureText(oldP).width;
            ctx.fillStyle = "#ef4444"; 
            ctx.fillRect(cardW/2 - w/2, contentY + 140, w, 3);
        }
    } 
    
    // === القالب 2: زجاجي (Glass) ===
    else if (discountCurrentTemplate === 2) {
        // صورة كاملة
        ctx.drawImage(discountUploadedImage, 0, 0, cardW, cardH);
        
        // تظليل
        const grad = ctx.createLinearGradient(0, cardH/2, 0, cardH);
        grad.addColorStop(0, "rgba(0,0,0,0)");
        grad.addColorStop(1, "rgba(0,0,0,0.6)");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, cardW, cardH);

        // البطاقة العائمة
        ctx.save();
        ctx.shadowColor = "rgba(0,0,0,0.2)";
        ctx.shadowBlur = 20;
        ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
        roundRect(50, cardH - 280, cardW - 100, 230, 30);
        ctx.fill();
        ctx.restore();

        ctx.textAlign = "center";
        ctx.fillStyle = "#1e293b";
        ctx.font = "bold 40px 'Cairo', sans-serif";
        ctx.fillText(name, cardW/2, cardH - 180);

        ctx.font = "900 55px 'Cairo', sans-serif";
        ctx.fillStyle = accentColor;
        ctx.fillText(price + " ر.س", cardW/2, cardH - 100);

        if(oldPrice) {
            ctx.font = "bold 35px 'Cairo', sans-serif";
            ctx.fillStyle = "#94a3b8";
            const oldP = oldPrice + " ر.س";
            ctx.fillText(oldP, cardW/2, cardH - 55);
            const w = ctx.measureText(oldP).width;
            ctx.fillStyle = "#ef4444";
            ctx.fillRect(cardW/2 - w/2, cardH - 65, w, 3);
        }
    }

    // === القالب 3: بوستر ===
    else if (discountCurrentTemplate === 3) {
        ctx.drawImage(discountUploadedImage, 0, 0, cardW, cardH);
        const grad = ctx.createLinearGradient(0, cardH/2, 0, cardH);
        grad.addColorStop(0, "rgba(0,0,0,0)");
        grad.addColorStop(0.8, "rgba(0,0,0,0.95)");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, cardW, cardH);
        
        ctx.textAlign = "center";
        
        ctx.fillStyle = "white";
        ctx.font = "bold 48px 'Cairo', sans-serif";
        ctx.fillText(name, cardW/2, cardH - 180);
        
        if(oldPrice) {
            ctx.font = "bold 36px 'Cairo', sans-serif";
            ctx.fillStyle = "#cbd5e1"; 
            const oldP = oldPrice + " ر.س";
            ctx.fillText(oldP, cardW/2, cardH - 135);
            const w = ctx.measureText(oldP).width;
            ctx.fillStyle = "#ef4444"; 
            ctx.fillRect(cardW/2 - w/2, cardH - 145, w, 4);
        }
        
        ctx.fillStyle = accentColor;
        ctx.font = "900 60px 'Cairo', sans-serif";
        ctx.fillText(price + " ر.س", cardW/2, cardH - 60);
    }

    // === العلامة المائية للمستخدمين غير Premium ===
    if (typeof userTier === 'undefined' || userTier !== 'premium') {
        ctx.save();
        
        // شريط قطري شفاف
        ctx.translate(cardW / 2, cardH / 2);
        ctx.rotate(-Math.PI / 4);
        
        // خلفية الشريط بتدرج
        const stripeGrad = ctx.createLinearGradient(-300, 0, 300, 0);
        stripeGrad.addColorStop(0, "rgba(251, 191, 36, 0.85)");
        stripeGrad.addColorStop(0.5, "rgba(245, 158, 11, 0.95)");
        stripeGrad.addColorStop(1, "rgba(251, 191, 36, 0.85)");
        ctx.fillStyle = stripeGrad;
        ctx.fillRect(-400, -35, 800, 70);
        
        // النص على الشريط
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 32px 'Cairo', sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.shadowColor = "rgba(0,0,0,0.3)";
        ctx.shadowBlur = 4;
        ctx.fillText("👑 PREMIUM 👑", 0, 0);
        
        ctx.restore();
        
        // نص صغير في الأسفل
        ctx.font = "bold 18px 'Cairo', sans-serif";
        ctx.fillStyle = "rgba(0,0,0,0.5)";
        ctx.textAlign = "center";
        ctx.fillText("اشترك لإزالة العلامة المائية", cardW / 2, cardH - 15);
    }

    // تحويل لـ PNG
    const finalCardUrl = canvas.toDataURL("image/png");
    
    // إغلاق النافذة أولاً
    closeDiscountModal();
    
    // إضافة للتصميم باستخدام addAssetToCanvas (نفس الباركود والسوشيال)
    setTimeout(() => {
        if (typeof addAssetToCanvas === 'function') {
            addAssetToCanvas(finalCardUrl, false);
        } else {
            alert('خطأ: لم يتم تحميل النظام');
        }
    }, 100);
}

// تصدير الدوال للاستخدام العام
window.openDiscountModal = openDiscountModal;
window.closeDiscountModal = closeDiscountModal;
window.handleDiscountImg = handleDiscountImg;
window.selectDiscountTemplate = selectDiscountTemplate;
window.generateDiscountCard = generateDiscountCard;
