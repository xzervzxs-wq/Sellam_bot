// ==========================================
// نظام حفظ وتحميل المشاريع - أعمالي
// للمشتركين في Google Sheet فقط
// ==========================================

const API_URL = 'https://sellambot-despro.up.railway.app';

// دالة إظهار التنبيهات
function showToast(message, type = 'info') {
    // إزالة أي toast سابق
    const oldToast = document.getElementById('projectToast');
    if (oldToast) oldToast.remove();
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        loading: 'bg-amber-500'
    };
    
    const toast = document.createElement('div');
    toast.id = 'projectToast';
    toast.className = `fixed top-20 left-1/2 transform -translate-x-1/2 ${colors[type]} text-white px-6 py-4 rounded-xl shadow-2xl z-[99999] text-lg font-bold`;
    toast.innerHTML = message;
    toast.style.cssText = 'animation: fadeIn 0.3s ease; min-width: 250px; text-align: center;';
    document.body.appendChild(toast);
    
    if (type !== 'loading') {
        setTimeout(() => toast.remove(), 4000);
    }
    
    return toast;
}

// التحقق من الاشتراك - من Google Sheet
function checkPremiumAccess() {
    // التحقق من الجلسة المحفوظة
    const session = localStorage.getItem('despro_session');
    if (!session) {
        alert('⭐ هذه الميزة متاحة للمشتركين فقط!\n\nسجل دخولك بالكود للحصول على:\n• حفظ غير محدود للمشاريع\n• الوصول من أي جهاز\n• بدون علامة مائية');
        return false;
    }
    
    try {
        const sessionData = JSON.parse(session);
        // التحقق من انتهاء الصلاحية
        if (sessionData.expiryDate) {
            let expiryDate = null;
            const dateStr = sessionData.expiryDate.trim();
            if (dateStr.match(/^\d{2}-\d{2}-\d{4}$/)) {
                const [day, month, year] = dateStr.split('-');
                expiryDate = new Date(`${year}-${month}-${day}`);
            } else if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
                expiryDate = new Date(dateStr);
            } else if (dateStr.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
                expiryDate = new Date(dateStr);
            }
            if (expiryDate && expiryDate < new Date()) {
                alert('⚠️ انتهت صلاحية اشتراكك!\n\nجدد اشتراكك للاستمرار.');
                return false;
            }
        }
        return true;
    } catch (e) {
        return false;
    }
}

// الحصول على كود العميل من الجلسة (كود الاشتراك نفسه)
function getClientCode() {
    const session = localStorage.getItem('despro_session');
    if (session) {
        try {
            const sessionData = JSON.parse(session);
            // استخدم كود الاشتراك كـ client code
            if (sessionData.code) {
                return sessionData.code;
            }
        } catch (e) {}
    }
    return null;
}

// الحصول على اسم المشترك
function getClientName() {
    const session = localStorage.getItem('despro_session');
    if (session) {
        try {
            const sessionData = JSON.parse(session);
            return sessionData.name || 'مشترك';
        } catch (e) {}
    }
    return 'مشترك';
}

// حفظ المشروع الحالي
async function saveCurrentProject() {
    // التحقق من الاشتراك أولاً
    if (!checkPremiumAccess()) return;
    
    // جلب الجلسة مباشرة
    const session = localStorage.getItem('despro_session');
    let clientCode = null;
    
    if (session) {
        try {
            const sessionData = JSON.parse(session);
            clientCode = sessionData.code;
        } catch (e) {}
    }
    
    // إذا ما فيه كود، استخدم اسم المشترك
    if (!clientCode) {
        const sessionName = sessionStorage.getItem('studioName');
        if (sessionName) {
            clientCode = sessionName.replace(/\s+/g, '_');
        }
    }
    
    // تأكد من وجود كود العميل
    if (!clientCode) {
        showToast('⚠️ خطأ في الجلسة! أعد تسجيل الدخول', 'error');
        return;
    }
    
    const projectName = prompt('أدخل اسم المشروع:', 'مشروع جديد');
    
    if (!projectName) return;
    
    // إظهار رسالة التحميل
    const loadingToast = showToast('⏳ جاري حفظ المشروع...', 'loading');
    
    // الحصول على بيانات Canvas
    let canvasData = {};
    let thumbnail = '';
    
    try {
        canvasData = canvas.toJSON(['id', 'name', 'selectable', 'evented']);
        // thumbnail صغير جداً لتسريع الحفظ
        thumbnail = canvas.toDataURL({
            format: 'jpeg',
            quality: 0.1,
            multiplier: 0.15
        });
    } catch (e) {
        console.log('Canvas error:', e);
    }
    
    try {
        // إضافة timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 ثانية
        
        const response = await fetch(`${API_URL}/api/project/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_code: clientCode,
                project_name: projectName,
                project_data: JSON.stringify(canvasData),
                thumbnail: thumbnail.substring(0, 50000) // حد أقصى للصورة
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // إزالة رسالة التحميل
        if (loadingToast) loadingToast.remove();
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✅ تم حفظ المشروع بنجاح!', 'success');
            loadProjectsList(); // تحديث القائمة
        } else {
            showToast('❌ فشل: ' + (result.error || 'خطأ غير معروف'), 'error');
        }
    } catch (error) {
        // إزالة رسالة التحميل
        if (loadingToast) loadingToast.remove();
        
        if (error.name === 'AbortError') {
            showToast('❌ انتهى وقت الاتصال، حاول مرة أخرى', 'error');
        } else {
            showToast('❌ خطأ: ' + error.message, 'error');
        }
        console.error('Save error:', error);
    }
}

// تحميل قائمة المشاريع
async function loadMyProjects() {
    // التحقق من الاشتراك أولاً
    if (!checkPremiumAccess()) return;
    
    // جلب كود العميل
    let clientCode = getClientCode();
    if (!clientCode) {
        const sessionName = sessionStorage.getItem('studioName');
        if (sessionName) {
            clientCode = sessionName.replace(/\s+/g, '_');
        }
    }
    
    if (!clientCode) {
        alert('⚠️ خطأ في الجلسة! أعد تسجيل الدخول.');
        return;
    }
    
    try {
        showLoadingMessage('جاري تحميل المشاريع...');
        
        const response = await fetch(`${API_URL}/api/projects/${clientCode}`);
        const result = await response.json();
        
        hideLoadingMessage();
        
        if (result.success) {
            displayProjectsModal(result.projects);
        } else {
            showErrorMessage('فشل في تحميل المشاريع');
        }
    } catch (error) {
        hideLoadingMessage();
        showErrorMessage('خطأ في الاتصال بالسيرفر');
        console.error('Load error:', error);
    }
}

// عرض نافذة المشاريع
function displayProjectsModal(projects) {
    const modal = document.getElementById('myProjectsModal');
    const grid = document.getElementById('projectsGrid');
    
    grid.innerHTML = '';
    
    if (projects.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12 text-gray-400">
                <i class="fas fa-folder-open text-6xl mb-4"></i>
                <p class="text-xl">لا توجد مشاريع محفوظة</p>
                <p class="text-sm mt-2">ابدأ بحفظ مشروعك الأول!</p>
            </div>
        `;
    } else {
        projects.forEach(project => {
            const card = document.createElement('div');
            card.className = 'bg-gray-700 rounded-xl overflow-hidden cursor-pointer hover:ring-2 hover:ring-blue-500 transition-all group';
            card.innerHTML = `
                <div class="aspect-square bg-gray-800 relative overflow-hidden">
                    ${project.thumbnail ? 
                        `<img src="${project.thumbnail}" class="w-full h-full object-contain" alt="${project.name}">` :
                        `<div class="w-full h-full flex items-center justify-center text-gray-500">
                            <i class="fas fa-image text-4xl"></i>
                        </div>`
                    }
                    <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                        <button onclick="loadProject(${project.id})" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                            <i class="fas fa-folder-open ml-1"></i> فتح
                        </button>
                        <button onclick="deleteProject(${project.id})" class="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="p-3">
                    <h3 class="text-white font-medium truncate">${project.name}</h3>
                    <p class="text-gray-400 text-xs mt-1">${formatDate(project.updated_at)}</p>
                </div>
            `;
            card.onclick = (e) => {
                if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
                    loadProject(project.id);
                }
            };
            grid.appendChild(card);
        });
    }
    
    modal.classList.remove('hidden');
}

// تحميل مشروع محدد
async function loadProject(projectId) {
    const clientCode = getClientCode();
    
    try {
        showLoadingMessage('جاري تحميل المشروع...');
        
        const response = await fetch(`${API_URL}/api/project/${projectId}?client_code=${clientCode}`);
        const result = await response.json();
        
        hideLoadingMessage();
        
        if (result.success) {
            const projectData = JSON.parse(result.project.data);
            canvas.loadFromJSON(projectData, () => {
                canvas.renderAll();
                closeMyProjectsModal();
                showSuccessMessage('تم تحميل المشروع! ✅');
            });
        } else {
            showErrorMessage('فشل في تحميل المشروع');
        }
    } catch (error) {
        hideLoadingMessage();
        showErrorMessage('خطأ في الاتصال بالسيرفر');
        console.error('Load project error:', error);
    }
}

// حذف مشروع
async function deleteProject(projectId) {
    if (!confirm('هل أنت متأكد من حذف هذا المشروع؟')) return;
    
    const clientCode = getClientCode();
    
    try {
        const response = await fetch(`${API_URL}/api/project/${projectId}?client_code=${clientCode}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage('تم حذف المشروع');
            loadMyProjects(); // إعادة تحميل القائمة
        } else {
            showErrorMessage('فشل في حذف المشروع');
        }
    } catch (error) {
        showErrorMessage('خطأ في الاتصال بالسيرفر');
    }
}

// إغلاق نافذة المشاريع
function closeMyProjectsModal() {
    document.getElementById('myProjectsModal').classList.add('hidden');
}

// تنسيق التاريخ
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// رسائل التحميل والنجاح والخطأ
function showLoadingMessage(msg) {
    // يمكن استخدام Toast أو Modal
    console.log(msg);
}

function hideLoadingMessage() {
    // إخفاء رسالة التحميل
}

function showSuccessMessage(msg) {
    alert(msg);
}

function showErrorMessage(msg) {
    alert(msg);
}

// عرض كود العميل
function showClientCode() {
    // التحقق من الاشتراك أولاً
    if (!checkPremiumAccess()) return;
    
    const code = getClientCode();
    alert(`كود حسابك: ${code}\n\nاحتفظ بهذا الكود للوصول لمشاريعك من أي جهاز.`);
}

// تسجيل الدخول بكود موجود
function loginWithCode() {
    const code = prompt('أدخل كود حسابك:');
    if (code && code.length >= 6) {
        localStorage.setItem('despro_client_code', code.toUpperCase());
        showSuccessMessage('تم تسجيل الدخول بنجاح!');
        loadProjectsList();
    } else if (code) {
        showErrorMessage('الكود غير صحيح');
    }
}

// فتح نافذة أعمالي
function openMyProjectsModal() {
    // التحقق من الاشتراك أولاً
    if (!checkPremiumAccess()) return;
    
    const modal = document.getElementById('myProjectsModal');
    const nameDisplay = document.getElementById('clientNameDisplay');
    
    // عرض اسم المشترك
    const name = getClientName();
    if (nameDisplay) {
        nameDisplay.textContent = `مرحباً ${name}!`;
    }
    
    modal.classList.remove('hidden');
    
    // تحميل المشاريع
    loadProjectsList();
}

// تحميل قائمة المشاريع (بدون تحقق - للاستخدام الداخلي)
async function loadProjectsList() {
    // جلب كود العميل
    let clientCode = getClientCode();
    if (!clientCode) {
        const sessionName = sessionStorage.getItem('studioName');
        if (sessionName) {
            clientCode = sessionName.replace(/\s+/g, '_');
        }
    }
    
    const grid = document.getElementById('projectsGrid');
    const countEl = document.getElementById('projectsCount');
    
    grid.innerHTML = `
        <div class="col-span-full text-center py-12 text-gray-400">
            <i class="fas fa-spinner fa-spin text-4xl mb-4 text-amber-500"></i>
            <p>جاري تحميل المشاريع...</p>
        </div>
    `;
    
    if (!clientCode) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12 text-gray-400">
                <i class="fas fa-cloud text-6xl mb-4 text-amber-500/30"></i>
                <p class="text-xl">لا توجد مشاريع محفوظة</p>
            </div>
        `;
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/projects/${clientCode}`);
        const result = await response.json();
        
        if (result.success) {
            if (countEl) countEl.textContent = `${result.count} مشاريع`;
            displayProjectsInGrid(result.projects);
        } else {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12 text-red-400">
                    <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                    <p>فشل في تحميل المشاريع</p>
                </div>
            `;
        }
    } catch (error) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12 text-red-400">
                <i class="fas fa-wifi text-4xl mb-4"></i>
                <p>خطأ في الاتصال بالسيرفر</p>
            </div>
        `;
    }
}

// عرض المشاريع في الـ Grid
function displayProjectsInGrid(projects) {
    const grid = document.getElementById('projectsGrid');
    
    if (projects.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12 text-gray-400">
                <i class="fas fa-cloud text-6xl mb-4 text-amber-500/30"></i>
                <p class="text-xl mb-2">لا توجد مشاريع محفوظة</p>
                <p class="text-sm">اضغط "حفظ المشروع الحالي" لحفظ أول مشروع!</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = '';
    projects.forEach(project => {
        const card = document.createElement('div');
        card.className = 'bg-slate-700/50 rounded-xl overflow-hidden cursor-pointer hover:ring-2 hover:ring-amber-500 transition-all group border border-slate-600/50';
        card.innerHTML = `
            <div class="aspect-square bg-slate-800 relative overflow-hidden">
                ${project.thumbnail ? 
                    `<img src="${project.thumbnail}" class="w-full h-full object-contain" alt="${project.name}">` :
                    `<div class="w-full h-full flex items-center justify-center text-slate-500">
                        <i class="fas fa-image text-4xl"></i>
                    </div>`
                }
                <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    <button onclick="event.stopPropagation(); loadProject(${project.id})" class="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-bold">
                        <i class="fas fa-folder-open ml-1"></i> فتح
                    </button>
                    <button onclick="event.stopPropagation(); deleteProject(${project.id})" class="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="p-3">
                <h3 class="text-white font-medium truncate text-sm">${project.name}</h3>
                <p class="text-slate-400 text-xs mt-1">${formatDate(project.updated_at)}</p>
            </div>
        `;
        card.onclick = () => loadProject(project.id);
        grid.appendChild(card);
    });
}

// تصدير الدوال للاستخدام العام
window.saveCurrentProject = saveCurrentProject;
window.loadMyProjects = loadMyProjects;
window.loadProject = loadProject;
window.deleteProject = deleteProject;
window.closeMyProjectsModal = closeMyProjectsModal;
window.showClientCode = showClientCode;
window.loginWithCode = loginWithCode;
window.openMyProjectsModal = openMyProjectsModal;
