// ==========================================
// Hybrid Save System - Local for Free, Cloud for Premium
// ==========================================

const API_URL = 'https://sellambot-despro.up.railway.app';
const LOCAL_STORAGE_KEY = 'despro_local_projects';

// Toast Notifications
function showToast(message, type = 'info') {
    const oldToast = document.getElementById('projectToast');
    if (oldToast) oldToast.remove();
    
    const colors = {
        success: 'bg-emerald-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        loading: 'bg-amber-500'
    };
    
    const toast = document.createElement('div');
    toast.id = 'projectToast';
    toast.className = `fixed top-6 left-1/2 transform -translate-x-1/2 ${colors[type]} text-white px-4 py-2 rounded-lg shadow-lg z-[99999] text-sm font-bold flex items-center gap-2`;
    toast.innerHTML = message;
    toast.style.cssText = 'animation: slideDown 0.3s ease; min-width: auto; white-space: nowrap;';
    document.body.appendChild(toast);
    
    if (!document.getElementById('toastStyle')) {
        const style = document.createElement('style');
        style.id = 'toastStyle';
        style.innerHTML = `@keyframes slideDown { from { transform: translate(-50%, -100%); opacity: 0; } to { transform: translate(-50%, 0); opacity: 1; } }`;
        document.head.appendChild(style);
    }
    
    if (type !== 'loading') {
        setTimeout(() => toast.remove(), 3000);
    }
    return toast;
}

// User Identity Management
function getUserIdentity() {
    // Method 1: Check localStorage despro_session
    const session = localStorage.getItem('despro_session');
    if (session) {
        try {
            const data = JSON.parse(session);
            if (data.code && data.code.length > 0) {
                return { 
                    id: data.code, 
                    type: 'premium', 
                    name: data.name || 'مشترك مميز',
                    limit: 10
                };
            }
        } catch(e){}
    }
    
    // Method 2: Check sessionStorage (backup - set by app.js on login)
    const studioName = sessionStorage.getItem('studioName');
    const sessionId = sessionStorage.getItem('sessionId');
    if (studioName && sessionId) {
        // User is logged in via app.js
        return { 
            id: sessionId, 
            type: 'premium', 
            name: studioName,
            limit: 10
        };
    }
    
    // Method 3: Check if page shows premium UI (data-tier attribute)
    if (document.documentElement.getAttribute('data-tier') === 'premium') {
        const name = sessionStorage.getItem('studioName') || 'مشترك';
        return { 
            id: 'premium_' + Date.now(), 
            type: 'premium', 
            name: name,
            limit: 10
        };
    }
    
    // Guest = Local Storage only (2 projects max)
    return { 
        id: 'local_guest', 
        type: 'free', 
        name: 'زائر',
        limit: 2
    };
}

// ==========================================
// LOCAL STORAGE FUNCTIONS (For Free Users)
// ==========================================
function getLocalProjects() {
    try {
        const data = localStorage.getItem(LOCAL_STORAGE_KEY);
        return data ? JSON.parse(data) : [];
    } catch(e) {
        return [];
    }
}

function saveLocalProjects(projects) {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(projects));
}

function saveProjectLocally(projectName, projectData) {
    const projects = getLocalProjects();
    const newProject = {
        id: 'local_' + Date.now(),
        name: projectName,
        data: projectData,
        updated_at: new Date().toISOString()
    };
    projects.unshift(newProject);
    saveLocalProjects(projects);
    return newProject;
}

function deleteLocalProject(projectId) {
    let projects = getLocalProjects();
    projects = projects.filter(p => p.id !== projectId);
    saveLocalProjects(projects);
}

function getLocalProject(projectId) {
    const projects = getLocalProjects();
    return projects.find(p => p.id === projectId);
}

// ==========================================
// MODAL & UI FUNCTIONS
// ==========================================
function openNameModal() {
    const user = getUserIdentity();
    
    // Check limits
    if (user.type === 'free') {
        const localProjects = getLocalProjects();
        if (localProjects.length >= user.limit) {
            showSubscribeModal();
            return;
        }
    } else {
        // Premium - check server
        checkPremiumLimitAndOpenModal(user);
        return;
    }

    const modal = document.getElementById('nameProjectModal');
    const input = document.getElementById('newProjectNameInput');
    
    if (modal) {
        modal.classList.remove('hidden');
        if(input) {
            input.value = '';
            setTimeout(() => input.focus(), 100);
        }
    }
}

async function checkPremiumLimitAndOpenModal(user) {
    try {
        const checkRes = await fetch(`${API_URL}/api/projects/${user.id}`);
        const checkData = await checkRes.json();
        const currentCount = checkData.projects ? checkData.projects.length : 0;
        
        if (currentCount >= user.limit) {
            showToast(`⚠️ المجلد ممتلئ! الحد الأقصى ${user.limit} مشاريع.`, 'error');
            return;
        }

        const modal = document.getElementById('nameProjectModal');
        const input = document.getElementById('newProjectNameInput');
        
        if (modal) {
            modal.classList.remove('hidden');
            if(input) {
                input.value = '';
                setTimeout(() => input.focus(), 100);
            }
        }
    } catch (e) {
        showToast('❌ تأكد من اتصالك بالإنترنت', 'error');
    }
}

function closeNameModal() {
    const modal = document.getElementById('nameProjectModal');
    if (modal) modal.classList.add('hidden');
}

function confirmSaveProject() {
    const input = document.getElementById('newProjectNameInput');
    const name = input ? input.value.trim() : 'مشروع جديد';
    
    if (!name) {
        showToast('⚠️ يرجى كتابة اسم للمشروع', 'info');
        return;
    }
    
    closeNameModal();
    const user = getUserIdentity();
    
    if (user.type === 'free') {
        saveProjectLocal(name);
    } else {
        saveProjectToCloud(user.id, name);
    }
}

// Save for FREE users (Local)
function saveProjectLocal(projectName) {
    const loadingToast = showToast('⏳ جاري الحفظ...', 'loading');
    
    const card = document.getElementById('card');
    if (!card) {
        if (loadingToast) loadingToast.remove();
        showToast('❌ خطأ: منطقة العمل فارغة', 'error');
        return;
    }
    
    const projectData = {
        name: projectName,
        html: card.innerHTML,
        wVal: card.getAttribute('data-card-width'),
        hVal: card.getAttribute('data-card-height'),
        width: card.style.width,
        height: card.style.height,
        customW: document.getElementById('custom-width')?.value || '10',
        customH: document.getElementById('custom-height')?.value || '10',
        timestamp: new Date().toLocaleString('en-GB'),
        version: "2.5"
    };

    const notesField = document.getElementById('designer-notes');
    if (notesField) projectData.notes = notesField.value.trim();
    
    saveProjectLocally(projectName, projectData);
    
    if (loadingToast) loadingToast.remove();
    showToast('✅ تم الحفظ في المتصفح', 'success');
    openMyProjectsModal();
}

// Save for PREMIUM users (Cloud)
async function saveProjectToCloud(clientId, projectName) {
    const loadingToast = showToast('⏳ جاري الحفظ...', 'loading');
    
    const card = document.getElementById('card');
    if (!card) {
        if (loadingToast) loadingToast.remove();
        showToast('❌ خطأ: منطقة العمل فارغة', 'error');
        return;
    }
    
    const projectData = {
        name: projectName,
        html: card.innerHTML,
        wVal: card.getAttribute('data-card-width'),
        hVal: card.getAttribute('data-card-height'),
        width: card.style.width,
        height: card.style.height,
        customW: document.getElementById('custom-width')?.value || '10',
        customH: document.getElementById('custom-height')?.value || '10',
        timestamp: new Date().toLocaleString('en-GB'),
        version: "2.5"
    };

    const notesField = document.getElementById('designer-notes');
    if (notesField) projectData.notes = notesField.value.trim();
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000);
        
        const response = await fetch(`${API_URL}/api/project/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                client_code: clientId,
                project_name: projectName,
                project_data: JSON.stringify(projectData),
                thumbnail: ''
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        if (loadingToast) loadingToast.remove();
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✅ تم الحفظ على السحابة', 'success');
            openMyProjectsModal();
        } else {
            showToast('❌ فشل الحفظ', 'error');
        }
    } catch (error) {
        if (loadingToast) loadingToast.remove();
        showToast('❌ فشل الحفظ', 'error');
    }
}

// Modal Management
function openMyProjectsModal() {
    const modal = document.getElementById('myProjectsModal');
    if (modal) {
        modal.classList.remove('hidden');
        loadProjectsList();
    }
}

function closeMyProjectsModal() {
    const modal = document.getElementById('myProjectsModal');
    if (modal) modal.classList.add('hidden');
}

function showSubscribeModal() {
    const modal = document.getElementById('subscribeModal');
    if (modal) {
        modal.classList.remove('hidden');
        closeMyProjectsModal();
    }
}

function closeSubscribeModal() {
    const modal = document.getElementById('subscribeModal');
    if (modal) modal.classList.add('hidden');
}

// Migrate Local Projects to Cloud (when user becomes Premium)
async function migrateLocalToCloud(user) {
    const localProjects = getLocalProjects();
    if (localProjects.length === 0) return;
    
    console.log('[Migration] Found', localProjects.length, 'local projects to migrate');
    showToast('⏳ جاري نقل مشاريعك للسحابة...', 'loading');
    
    let migrated = 0;
    for (const project of localProjects) {
        try {
            const response = await fetch(`${API_URL}/api/project/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    client_code: user.id,
                    project_name: project.name,
                    project_data: JSON.stringify(project.data),
                    thumbnail: ''
                })
            });
            const result = await response.json();
            if (result.success) migrated++;
        } catch(e) {
            console.log('[Migration] Failed to migrate:', project.name);
        }
    }
    
    // Clear local storage after migration
    if (migrated > 0) {
        localStorage.removeItem(LOCAL_STORAGE_KEY);
        console.log('[Migration] Cleared local storage, migrated', migrated, 'projects');
    }
    
    // Remove loading toast
    const toast = document.getElementById('projectToast');
    if (toast) toast.remove();
    
    if (migrated > 0) {
        showToast(`✅ تم نقل ${migrated} مشروع للسحابة`, 'success');
    }
}

// Load Projects List (Hybrid)
async function loadProjectsList() {
    const user = getUserIdentity();
    const grid = document.getElementById('projectsGrid');
    
    const limitLabel = document.getElementById('projectsLimitLabel');
    if (limitLabel && limitLabel.parentElement) {
         const titleEl = limitLabel.parentElement.querySelector('h3');
         if (titleEl) {
             titleEl.innerHTML = '<i class="fas fa-crown text-amber-500 ml-2"></i> أعمالي';
         }
    }
    
    const countLabel = document.getElementById('projectsLimitLabel');
    const countDetail = document.getElementById('projectsCountDetail');
    const usageBar = document.getElementById('projectsUsageBar');
    
    if (countLabel) countLabel.textContent = user.type === 'premium' ? '☁️ تخزين سحابي' : '💾 تخزين محلي';
    
    // Warning for Free Users - Only show if they have at least 1 project
    let warningEl = document.getElementById('guestWarning');
    const localProjects = getLocalProjects();
    
    if (user.type === 'free' && localProjects.length > 0) {
        if (!warningEl) {
            warningEl = document.createElement('div');
            warningEl.id = 'guestWarning';
            warningEl.className = 'mx-4 mt-2 p-3 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-500/20 rounded-xl flex gap-3 items-start';
            warningEl.innerHTML = `
                <i class="fas fa-exclamation-triangle text-amber-500 mt-0.5 text-xs"></i>
                <p class="text-[11px] text-amber-700 dark:text-amber-400 font-medium leading-relaxed">
                    تنبيه: المشاريع محفوظة في متصفحك فقط. مسح بيانات المتصفح سيحذفها.
                    <a href="#" onclick="showSubscribeModal()" class="underline font-bold hover:text-amber-800">اشترك للحفظ السحابي</a>
                </p>
            `;
            const listArea = document.getElementById('projectsGrid');
            if (listArea && listArea.parentElement) {
                listArea.parentElement.insertBefore(warningEl, listArea);
            }
        } else {
            warningEl.style.display = 'flex';
        }
    } else {
        if (warningEl) warningEl.style.display = 'none';
        
        // Premium user - check for local projects to migrate
        if (user.type === 'premium') {
            await migrateLocalToCloud(user);
        }
    }

    grid.innerHTML = `
        <div class="h-48 flex flex-col items-center justify-center text-slate-400 gap-2">
            <i class="fas fa-circle-notch fa-spin text-xl text-amber-500"></i>
            <span class="text-[10px]">تحديث القائمة...</span>
        </div>
    `;
    
    if (user.type === 'free') {
        // Load from Local Storage
        const projects = getLocalProjects();
        const count = projects.length;
        
        const percent = Math.min((count / user.limit) * 100, 100);
        if (usageBar) {
            usageBar.style.width = `${percent}%`;
            usageBar.className = `h-full rounded-full transition-all duration-500 ${
                percent >= 100 ? 'bg-red-500' : 
                percent >= 80 ? 'bg-amber-500' : 
                'bg-gradient-to-r from-amber-400 to-amber-600'
            }`;
        }
        
        if (countDetail) countDetail.textContent = `${count} من ${user.limit}`;
        displayProjectsInGrid(projects, 'local');
        
    } else {
        // Load from Server
        try {
            const response = await fetch(`${API_URL}/api/projects/${user.id}`);
            const result = await response.json();
            
            if (result.success) {
                const projects = result.projects || [];
                const count = projects.length;
                
                const percent = Math.min((count / user.limit) * 100, 100);
                if (usageBar) {
                    usageBar.style.width = `${percent}%`;
                    usageBar.className = `h-full rounded-full transition-all duration-500 ${
                        percent >= 100 ? 'bg-red-500' : 
                        percent >= 80 ? 'bg-amber-500' : 
                        'bg-gradient-to-r from-amber-400 to-amber-600'
                    }`;
                }
                
                if (countDetail) countDetail.textContent = `${count} من ${user.limit}`;
                displayProjectsInGrid(projects, 'cloud');
            } else {
                displayProjectsInGrid([], 'cloud');
                if (countDetail) countDetail.textContent = `0 من ${user.limit}`;
            }
        } catch(e) {
            grid.innerHTML = '<div class="text-center py-8 text-red-400 text-xs">تعذر الاتصال بالسيرفر</div>';
        }
    }
}

function displayProjectsInGrid(projects, storageType) {
    const grid = document.getElementById('projectsGrid');
    
    if (projects.length === 0) {
        grid.innerHTML = `
            <div class="flex flex-col items-center justify-center py-12 text-slate-400 opacity-60">
                <i class="fas fa-folder-open text-3xl mb-2 text-slate-300 dark:text-slate-700"></i>
                <p class="text-[10px]">لا توجد مشاريع محفوظة</p>
                <div class="mt-4">
                    <button onclick="openNameModal()" class="text-xs text-amber-500 hover:text-amber-600 underline">
                        احفظ مشروعك الأول الآن
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
    projects.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
    grid.innerHTML = '';
    
    projects.forEach(project => {
        const el = document.createElement('div');
        el.className = 'group flex items-center gap-3 p-3 rounded-2xl bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 hover:border-amber-500/30 hover:shadow-lg hover:shadow-amber-500/5 transition-all cursor-pointer relative overflow-hidden';
        
        const dateObj = new Date(project.updated_at);
        const dateStr = dateObj.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
        
        const isLocal = storageType === 'local';
        const projectId = project.id;
        
        el.innerHTML = `
            <div class="h-10 w-10 rounded-xl bg-white dark:bg-slate-700 flex items-center justify-center text-amber-500 shadow-sm border border-slate-100 dark:border-slate-600 group-hover:scale-105 transition-transform">
                <i class="fas ${isLocal ? 'fa-hdd' : 'fa-cloud'} text-sm"></i>
            </div>
            
            <div class="flex-1 min-w-0">
                <h4 class="font-bold text-slate-700 dark:text-slate-200 text-xs truncate group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">${project.name || 'Untitled'}</h4>
                <div class="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5 font-mono">
                    <span>${dateStr}</span>
                </div>
            </div>
            
            <div class="flex items-center gap-1">
                <button onclick="event.stopPropagation(); loadProject('${projectId}', '${storageType}')" class="w-7 h-7 rounded-full bg-indigo-50 dark:bg-slate-700 text-indigo-500 hover:bg-indigo-500 hover:text-white transition flex items-center justify-center" title="فتح">
                    <i class="fas fa-folder-open text-[10px]"></i>
                </button>
                <button onclick="event.stopPropagation(); deleteProject('${projectId}', '${storageType}')" class="w-7 h-7 rounded-full bg-red-50 dark:bg-slate-700 text-red-500 hover:bg-red-500 hover:text-white transition flex items-center justify-center" title="حذف">
                    <i class="fas fa-trash text-[10px]"></i>
                </button>
            </div>
        `;
        
        el.onclick = () => loadProject(projectId, storageType);
        grid.appendChild(el);
    });
}

// Load Project (Hybrid)
async function loadProject(projectId, storageType) {
    const loadingToast = showToast('⏳ جاري التحميل...', 'loading');
    
    let data;
    
    if (storageType === 'local') {
        const project = getLocalProject(projectId);
        if (loadingToast) loadingToast.remove();
        
        if (project) {
            data = project.data;
        } else {
            showToast('❌ المشروع غير موجود', 'error');
            return;
        }
    } else {
        // Cloud
        const user = getUserIdentity();
        try {
            const res = await fetch(`${API_URL}/api/project/${projectId}?client_code=${user.id}`);
            const result = await res.json();
            
            if (loadingToast) loadingToast.remove();
            
            if (result.success && result.project) {
                data = result.project.data;
                if (typeof data === 'string') data = JSON.parse(data);
            } else {
                showToast('❌ المشروع غير موجود', 'error');
                return;
            }
        } catch(e) {
            if (loadingToast) loadingToast.remove();
            showToast('❌ خطأ في الاتصال', 'error');
            return;
        }
    }
    
    // Apply project data
    const card = document.getElementById('card');
    
    if (data.html) card.innerHTML = data.html;
    
    const wVal = data.wVal || data.cardWidth;
    const hVal = data.hVal || data.cardHeight;
    const customW = data.customW || '10';
    const customH = data.customH || '10';
    
    document.getElementById('custom-width').value = customW;
    document.getElementById('custom-height').value = customH;

    if (wVal && hVal) {
        card.setAttribute('data-card-width', wVal);
        card.setAttribute('data-card-height', hVal);
        if (window.setCardSize) window.setCardSize(parseFloat(wVal), parseFloat(hVal));
    } else if (data.width && data.height) {
        card.style.width = data.width;
        card.style.height = data.height;
    }
    
    if (window.rebindEvents) window.rebindEvents();
    if (window.setCustomZoom) window.setCustomZoom(50);
    
    const notesField = document.getElementById('designer-notes');
    if (notesField && data.notes) notesField.value = data.notes;
    
    closeMyProjectsModal();
    showToast('✅ تم تحميل المشروع', 'success');
}

// Delete Project (Hybrid)
async function deleteProject(projectId, storageType) {
    if (!confirm('هل أنت متأكد من حذف هذا المشروع؟')) return;
    
    const loadingToast = showToast('⏳ جاري الحذف...', 'loading');
    
    if (storageType === 'local') {
        deleteLocalProject(projectId);
        if (loadingToast) loadingToast.remove();
        showToast('🗑️ تم الحذف', 'info');
        loadProjectsList();
    } else {
        // Cloud
        const user = getUserIdentity();
        try {
            const res = await fetch(`${API_URL}/api/project/${projectId}?client_code=${user.id}`, { method: 'DELETE' });
            const result = await res.json();
            
            if (loadingToast) loadingToast.remove();
            
            if (result.success) {
                loadProjectsList();
                showToast('🗑️ تم الحذف', 'info');
            } else {
                showToast('❌ فشل الحذف', 'error');
            }
        } catch(e) {
            if (loadingToast) loadingToast.remove();
            showToast('❌ خطأ في الاتصال', 'error');
        }
    }
}

// Legacy function
async function saveCurrentProject() {
    openNameModal();
}

// Exports
window.openMyProjectsModal = openMyProjectsModal;
window.closeMyProjectsModal = closeMyProjectsModal;
window.saveCurrentProject = saveCurrentProject;
window.loadProject = loadProject;
window.deleteProject = deleteProject;
window.showSubscribeModal = showSubscribeModal;
window.closeSubscribeModal = closeSubscribeModal;
window.getUserIdentity = getUserIdentity;
window.openNameModal = openNameModal;
window.closeNameModal = closeNameModal;
window.confirmSaveProject = confirmSaveProject;
