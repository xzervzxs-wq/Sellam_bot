// ==========================================
//  تكامل أيقونات التواصل الاجتماعي (Social Media Handling)
//  استخدام html2canvas لتصوير المعاينة مباشرة
// ==========================================

const socialIcons = {
    Instagram: '<i class="fab fa-instagram"></i>',
    Snapchat: '<i class="fab fa-snapchat-ghost"></i>',
    Twitter: '<i class="fab fa-x-twitter"></i>',
    TikTok: '<i class="fab fa-tiktok"></i>',
    Facebook: '<i class="fab fa-facebook-f"></i>',
    WhatsApp: '<i class="fab fa-whatsapp"></i>'
};

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
    
    // المعاينة - نفس الشكل الذي سيتم تصويره
    previewContainer.innerHTML = `
        <div id="socialCaptureArea" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 16px 14px 16px; background: transparent;" dir="ltr">
            <span style="font-size: 24px; color: ${chosenColor}; display: flex; align-items: center; justify-content: center; line-height: 1;">
                ${iconHtml}
            </span>
            <span style="font-size: 22px; font-weight: 800; color: ${chosenColor}; line-height: 1; font-family: ${chosenFont}; white-space: nowrap;">
                ${handle}
            </span>
        </div>
    `;
}

function addSocialHandleToCanvas() {
    const captureArea = document.getElementById('socialCaptureArea');
    
    if (!captureArea) {
        alert('يرجى إدخال المعرف أولاً');
        return;
    }
    
    // تصوير المعاينة بدقة عالية باستخدام html2canvas
    html2canvas(captureArea, {
        backgroundColor: null, // خلفية شفافة
        scale: 4, // دقة عالية جداً (4x)
        useCORS: true,
        allowTaint: true,
        logging: false
    }).then(canvas => {
        // تحويل لـ PNG
        const pngUrl = canvas.toDataURL("image/png");
        
        // إضافة للتصميم (نفس طريقة الباركود)
        if (typeof addAssetToCanvas === 'function') {
            addAssetToCanvas(pngUrl, true);
        } else {
            alert('خطأ: لم يتم تحميل النظام');
            return;
        }
        
        closeSocialModal();
    }).catch(err => {
        console.error('Error capturing social handle:', err);
        alert('حدث خطأ أثناء إنشاء الصورة');
    });
}

window.openSocialModal = openSocialModal;
window.closeSocialModal = closeSocialModal;
window.selectPlat = selectPlat;
window.updatePreview = updatePreview;
window.addSocialHandleToCanvas = addSocialHandleToCanvas;
