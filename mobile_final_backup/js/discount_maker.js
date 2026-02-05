// ==========================================
//  صانع بطاقات الخصومات (Discount Card Maker)
//  يستخدم addAssetToCanvas مثل الباركود والسوشيال
// ==========================================

let discountCurrentTemplate = 1;
let discountUploadedImage = null;

function openDiscountModal() {
    const modal = document.getElementById('discountModal');
    modal.style.display = 'flex';
    document.getElementById('discountProdName').value = '';
    document.getElementById('discountProdPrice').value = '';
    document.getElementById('discountProdOldPrice').value = '';
    document.getElementById('discountImgPreview').classList.add('hidden');
    document.getElementById('discountUploadPlaceholder').classList.remove('hidden');
    discountUploadedImage = null;
    selectDiscountTemplate(1);
    
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
    document.querySelectorAll('.discount-template-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById('discount-tmpl-' + id);
    if (activeBtn) {
        activeBtn.classList.add('active');
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

async function generateDiscountCard() {
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
    const scale = 4;
    
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

    const hex = bgColor.replace('#','');
    const r = parseInt(hex.substring(0,2), 16);
    const g = parseInt(hex.substring(2,4), 16);
    const b = parseInt(hex.substring(4,6), 16);
    const isDark = (r * 0.299 + g * 0.587 + b * 0.114) < 128;
    const mainTextColor = isDark ? "#ffffff" : "#1f2937";
    const accentColor = borderColor;

    function drawModernPrice(ctx, priceValue, x, y, color, baseSize) {
        return new Promise((resolve) => {
            ctx.save();
            
            const numberFont = "900 " + baseSize + "px 'Cairo', sans-serif";
            ctx.font = numberFont;
            const numWidth = ctx.measureText(priceValue).width;
            
            const svgSize = baseSize * 0.75; 
            const gap = baseSize * 0.2;
            const totalWidth = numWidth + svgSize + gap;
            
            let startX = x - (totalWidth / 2);
            
            const svgString = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 1500"><path d="M887.52 1234.67h0A460.06 460.06 0 0 0 849.13 1378l424.38-90.21a460.46 460.46 0 0 0 38.39-143.33ZM1273.51 1017.52A460.12 460.12 0 0 0 1311.9 874.2L981.32 944.5V809.35l292.18-62.09a460.26 460.26 0 0 0 38.39-143.33L981.31 674.18V188.11a466.3 466.3 0 0 0-132.21 111V702.29l-132.21 28.1V122A466.27 466.27 0 0 0 584.68 233V758.48L288.86 821.34a460.2 460.2 0 0 0-38.4 143.33l334.22-71v170.21L226.49 1140a460.26 460.26 0 0 0-38.39 143.33L563 1203.61a119.09 119.09 0 0 0 73.81-49.22l68.75-101.94v0a65.69 65.69 0 0 0 11.3-37V865.54l132.21-28.1v270.31l424.4-90.25Z" fill="${color}"></path></svg>`;
            
            const img = new Image();
            const blob = new Blob([svgString], {type: 'image/svg+xml;charset=utf-8'});
            const url = URL.createObjectURL(blob);
            
            img.onload = () => {
                ctx.drawImage(img, startX, y - svgSize + (baseSize * 0.1), svgSize, svgSize);
                ctx.textAlign = "left";
                ctx.fillStyle = color;
                ctx.fillText(priceValue, startX + svgSize + gap, y);
                URL.revokeObjectURL(url);
                ctx.restore();
                resolve(totalWidth);
            };
            img.src = url;
        });
    }

    if (discountCurrentTemplate === 1) {
        ctx.shadowColor = "rgba(0,0,0,0.15)";
        ctx.shadowBlur = 20;
        ctx.shadowOffsetY = 10;
        ctx.fillStyle = bgColor;
        roundRect(20, 20, cardW - 40, cardH - 40, 40);
        ctx.fill();
        ctx.shadowColor = "transparent";
        
        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 3;
        ctx.strokeRect(50, 50, cardW - 100, cardH - 100);
        
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
        
        await drawModernPrice(ctx, price, cardW/2, contentY + 90, accentColor, 65);
        
        if(oldPrice) {
            const oldPriceSize = 40;
            const oldPriceColor = "#9ca3af";
            const totalW = await drawModernPrice(ctx, oldPrice, cardW/2, contentY + 150, oldPriceColor, oldPriceSize);
            
            ctx.fillStyle = "#ef4444";
            const startX = (cardW/2) - (totalW / 2);
            ctx.fillRect(startX, contentY + 150 - (oldPriceSize * 0.3), totalW, 3);
        }
    } 
    
    else if (discountCurrentTemplate === 2) {
        ctx.drawImage(discountUploadedImage, 0, 0, cardW, cardH);
        
        const grad = ctx.createLinearGradient(0, cardH/2, 0, cardH);
        grad.addColorStop(0, "rgba(0,0,0,0)");
        grad.addColorStop(1, "rgba(0,0,0,0.6)");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, cardW, cardH);

        const boxHeight = oldPrice ? 260 : 200;
        const boxY = cardH - boxHeight - 30;
        
        ctx.save();
        ctx.shadowColor = "rgba(0,0,0,0.2)";
        ctx.shadowBlur = 20;
        ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
        roundRect(50, boxY, cardW - 100, boxHeight, 30);
        ctx.fill();
        ctx.restore();

        ctx.textAlign = "center";
        ctx.fillStyle = "#1e293b";
        ctx.font = "bold 40px 'Cairo', sans-serif";
        
        if(oldPrice) {
            ctx.fillText(name, cardW/2, boxY + 55);
            
            await drawModernPrice(ctx, price, cardW/2 + 80, boxY + 130, accentColor, 55);
            
            const oldPriceSize = 40;
            const oldPriceColor = "#94a3b8";
            const totalW = await drawModernPrice(ctx, oldPrice, cardW/2 - 80, boxY + 130, oldPriceColor, oldPriceSize);
            
            ctx.fillStyle = "#ef4444";
            const startX = (cardW/2 - 80) - (totalW / 2);
            ctx.fillRect(startX, boxY + 130 - (oldPriceSize * 0.3), totalW, 3);
            
        } else {
            ctx.fillText(name, cardW/2, boxY + 70);
            await drawModernPrice(ctx, price, cardW/2, boxY + 150, accentColor, 55);
        }
    }

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
            const oldPriceSize = 36;
            const oldPriceColor = "#cbd5e1";
            const totalW = await drawModernPrice(ctx, oldPrice, cardW/2, cardH - 135, oldPriceColor, oldPriceSize);
            
            ctx.fillStyle = "#ef4444"; 
            const startX = (cardW/2) - (totalW / 2);
            ctx.fillRect(startX, cardH - 135 - (oldPriceSize * 0.3), totalW, 4);
        }
        
        await drawModernPrice(ctx, price, cardW/2, cardH - 60, accentColor, 60);
    }

    if (typeof userTier === 'undefined' || userTier !== 'premium') {
        ctx.save();
        ctx.globalAlpha = 0.25;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.font = "bold 80px 'Cairo', sans-serif";
        ctx.fillStyle = "#000000";
        ctx.fillText("👑 Premium", cardW/2, cardH/2 - 20);
        ctx.font = "bold 28px 'Cairo', sans-serif";
        ctx.fillText("اشترك للحصول على النسخة الكاملة", cardW/2, cardH/2 + 50);
        ctx.restore();
    }

    const finalCardUrl = canvas.toDataURL("image/png");
    closeDiscountModal();
    
    setTimeout(() => {
        if (typeof addAssetToCanvas === 'function') {
            addAssetToCanvas(finalCardUrl, false);
        } else {
            alert('خطأ: لم يتم تحميل النظام');
        }
    }, 100);
}

window.openDiscountModal = openDiscountModal;
window.closeDiscountModal = closeDiscountModal;
window.handleDiscountImg = handleDiscountImg;
window.selectDiscountTemplate = selectDiscountTemplate;
window.generateDiscountCard = generateDiscountCard;
