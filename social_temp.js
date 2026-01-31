
// ==========================================
//  تكامل أيقونات التواصل الاجتماعي (Social Media Handling)
// ==========================================

const socialIcons = {
    Instagram: '<i class="fab fa-instagram"></i>',
    Snapchat: '<i class="fab fa-snapchat-ghost"></i>',
    Twitter: '<i class="fab fa-twitter"></i>',
    TikTok: '<i class="fab fa-tiktok"></i>',
    Facebook: '<i class="fab fa-facebook-f"></i>',
    WhatsApp: '<i class="fab fa-whatsapp"></i>'
};

const iconPaths = {
    Instagram: `<rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>`,
    Snapchat: `<path d="M12 2.5c-3.1 0-5 2.2-5 4.5 0 1.2.4 2.2 1 3.1-.7.4-1.3.8-1.8 1.4-.5.6-.7 1.3-.7 2.1 0 1.5 1.5 2.5 3 2.5.5 0 1-.1 1.5-.3.6.8 1.4 1.2 2 1.2s1.4-.4 2-1.2c.5.2 1 .3 1.5.3 1.5 0 3-1 3-2.5 0-.8-.3-1.5-.7-2.1-.5-.6-1.1-1-1.8-1.4.6-.9 1-1.9 1-3.1 0-2.3-1.9-4.5-5-4.5z"></path>`,
    Twitter: `<path d="M4 4l11.733 16h4.267l-11.733 -16zM4 20l6.768 -6.768M13.232 10.768l6.768 -6.768"></path>`,
    TikTok: `<path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5"></path>`,
    Facebook: `<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>`,
    WhatsApp: `<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>`
};

function openSocialModal() {
    const modal = document.getElementById('social-modal');
    modal.classList.remove('hidden');
    setTimeout(() => {
         modal.classList.remove('opacity-0');
    }, 10);
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
    
    // Preview uses FontAwesome for simplicity/consistency with buttons
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
    
    // SVG Creation Logic
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.font = `900 40px "${chosenFont}", sans-serif`;
    const textMetrics = ctx.measureText(handle);
    const textWidth = textMetrics.width;
    
    const iconPath = iconPaths[platform] || iconPaths['Instagram'];
    const iconSize = 50;
    const gap = 15;
    const totalWidth = iconSize + gap + textWidth + 20; 
    const totalHeight = 60;
    
    const svgString = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="${totalHeight}" viewBox="0 0 ${totalWidth} ${totalHeight}">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@900&family=Tajawal:wght@700&family=Montserrat:wght@900&family=Pacifico&family=Dancing+Script:wght@700&family=Bebas+Neue&family=Playfair+Display:wght@900&family=Lobster&family=Caveat:wght@700&family=Cinzel:wght@900&display=swap');
            .text { font-family: '${chosenFont}', sans-serif; font-weight: 900; font-size: 40px; fill: ${chosenColor}; }
            .icon-g { stroke: ${chosenColor}; fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
            ${platform === 'Twitter' ? '.icon-g { stroke: none; fill: '+chosenColor+'; }' : ''} 
        </style>
        
        <g transform="translate(5, 5) scale(2)" class="icon-g">
            ${iconPath}
        </g>
        
        <text x="${iconSize + gap}" y="42" class="text" dominant-baseline="middle">${handle}</text>
    </svg>`;
    
    const svgBase64 = btoa(unescape(encodeURIComponent(svgString)));
    const imgSrc = 'data:image/svg+xml;base64,' + svgBase64;

    // Use createWrapper for standard handles
    const wrapper = createWrapper('image-layer');
    
    const displayScale = 0.5; 
    
    wrapper.style.width = (totalWidth * displayScale) + 'px';
    wrapper.style.height = (totalHeight * displayScale) + 'px';
    
    const card = document.getElementById('card');
    const cardW = parseFloat(card.style.width) || card.offsetWidth;
    const cardH = parseFloat(card.style.height) || card.offsetHeight;
    
    wrapper.style.left = ((cardW - (totalWidth * displayScale)) / 2) + 'px';
    wrapper.style.top = ((cardH - (totalHeight * displayScale)) / 2) + 'px';
    
    const img = document.createElement('img');
    img.src = imgSrc;
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.pointerEvents = 'none';
    img.draggable = false;
    
    const contentWrapper = wrapper.querySelector('.content-wrapper');
    contentWrapper.appendChild(img);
    
    card.appendChild(wrapper);
    
    setupInteract(wrapper, 'box');
    selectEl(wrapper);
    saveState();
    
    closeSocialModal();
    showSuccessModal('تم إضافة الحساب بنجاح ✅');
}

window.openSocialModal = openSocialModal;
window.closeSocialModal = closeSocialModal;
window.selectPlat = selectPlat;
window.addSocialHandleToCanvas = addSocialHandleToCanvas;
