// ==========================================
//  تكامل أيقونات التواصل الاجتماعي (Social Media Handling)
//  نفس طريقة الباركود - رسم مباشر على Canvas
// ==========================================

const socialIcons = {
    Instagram: '<i class="fab fa-instagram"></i>',
    Snapchat: '<i class="fab fa-snapchat-ghost"></i>',
    Twitter: '<i class="fab fa-twitter"></i>',
    TikTok: '<i class="fab fa-tiktok"></i>',
    Facebook: '<i class="fab fa-facebook-f"></i>',
    WhatsApp: '<i class="fab fa-whatsapp"></i>'
};

// دوال رسم الأيقونات مباشرة على Canvas
function drawInstagramIcon(ctx, x, y, size, color) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = size * 0.08;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // المربع الخارجي مع زوايا مستديرة
    const r = size * 0.2;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + size - r, y);
    ctx.quadraticCurveTo(x + size, y, x + size, y + r);
    ctx.lineTo(x + size, y + size - r);
    ctx.quadraticCurveTo(x + size, y + size, x + size - r, y + size);
    ctx.lineTo(x + r, y + size);
    ctx.quadraticCurveTo(x, y + size, x, y + size - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.stroke();
    
    // الدائرة الداخلية
    ctx.beginPath();
    ctx.arc(x + size/2, y + size/2, size * 0.25, 0, Math.PI * 2);
    ctx.stroke();
    
    // النقطة الصغيرة
    ctx.beginPath();
    ctx.arc(x + size * 0.75, y + size * 0.25, size * 0.06, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    
    ctx.restore();
}

function drawTwitterIcon(ctx, x, y, size, color) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.beginPath();
    // X logo (simplified)
    ctx.moveTo(x, y);
    ctx.lineTo(x + size * 0.45, y + size * 0.5);
    ctx.lineTo(x, y + size);
    ctx.lineTo(x + size * 0.15, y + size);
    ctx.lineTo(x + size * 0.5, y + size * 0.6);
    ctx.lineTo(x + size * 0.85, y + size);
    ctx.lineTo(x + size, y + size);
    ctx.lineTo(x + size * 0.55, y + size * 0.5);
    ctx.lineTo(x + size, y);
    ctx.lineTo(x + size * 0.85, y);
    ctx.lineTo(x + size * 0.5, y + size * 0.4);
    ctx.lineTo(x + size * 0.15, y);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
}

function drawSnapchatIcon(ctx, x, y, size, color) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = size * 0.06;
    
    // Ghost shape simplified
    ctx.beginPath();
    ctx.moveTo(x + size * 0.5, y + size * 0.1);
    ctx.bezierCurveTo(x + size * 0.2, y + size * 0.1, x + size * 0.15, y + size * 0.4, x + size * 0.15, y + size * 0.55);
    ctx.lineTo(x + size * 0.05, y + size * 0.6);
    ctx.lineTo(x + size * 0.15, y + size * 0.7);
    ctx.lineTo(x + size * 0.25, y + size * 0.85);
    ctx.lineTo(x + size * 0.4, y + size * 0.75);
    ctx.lineTo(x + size * 0.5, y + size * 0.9);
    ctx.lineTo(x + size * 0.6, y + size * 0.75);
    ctx.lineTo(x + size * 0.75, y + size * 0.85);
    ctx.lineTo(x + size * 0.85, y + size * 0.7);
    ctx.lineTo(x + size * 0.95, y + size * 0.6);
    ctx.lineTo(x + size * 0.85, y + size * 0.55);
    ctx.bezierCurveTo(x + size * 0.85, y + size * 0.4, x + size * 0.8, y + size * 0.1, x + size * 0.5, y + size * 0.1);
    ctx.stroke();
    ctx.restore();
}

function drawTikTokIcon(ctx, x, y, size, color) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = size * 0.08;
    ctx.lineCap = 'round';
    
    // Musical note shape
    ctx.beginPath();
    ctx.arc(x + size * 0.35, y + size * 0.7, size * 0.2, 0, Math.PI * 2);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(x + size * 0.55, y + size * 0.7);
    ctx.lineTo(x + size * 0.55, y + size * 0.15);
    ctx.quadraticCurveTo(x + size * 0.7, y + size * 0.2, x + size * 0.85, y + size * 0.35);
    ctx.stroke();
    
    ctx.restore();
}

function drawFacebookIcon(ctx, x, y, size, color) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = size * 0.08;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // f shape
    ctx.beginPath();
    ctx.moveTo(x + size * 0.65, y + size * 0.1);
    ctx.lineTo(x + size * 0.5, y + size * 0.1);
    ctx.quadraticCurveTo(x + size * 0.3, y + size * 0.1, x + size * 0.3, y + size * 0.35);
    ctx.lineTo(x + size * 0.3, y + size * 0.9);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(x + size * 0.15, y + size * 0.45);
    ctx.lineTo(x + size * 0.55, y + size * 0.45);
    ctx.stroke();
    
    ctx.restore();
}

function drawWhatsAppIcon(ctx, x, y, size, color) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = size * 0.08;
    ctx.lineCap = 'round';
    
    // Chat bubble
    ctx.beginPath();
    ctx.arc(x + size * 0.5, y + size * 0.45, size * 0.4, 0, Math.PI * 2);
    ctx.stroke();
    
    // Tail
    ctx.beginPath();
    ctx.moveTo(x + size * 0.2, y + size * 0.7);
    ctx.lineTo(x + size * 0.1, y + size * 0.9);
    ctx.lineTo(x + size * 0.35, y + size * 0.75);
    ctx.stroke();
    
    ctx.restore();
}

function drawIcon(ctx, platform, x, y, size, color) {
    switch(platform) {
        case 'Instagram': drawInstagramIcon(ctx, x, y, size, color); break;
        case 'Twitter': drawTwitterIcon(ctx, x, y, size, color); break;
        case 'Snapchat': drawSnapchatIcon(ctx, x, y, size, color); break;
        case 'TikTok': drawTikTokIcon(ctx, x, y, size, color); break;
        case 'Facebook': drawFacebookIcon(ctx, x, y, size, color); break;
        case 'WhatsApp': drawWhatsAppIcon(ctx, x, y, size, color); break;
        default: drawInstagramIcon(ctx, x, y, size, color);
    }
}

function openSocialModal() {
    const modal = document.getElementById('social-modal');
    modal.classList.remove('hidden');
    void modal.offsetWidth; 
    modal.classList.remove('opacity-0');
    updatePreview();
}

function closeSocialModal() {
    const modal = document.getElementById('social-modal');
    modal.classList.add('opacity-0');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

function selectPlat(plat) {
    document.getElementById('selectedPlatform').value = plat;
    document.querySelectorAll('.platform-btn').forEach(btn => {
        btn.classList.remove('active', 'border-sky-600', 'bg-sky-50', 'text-sky-600', 'shadow-md', 'scale-105');
    });
    
    const activeBtn = document.getElementById('plat-' + plat);
    if(activeBtn) {
        activeBtn.classList.add('active', 'border-sky-600', 'bg-sky-50', 'text-sky-600', 'shadow-md', 'scale-105');
    }
    updatePreview();
}

function updatePreview() {
    const handle = document.getElementById('socialInput').value || "username";
    const platform = document.getElementById('selectedPlatform').value;
    const chosenColor = document.getElementById('handleColor').value;
    const chosenFont = document.getElementById('fontSelect').value;
    const previewContainer = document.getElementById('livePreviewContainer');
    
    const iconHtml = socialIcons[platform] || '';
    
    previewContainer.innerHTML = `
        <div class="flex items-center gap-2 px-2 py-1 leading-none select-none border border-transparent" dir="ltr" style="display: flex; align-items: center; gap: 8px;">
            <div style="font-size: 20px; color: ${chosenColor}; display: flex; align-items: center; justify-content: center;">
                ${iconHtml}
            </div>
            <span style="font-size: 16px; font-weight: 900; color: ${chosenColor}; line-height: 1; font-family: ${chosenFont}; white-space: nowrap;">
                ${handle}
            </span>
        </div>
    `;
}

function addSocialHandleToCanvas() {
    const handle = document.getElementById('socialInput').value || "username";
    const platform = document.getElementById('selectedPlatform').value;
    const chosenColor = document.getElementById('handleColor').value;
    const chosenFont = document.getElementById('fontSelect').value;
    
    // Parse font family
    let fontName = chosenFont;
    if (fontName.includes("'")) {
        fontName = fontName.replace(/'/g, "");
    }
    if (fontName.includes(",")) {
        fontName = fontName.split(",")[0].trim();
    }
    
    // Canvas settings
    const iconSize = 60;
    const fontSize = 48;
    const gap = 15;
    const padding = 20;
    
    // Measure text width
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.font = `900 ${fontSize}px "${fontName}", Arial, sans-serif`;
    const textWidth = tempCtx.measureText(handle).width;
    
    // Calculate total dimensions
    const totalWidth = Math.ceil(padding + iconSize + gap + textWidth + padding);
    const totalHeight = Math.ceil(iconSize + padding * 2);
    
    // Create final canvas
    const finalCanvas = document.createElement('canvas');
    finalCanvas.width = totalWidth;
    finalCanvas.height = totalHeight;
    const ctx = finalCanvas.getContext('2d');
    
    // Clear canvas (transparent background)
    ctx.clearRect(0, 0, totalWidth, totalHeight);
    
    // Draw icon
    const iconX = padding;
    const iconY = (totalHeight - iconSize) / 2;
    drawIcon(ctx, platform, iconX, iconY, iconSize, chosenColor);
    
    // Draw text
    ctx.fillStyle = chosenColor;
    ctx.font = `900 ${fontSize}px "${fontName}", Arial, sans-serif`;
    ctx.textBaseline = 'middle';
    ctx.fillText(handle, padding + iconSize + gap, totalHeight / 2);
    
    // Convert to PNG (same as QR code!)
    const pngUrl = finalCanvas.toDataURL("image/png");
    
    // Use same function as QR code
    if (typeof addAssetToCanvas === 'function') {
        addAssetToCanvas(pngUrl, true);
    } else {
        alert('خطأ: لم يتم تحميل النظام');
        return;
    }
    
    closeSocialModal();
}

window.openSocialModal = openSocialModal;
window.closeSocialModal = closeSocialModal;
window.selectPlat = selectPlat;
window.updatePreview = updatePreview;
window.addSocialHandleToCanvas = addSocialHandleToCanvas;
