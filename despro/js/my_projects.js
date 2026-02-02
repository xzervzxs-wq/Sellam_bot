// ==========================================
// نظام حفظ وتحميل المشاريع - أعمالي
// للمشتركين Premium فقط
// ==========================================

const API_URL = 'https://sellambot-despro.up.railway.app';

// التحقق من الاشتراك
function checkPremiumAccess() {
    if (typeof userTier === 'undefined' || userTier !== 'premium') {
        alert('⭐ هذه الميزة متاحة للمشتركين فقط!\n\nاشترك الآن للحصول على:\n• حفظ غير محدود للمشاريع\n• الوصول من أي جهاز\n• بدون علامة مائية');
        return false;
    }
    return true;
}

// الحصول على كود العميل من localStorage أو إنشاء جديد
function getClientCode() {
    let code = localStorage.getItem('despro_client_code');
    if (!code) {
        code = generateClientCode();
        localStorage.setItem('despro_client_code', code);
    }
    return code;
}

// إنشاء كود عميل عشوائي
function generateClientCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 8; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
}

// حفظ المشروع الحالي
async function saveCurrentProject() {
    // التحقق من الاشتراك أولاً
    if (!checkPremiumAccess()) return;
    
    const clientCode = getClientCode();
    const projectName = prompt('أدخل اسم المشروع:', 'مشروع جديد');
    
    if (!projectName) return;
    
    // الحصول على بيانات Canvas
    const canvasData = canvas.toJSON(['id', 'name', 'selectable', 'evented']);
    const thumbnail = canvas.toDataURL({
        format: 'jpeg',
        quality: 0.3,
        multiplier: 0.3
    });
    
    try {
        showLoadingMessage('جاري حفظ المشروع...');
        
        const response = await fetch(`${API_URL}/api/project/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_code: clientCode,
                project_name: projectName,
                project_data: JSON.stringify(canvasData),
                thumbnail: thumbnail
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            hideLoadingMessage();
            showSuccessMessage('تم حفظ المشروع بنجاح! ✅');
        } else {
            hideLoadingMessage();
            showErrorMessage('فشل في حفظ المشروع: ' + result.error);
        }
    } catch (error) {
        hideLoadingMessage();
        showErrorMessage('خطأ في الاتصال بالسيرفر');
        console.error('Save error:', error);
    }
}

// تحميل قائمة المشاريع
async function loadMyProjects() {
    // التحقق من الاشتراك أولاً
    if (!checkPremiumAccess()) return;
    
    const clientCode = getClientCode();
    
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
    // التحقق من الاشتراك أولاً
    if (!checkPremiumAccess()) return;
    
    const code = prompt('أدخل كود حسابك:');
    if (code && code.length >= 6) {
        localStorage.setItem('despro_client_code', code.toUpperCase());
        showSuccessMessage('تم تسجيل الدخول بنجاح!');
        loadMyProjects();
    } else if (code) {
        showErrorMessage('الكود غير صحيح');
    }
}

// تصدير الدوال للاستخدام العام
window.saveCurrentProject = saveCurrentProject;
window.loadMyProjects = loadMyProjects;
window.loadProject = loadProject;
window.deleteProject = deleteProject;
window.closeMyProjectsModal = closeMyProjectsModal;
window.showClientCode = showClientCode;
window.loginWithCode = loginWithCode;
