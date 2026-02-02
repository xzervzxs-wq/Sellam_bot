// ==========================================
// Cloud Save System - Free & Premium
// ==========================================

const API_URL = 'https://sellambot-despro.up.railway.app';

// Toast Notifications
function showToast(message, type = 'info') {
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
    toast.className = `fixed top-20 left-1/2 transform -translate-x-1/2 ${colors[type]} text-white px-6 py-4 rounded-xl shadow-2xl z-[99999] text-lg font-bold flex items-center gap-3`;
    toast.innerHTML = message;
    toast.style.cssText = 'animation: fadeIn 0.3s ease; min-width: 280px; text-align: center;';
    document.body.appendChild(toast);
    
    if (type !== 'loading') {
        setTimeout(() => toast.remove(), 4000);
    }
    return toast;
}

// User Identity Management
function getUserIdentity() {
    // 1. Check for logged in Premium session
    const session = localStorage.getItem('despro_session');
    if (session) {
        try {
            const data = JSON.parse(session);
            // Valid session = Premium if it has code
            if (data.code || data.name) {
                return { 
                    id: data.code || ('PREM_' + Date.now()), // Fallback just in case
                    type: 'premium', 
                    name: data.name || 'مشترك مميز',
                    limit: 10
                };
            }
        } catch(e){}
    }
    
    // 2. Guest User (Free)
    let guestId = localStorage.getItem('despro_guest_id');
    if (!guestId) {
        // Generate persistent guest ID
        guestId = 'guest_' + Math.random().toString(36).substring(2, 10) + Date.now();
        localStorage.setItem('despro_guest_id', guestId);
    }
    
    return { 
        id: guestId, 
        type: 'free', 
        name: 'زائر',
        limit: 1
    };
}

// Check limits and save
async function saveCurrentProject() {
    const user = getUserIdentity();
    const loadingToast = showToast('⏳ جاري التحقق من المساحة...', 'loading');
    
    try {
        // Check current project count
        const checkRes = await fetch(`${API_URL}/api/projects/${user.id}`);
        const checkData = await checkRes.json();
        const currentCount = checkData.projects ? checkData.projects.length : 0;
        
        if (loadingToast) loadingToast.remove();

        // Enforce Limits
        if (currentCount >= user.limit) {
            if (user.type === 'free') {
                showSubscribeModal();
            } else {
                showToast(`⚠️ لقد وصلت للحد الأقصى (${user.limit} مشاريع). احذف بعض المشاريع للحفظ.`, 'error');
            }
            return;
        }
        
        // Proceed to Save
        const projectName = prompt('أدخل اسم المشروع:', 'مشروع جديد');
        if (!projectName) return;
        
        saveProjectToCloud(user.id, projectName);
        
    } catch (e) {
        if (loadingToast) loadingToast.remove();
        showToast('❌ خطأ في الاتصال', 'error');
        console.error(e);
    }
}

// Actual Save Logic (DOM Based)
async function saveProjectToCloud(clientId, projectName) {
    const loadingToast = showToast('⏳ جاري حفظ المشروع سحابياً...', 'loading');
    
    const card = document.getElementById('card');
    if (!card) {
        if (loadingToast) loadingToast.remove();
        showToast('❌ خطأ: لم يتم العثور على منطقة العمل', 'error');
        return;
    }
    
    const projectData = {
        name: projectName,
        html: card.innerHTML,
        wVal: card.getAttribute('data-card-width'),
        hVal: card.getAttribute('data-card-height'),
        // Add backup style dimensions
        width: card.style.width,
        height: card.style.height,
        customW: document.getElementById('custom-width')?.value || '10',
        customH: document.getElementById('custom-height')?.value || '10',
        timestamp: new Date().toLocaleString('ar-SA'),
        version: "2.5"
    };

    // Notes
    const notesField = document.getElementById('designer-notes');
    if (notesField) projectData.notes = notesField.value.trim();
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout
        
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
            showToast('✅ تم الحفظ بنجاح!', 'success');
            // Check if modal is open, if so refresh list
            const modal = document.getElementById('myProjectsModal');
            if (modal && !modal.classList.contains('hidden')) {
                loadProjectsList();
            }
        } else {
            showToast('❌ فشل الحفظ: ' + (result.error || ''), 'error');
        }
    } catch (error) {
        if (loadingToast) loadingToast.remove();
        showToast('❌ خطأ: ' + error.message, 'error');
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
        // Close projects modal if open to focus on subscribe
        closeMyProjectsModal();
    }
}

function closeSubscribeModal() {
    const modal = document.getElementById('subscribeModal');
    if (modal) modal.classList.add('hidden');
}

async function loadProjectsList() {
    const user = getUserIdentity();
    const grid = document.getElementById('projectsGrid');
    
    // UI Elements for limit
    const countLabel = document.getElementById('projectsLimitLabel');
    const countDetail = document.getElementById('projectsCountDetail');
    // const limitDetail = document.getElementById('projectsLimitDetail');
    const usageBar = document.getElementById('projectsUsageBar');
    
    if (countLabel) countLabel.textContent = user.type === 'premium' ? 'مساحة تخزين Premium' : 'مساحة تخزين مجانية';
    
    grid.innerHTML = `
        <div class="h-64 flex flex-col items-center justify-center text-slate-400 gap-3">
            <i class="fas fa-circle-notch fa-spin text-2xl text-amber-500"></i>
            <span class="text-xs">جاري جلب مشاريعك...</span>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_URL}/api/projects/${user.id}`);
        const result = await response.json();
        
        if (result.success) {
            const projects = result.projects || [];
            const count = projects.length;
            
            // Update Usage Bar
            // For Premium: 10, Free: 1
            const percent = Math.min((count / user.limit) * 100, 100);
            if (usageBar) {
                usageBar.style.width = `${percent}%`;
                usageBar.className = `h-full rounded-full transition-all duration-500 ${
                    percent >= 100 ? 'bg-red-500' : 
                    percent >= 80 ? 'bg-amber-500' : 
                    'bg-gradient-to-r from-amber-400 to-amber-600'
                }`;
            }
            
            if (countDetail) countDetail.textContent = `${count} من ${user.limit} مستخدم`;
            
            displayProjectsInGrid(projects);
        } else {
            const projects = []; // Default to empty if API fails for new users
             displayProjectsInGrid(projects);
             if (countDetail) countDetail.textContent = `0 من ${user.limit} مستخدم`;
        }
    } catch(e) {
        // Fallback for empty/error state
        const projects = [];
        displayProjectsInGrid(projects);
    }
}

function displayProjectsInGrid(projects) {
    const grid = document.getElementById('projectsGrid');
    
    if (projects.length === 0) {
        grid.innerHTML = `
            <div class="flex flex-col items-center justify-center py-12 text-slate-400 opacity-60">
                <i class="fas fa-folder-open text-4xl mb-3 text-slate-300 dark:text-slate-700"></i>
                <p class="text-xs">لا توجد مشاريع محفوظة</p>
            </div>
        `;
        return;
    }
    
    projects.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
    grid.innerHTML = '';
    
    projects.forEach(project => {
        const el = document.createElement('div');
        el.className = 'group flex items-center gap-3 p-3 rounded-2xl bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 hover:border-amber-500/30 hover:shadow-lg hover:shadow-amber-500/5 transition-all cursor-pointer relative overflow-hidden';
        
        el.innerHTML = `
            <!-- Icon -->
            <div class="h-12 w-12 rounded-xl bg-white dark:bg-slate-700 flex items-center justify-center text-amber-500 shadow-sm border border-slate-100 dark:border-slate-600 group-hover:scale-110 transition-transform">
                <i class="fas fa-file-contract"></i>
            </div>
            
            <!-- Info -->
            <div class="flex-1 min-w-0">
                <h4 class="font-bold text-slate-700 dark:text-slate-200 text-sm truncate group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">${project.name || 'بدون عنوان'}</h4>
                <div class="flex items-center gap-2 text-[10px] text-slate-400 mt-1">
                    <span>${new Date(project.updated_at).toLocaleDateString('ar-SA')}</span>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="flex items-center gap-1 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-all sm:translate-x-2 group-hover:translate-x-0">
                 <button onclick="event.stopPropagation(); loadProject('${project.id}')" class="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-500 hover:bg-amber-500 hover:text-white transition flex items-center justify-center">
                    <i class="fas fa-folder-open text-xs"></i>
                </button>
                <button onclick="event.stopPropagation(); deleteProject(${project.id})" class="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-500 hover:bg-red-500 hover:text-white transition flex items-center justify-center">
                    <i class="fas fa-trash text-xs"></i>
                </button>
            </div>
        `;
        
        el.onclick = () => loadProject(project.id);
        grid.appendChild(el);
    });
}

async function loadProject(projectId) {
    const user = getUserIdentity();
    const loadingToast = showToast('⏳ جاري فتح المشروع...', 'loading');
    
    try {
        const res = await fetch(`${API_URL}/api/project/${projectId}?client_code=${user.id}`);
        const result = await res.json();
        
        if (loadingToast) loadingToast.remove();
        
        if (result.success && result.project) {
            let data = result.project.data;
            if (typeof data === 'string') data = JSON.parse(data);
            
            // Restore Logic
            const card = document.getElementById('card');
            
            // HTML restore
            if (data.html) card.innerHTML = data.html;
            
            // Dimensions
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
            showToast('✅ تم فتح المشروع بنجاح', 'success');
        } else {
             showToast('❌ فشل الفتح', 'error');
        }
    } catch(e) {
        if (loadingToast) loadingToast.remove();
        showToast('❌ خطأ في التحميل', 'error');
    }
}

async function deleteProject(projectId) {
    if (!confirm('هل أنت متأكد من الحذف؟ لا يمكن التراجع.')) return;
    
    const user = getUserIdentity();
    const loadingToast = showToast('⏳ جاري الحذف...', 'loading');
    
    try {
        const res = await fetch(`${API_URL}/api/project/${projectId}?client_code=${user.id}`, { method: 'DELETE' });
        const result = await res.json();
        
        if (loadingToast) loadingToast.remove();
        
        if (result.success) {
            showToast('✅ تم الحذف', 'success');
            loadProjectsList();
        } else {
            showToast('❌ فشل الحذف', 'error');
        }
    } catch(e) {
        if (loadingToast) loadingToast.remove();
        showToast('❌ خطأ في الاتصال', 'error');
    }
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
