// ==========================================
        //  إعدادات تليجرام (قم بوضع بياناتك هنا)
        // ==========================================
        const TG_BOT_TOKEN = "8496103721:AAEwYa65lXMrH5RjnzTXdg-EkPNt5sB7uOM";
        const TG_CHAT_ID = "237657512";
        // ==========================================

        // ==========================================
        //  نظام الوضع الليلي والنهاري (Dark Mode)
        // ==========================================
        const DARK_MODE_COLORS = {
            '#ffffff': '#16213e',
            '#f8fafc': '#0f172a',
            '#f1f5f9': '#1a1a2e',
            '#1e293b': '#e8e8e8',
            '#64748b': '#a8b5c8',
            '#94a3b8': '#a8b5c8',
            'rgb(255, 255, 255)': 'rgb(22, 33, 62)',
            'rgb(248, 250, 252)': 'rgb(15, 23, 42)',
            'rgb(30, 41, 59)': 'rgb(232, 232, 232)',
        };

        function initTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            if (savedTheme === 'dark') {
                document.documentElement.classList.add('dark-mode');
                applyDarkModeColors();
            }
        }

        function applyDarkModeColors() {
            const elements = document.querySelectorAll('[style*="color"], [style*="background"]');
            elements.forEach(el => {
                let style = el.getAttribute('style') || '';
                Object.entries(DARK_MODE_COLORS).forEach(([light, dark]) => {
                    style = style.replace(new RegExp(light, 'gi'), dark);
                });
                el.setAttribute('style', style);
            });
        }

        function toggleDarkMode() {
            const html = document.documentElement;
            const isDarkMode = html.classList.toggle('dark-mode');
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');

            // لا حاجة لإعادة التحميل - CSS يتولى كل شيء!
            // التبديل يحصل فوراً بدون فقدان البيانات
        }

        // تطبيق الثيم المحفوظ عند بدء الصفحة
        initTheme();
        // ==========================================

        // ==========================================
        //  نظام الـ Free Tier vs Premium
        // ==========================================
        let userTier = 'free'; // 'free' أو 'premium'
        const ITEMS_PER_CATEGORY_FREE = 10; // عدد العناصر المفتوحة في المجاني

        function updateUserTier(isPremium) {
            userTier = isPremium ? 'premium' : 'free';
            localStorage.setItem('userTier', userTier);
            applyTierRestrictions();
        }

        function applyTierRestrictions() {
            if (userTier === 'free') {
                restrictFonts();
                restrictShapes();
                restrictFrames();
            }
        }

        // استعادة الـ tier من localStorage
        window.addEventListener('load', () => {
            const savedTier = localStorage.getItem('userTier');
            if (savedTier === 'premium') {
                userTier = 'premium';
            } else {
                userTier = 'free';
            }
            setTimeout(applyTierRestrictions, 500);
        });
        // ==========================================

        const DPI_RATIO = 118.11;
        let activeEl = null;
        let undoStack = [];
        let redoStack = [];
        let isTransparent = false;
        let hasGradient = false;
        let eraserMode = false;
        let magicMode = false;
        let lassoMode = false; // متغير القص الذكي
        let lassoTargetEl = null; // الطبقة المستهدفة للقص
        let smartEraserMode = false; // متغير الممحاة الذكية
        let smartEraserCanvas = null; // كانفاس الممحاة الذكية
        let cropMode = false; // متغير وضع القص
        let handMode = false; // متغير وضع اليد للتحريك
        let eraserCanvas = null;
        let lassoCanvas = null; // كانفاس القص
        let smartFillMode = false; // متغير التلوين الذكي
        let smartFillCanvas = null; // كانفاس التلوين الذكي
        let smartFillColor = "#6366f1"; // لون التعبئة الافتراضي
        let eraserSize = 30;
        let eraserSoftness = 0;
        let magicTolerance = 30;
        let isSnappingEnabled = false;
        let currentZoom = 50; // متغير التحكم بـ zoom (الافتراضي 50%)

        // Crop variables
        let cropStartX = 0, cropStartY = 0;
        let cropStartWidth = 100, cropStartHeight = 100;
        let draggedHandle = null;
        let isDraggingCrop = false;
        let cropInitialX, cropInitialY;

        // Hand Tool variables
        let isHandDragging = false;
        let handStartX = 0, handStartY = 0;
        let handScrollLeft = 0, handScrollTop = 0;

        // --- إدارة الألوان المفضلة ---
        let favoriteColors = JSON.parse(localStorage.getItem('dalal_fav_colors')) || [
            '#000000', '#ffffff', '#6366f1', '#ec4899', '#6366f1',
            '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#64748b'
        ];

        function renderFavoriteColors() {
            const container = document.getElementById('fav-colors-container');
            if(!container) return;
            container.innerHTML = '';
            favoriteColors.forEach(color => {
                const div = document.createElement('div');
                div.className = 'w-6 h-6 rounded-full cursor-pointer border border-gray-200 shadow-sm hover:scale-110 transition relative group flex-shrink-0';
                div.style.backgroundColor = color;

                // زر الحذف
                const del = document.createElement('div');
                del.className = 'absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full text-white items-center justify-center text-[8px] hidden group-hover:flex shadow-sm z-10';
                del.innerHTML = '×';
                del.onclick = (e) => {
                    e.stopPropagation();
                    removeFavoriteColor(color);
                };
                div.appendChild(del);

                div.onclick = () => applyFavoriteColor(color);
                container.appendChild(div);
            });
        }

        // تحميل الألوان فور جاهزية الصفحة
        document.addEventListener('DOMContentLoaded', renderFavoriteColors);

        function addFavoriteColor(color) {
            if(!favoriteColors.includes(color)) {
                favoriteColors.push(color);
                if(favoriteColors.length > 15) favoriteColors.shift();
                saveFavoriteColors();
                renderFavoriteColors();
            }
        }

        function removeFavoriteColor(color) {
            favoriteColors = favoriteColors.filter(c => c !== color);
            saveFavoriteColors();
            renderFavoriteColors();
        }

        function saveFavoriteColors() {
            localStorage.setItem('dalal_fav_colors', JSON.stringify(favoriteColors));
        }

        function applyFavoriteColor(color) {
            if(activeEl) {
                if(activeEl.classList.contains('text-layer')) {
                    if (document.getElementById('quick-color')) document.getElementById('quick-color').value = color;
                    if (document.getElementById('top-text-color')) document.getElementById('top-text-color').value = color;
                    updateStyle('color', color);
                } else if(activeEl.classList.contains('frame-layer')) {
                    if (document.getElementById('bg-color')) document.getElementById('bg-color').value = color;
                    updateStyle('backgroundColor', color);
                } else if(activeEl.classList.contains('image-layer') && activeEl.getAttribute('data-colorable') !== 'false') {
                    // تطبيق اللون على الصور (ما عدا colorable = false)
                    if (document.getElementById('colorable-color')) document.getElementById('colorable-color').value = color;
                    updateColorableColor(color);
                }
            }
        }

        // متغيرات للتحكم في معاينة A4
        let currentCardData = null;
        let currentA4Layout = null;
        let cachedCardImage = null;
        let savedZoomBeforeA4 = null; // لحفظ الزوم قبل فتح مودال الطباعة

        // متغير لتتبع القالب المحمل الحالي
        let currentLoadedTemplateIndex = null;

        // دالة تحويل الأرقام العربية إلى إنجليزية
        function arabicToEnglish(arabicNum) {
            const arabicDigits = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
            const englishDigits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
            let result = String(arabicNum);
            for (let i = 0; i < 10; i++) {
                result = result.replace(new RegExp(arabicDigits[i], 'g'), englishDigits[i]);
            }
            return result;
        }

        window.onload = async () => {
            await document.fonts.ready;
            setTimeout(() => {
                document.getElementById('startup-overlay').style.opacity = '0';
                setTimeout(() => document.getElementById('startup-overlay').remove(), 500);
            }, 800);

            // تعيين المقاس الافتراضي 10 سم * 10 سم
            const defaultSize = Math.round(10 * DPI_RATIO);
            setCardSize(defaultSize, defaultSize);

            
            // تعيين الزووم الافتراضي 50%
            setCustomZoom(50);
            // إخفاء التدرج عند البدء
            hasGradient = false;
            const grad = document.getElementById('card-gradient');
            if(grad) grad.style.display = 'none';

            // إعادة تعيين متغير القالب المحمل (عمل جديد)
            currentLoadedTemplateIndex = null;

            updateTemplateList(); // تحميل القوالب
            initAssetWindowDrag(); // تفعيل سحب نافذة الأصول
            renderFavoriteColors(); // تحميل الألوان المفضلة

            // تحميل مكتبة العناصر مباشرة مع بداية الصفحة
            loadAssetsLibraryFromGitHub();

            // حفظ الحالة الأولية (فارغة) لتمكين التراجع
            saveState();

            // إضافة حماية عند تحديث الصفحة أو إغلاقها
            window.addEventListener('beforeunload', (e) => {
                const card = document.getElementById('card');
                const hasElements = card && card.children.length > 1; // > 1 لأن card-gradient يحسب كعنصر

                if (hasElements) {
                    e.preventDefault();
                    e.returnValue = '';
                    return '';
                }
            });

            // تحميل الملاحظات المحفوظة عند فتح الصفحة - بدون localStorage
            // الملاحظات تأتي فقط من فتح قالب محفوظ
        };

        // --- إدارة القوالب (Templates) ---
        const MAX_TEMPLATES = 20;

        // الحصول على معرف الجلسة الفريد
        function getSessionId() {
            return sessionStorage.getItem('sessionId') || 'default_session';
        }

        // مفتاح تخزين القوالب الخاصة بالمستخدم (باستخدام Session ID العشوائي)
        function getUserTemplatesKey() {
            return `template_${getSessionId()}`;
        }

        // مفتاح تخزين القوالب المشتركة من GitHub
        const SHARED_TEMPLATES_KEY = 'template_shared';

        function getTemplates() {
            try {
                const userKey = getUserTemplatesKey();
                const userTemplates = JSON.parse(localStorage.getItem(userKey) || '[]');
                const sharedTemplates = JSON.parse(localStorage.getItem(SHARED_TEMPLATES_KEY) || '[]');

                // دمج القوالب الخاصة والمشتركة (الخاصة أولاً)
                return [...userTemplates, ...sharedTemplates];
            } catch (e) {
                return [];
            }
        }

        function saveTemplates(templates, isShared = false) {
            try {
                const key = isShared ? SHARED_TEMPLATES_KEY : getUserTemplatesKey();
                localStorage.setItem(key, JSON.stringify(templates));
                updateTemplateList();
            } catch (e) {
                console.error("Storage Quota Exceeded:", e);
                // لا نرمي الخطأ هنا حتى لا نوقف عملية التنزيل
                // فقط نكتفي بتسجيله، لأن المستخدم حصل على ملفه المحفوظ
            }
        }

        // تحميل القوالب من GitHub إذا لم تكن موجودة محلياً
        async function loadTemplatesFromGitHub() {
            const existingSharedTemplates = JSON.parse(localStorage.getItem(SHARED_TEMPLATES_KEY) || '[]');

            // إذا كانت هناك قوالب مشتركة محفوظة بالفعل، لا تحمل من GitHub
            if (existingSharedTemplates.length > 0) {
                return;
            }

            try {
                const response = await fetch('https://raw.githubusercontent.com/xzervzxs-wq/Sellam_bot/main/dalal_templates_2026-01-17%20(4).json');
                if (response.ok) {
                    const githubTemplates = await response.json();
                    if (Array.isArray(githubTemplates) && githubTemplates.length > 0) {
                        saveTemplates(githubTemplates, true); // حفظ كقوالب مشتركة
                    }
                }
            } catch (error) {
                console.log('تعذر تحميل القوالب من GitHub (غير حرج):', error);
            }
        }

        function updateTemplateList() {
            const templates = getTemplates();
            const select = document.getElementById('template-select');

            // إبقاء الخيار الأول فقط
            while (select.options.length > 1) {
                select.remove(1);
            }

            templates.forEach((t, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.text = t.name;
                select.add(option);
            });
        }

        function toggleTemplates() {
            const content = document.getElementById('templates-content');
            const arrow = document.getElementById('templates-arrow');
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                content.classList.add('flex');
                arrow.style.transform = 'rotate(-90deg)';
            } else {
                content.classList.add('hidden');
                content.classList.remove('flex');
                arrow.style.transform = 'rotate(0deg)';
            }
        }

        // ============= مكتبة العناصر الرسمية =============
        let officialAssetsLibrary = [];

        function toggleAssetsLibrary() {
            const content = document.getElementById('assets-library-content');
            const arrow = document.getElementById('assets-library-arrow');
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                content.classList.add('flex');
                arrow.style.transform = 'rotate(-90deg)';
                // تحميل المكتبة عند أول فتح فقط
                if (officialAssetsLibrary.length === 0) {
                    loadAssetsLibraryFromGitHub();
                }
            } else {
                content.classList.add('hidden');
                content.classList.remove('flex');
                arrow.style.transform = 'rotate(0deg)';
            }
        }

        function loadAssetsLibraryFromGitHub() {
            const grid = document.getElementById('assets-grid');
            const select = document.getElementById('assets-category-select');

            if (!grid || !select) {
                console.error('عناصر المكتبة غير موجودة');
                return;
            }

            // التحقق من وجود البيانات المحملة مسبقاً
            if (officialAssetsLibrary && officialAssetsLibrary.length > 0) {
                // ملء قائمة التصنيفات
                select.innerHTML = '<option value="">📂 اختر تصنيفاً...</option>';
                officialAssetsLibrary.forEach((category, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = category.name;
                    select.appendChild(option);
                });

                // اختيار أول تصنيف تلقائياً
                select.value = 0;
                loadAssetsCategory();

                console.log('✅ تم تحميل المكتبة:', officialAssetsLibrary.length, 'تصنيف');
                return;
            }

            // عرض رسالة تحميل
            grid.innerHTML = `
                <div class="col-span-3 py-6 px-4">
                    <div class="h-1 w-full bg-[#f1f5f9] rounded-full overflow-hidden relative">
                        <div class="absolute h-full bg-gradient-to-r from-[#6366f1] via-[#a855f7] to-[#6366f1] w-1/3 rounded-full" style="animation: loadingSlide 1.5s infinite ease-in-out;"></div>
                    </div>
                    <style>@keyframes loadingSlide { 0% { left: -40%; } 100% { left: 110%; } }</style>
                </div>`;

            // تحميل ملف JSON من نفس المخادم (بدلاً من GitHub)
            fetch('./Official.json?t=' + Date.now())
                .then(response => {
                    if (!response.ok) {
                        throw new Error('فشل تحميل الملف');
                    }
                    return response.json();
                })
                .then(data => {
                    officialAssetsLibrary = data;

                    // ملء قائمة التصنيفات
                    select.innerHTML = '<option value="">📂 اختر تصنيفاً...</option>';
                    officialAssetsLibrary.forEach((category, index) => {
                        const option = document.createElement('option');
                        option.value = index;
                        option.textContent = category.name;
                        select.appendChild(option);
                    });

                    // اختيار أول تصنيف تلقائياً
                    if (officialAssetsLibrary.length > 0) {
                        select.value = 0;
                        loadAssetsCategory();
                    } else {
                        grid.innerHTML = '<p class="text-[#64748b] text-[10px] col-span-3 text-center py-4">✅ المكتبة فارغة حالياً</p>';
                    }

                    console.log('✅ تم تحميل المكتبة:', officialAssetsLibrary.length, 'تصنيف');
                })
                .catch(error => {
                    console.error('خطأ في تحميل المكتبة:', error);
                    grid.innerHTML = '<p class="text-red-500 text-[10px] col-span-3 text-center py-4"><i class="fas fa-exclamation-triangle ml-2"></i>خطأ في الاتصال - تأكد من الانترنت</p>';
                });
        }

        function loadAssetsCategory() {
            const select = document.getElementById('assets-category-select');
            const grid = document.getElementById('assets-grid');
            const index = select.value;

            if (index === '' || !officialAssetsLibrary[index]) {
                grid.innerHTML = '<p class="text-[#64748b] text-[10px] col-span-3 text-center py-4">اختر تصنيفاً لعرض العناصر</p>';
                return;
            }

            const category = officialAssetsLibrary[index];
            grid.innerHTML = '';

            if (!category.items || category.items.length === 0) {
                grid.innerHTML = '<p class="text-[#64748b] text-[10px] col-span-3 text-center py-4">لا توجد عناصر في هذا التصنيف</p>';
                return;
            }

            category.items.forEach((item, index) => {
                const div = document.createElement('div');
                div.className = 'asset-item bg-[#f1f5f9] rounded-lg p-2 cursor-pointer hover:bg-[#e2e8f0] transition-all relative group';

                // تحديد ما إذا كان العنصر مقفول (استخدام freeCount من البيانات، افتراضي 4)
                const freeCount = category.freeCount !== undefined ? category.freeCount : 4;
                const isLocked = index >= freeCount && userTier === 'free';

                if (isLocked) {
                    // div.classList.add('locked-item'); // تم تعطيل الكلاس القديم لإزالة علامة القفل القديمة
                    div.style.position = 'relative';
                    div.style.opacity = '0.9'; // جعل العنصر واضحاً ومغرياً

                    // إضافة أيقونة القفل الجديدة
                    const lockIcon = document.createElement('div');
                    lockIcon.className = 'absolute top-1 right-1 bg-white/90 backdrop-blur-sm rounded-full p-1 shadow-sm z-10 flex items-center justify-center';
                    lockIcon.style.width = '20px';
                    lockIcon.style.height = '20px';
                    lockIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 13a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v6a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2v-6" /><path d="M11 16a1 1 0 1 0 2 0a1 1 0 0 0 -2 0" /><path d="M8 11v-4a4 4 0 1 1 8 0v4" /></svg>`;
                    div.appendChild(lockIcon);
                }

                const img = document.createElement('img');
                img.src = item.src;
                img.className = 'w-full h-16 object-contain rounded';
                img.draggable = false;

                div.appendChild(img);

                if (isLocked) {
                    // إذا كان مقفول، عرض modal الاشتراك بدل إضافة العنصر
                    div.onclick = (e) => {
                        e.stopPropagation();
                        showPremiumModal('عناصر إضافية', item.src);
                    };
                } else {
                    // إذا كان مفتوح، أضفه للـ canvas
                    div.onclick = () => addAssetToCanvas(item.src, item.colorable, category.name);
                }

                grid.appendChild(div);
            });
        }

        function addAssetToCanvas(src, colorable, categoryName) {
            const img = new Image();
            img.onload = function() {
                const card = document.getElementById('card');
                const cardRect = card.getBoundingClientRect();

                // حساب الحجم المناسب
                let w = img.naturalWidth;
                let h = img.naturalHeight;
                const maxSize = 250;

                if (w > maxSize || h > maxSize) {
                    const ratio = Math.min(maxSize / w, maxSize / h);
                    w = Math.round(w * ratio);
                    h = Math.round(h * ratio);
                }

                // حساب موقع في وسط البطاقة
                const cardW = parseFloat(card.style.width) || card.offsetWidth;
                const cardH = parseFloat(card.style.height) || card.offsetHeight;
                const centerX = (cardW - w) / 2;
                const centerY = (cardH - h) / 2;

                // إنشاء العنصر
                const wrapper = createWrapper('image-layer');
                wrapper.style.width = w + 'px';
                wrapper.style.height = h + 'px';
                wrapper.style.left = Math.max(10, centerX) + 'px';
                wrapper.style.top = Math.max(10, centerY) + 'px';

                const imgEl = document.createElement('img');
                imgEl.src = src;
                imgEl.style.width = '100%';
                imgEl.style.height = '100%';
                imgEl.style.objectFit = 'fill';
                imgEl.draggable = false;

                // جميع العناصر قابلة للتلوين ما عدا اللي محددة بـ colorable: false
                if (colorable !== false) {
                    wrapper.setAttribute('data-colorable', 'true');
                } else {
                    wrapper.setAttribute('data-colorable', 'false');
                }

                // حفظ معلومات الصورة المصغرة واسم الفئة للطبقات
                wrapper.setAttribute('data-thumb', src);
                if (categoryName) {
                    wrapper.setAttribute('data-category-name', categoryName);
                }

                // إضافة الصورة داخل content-wrapper
                const contentWrapper = wrapper.querySelector('.content-wrapper');
                if (contentWrapper) {
                    contentWrapper.appendChild(imgEl);
                } else {
                    wrapper.appendChild(imgEl);
                }

                card.appendChild(wrapper);

                // تفعيل السحب والتحجيم
                setupInteract(wrapper, 'box');

                // تحديد العنصر
                selectEl(wrapper);

                saveState();
            };
            img.onerror = function() {
                alert('❌ فشل في تحميل العنصر');
            };
            img.src = src;
        }

        function saveCurrentAsTemplate() {
            const templates = getTemplates();
            const card = document.getElementById('card');

            // إلغاء التحديد قبل الحفظ ليكون القالب نظيفاً
            deselect();

            // تنظيف HTML من خصائص الأحداث المرتبطة
            let cleanedHTML = card.innerHTML;
            // إزالة data-events-bound و data-element-id لتجنب مشاكل إعادة ربط الأحداث
            cleanedHTML = cleanedHTML.replace(/\s*data-events-bound="[^"]*"/g, '');
            cleanedHTML = cleanedHTML.replace(/\s*data-element-id="[^"]*"/g, '');

            // إذا كان هناك قالب محمل حالياً، نسأل هل تريد تحديثه
            if (currentLoadedTemplateIndex !== null && currentLoadedTemplateIndex >= 0) {
                if (confirm('🔄 تم تحميل قالب موجود.\n\nهل تريد تحديث هذا القالب بالتعديلات الحالية؟\n\n✅ نعم = تحديث القالب الموجود\n❌ لا = حفظ كقالب جديد')) {
                    // تحديث القالب الموجود
                    templates[currentLoadedTemplateIndex].html = cleanedHTML;
                    templates[currentLoadedTemplateIndex].width = card.style.width;
                    templates[currentLoadedTemplateIndex].height = card.style.height;
                    templates[currentLoadedTemplateIndex].wVal = card.getAttribute('data-card-width');
                    templates[currentLoadedTemplateIndex].hVal = card.getAttribute('data-card-height');
                    templates[currentLoadedTemplateIndex].customW = document.getElementById('custom-width').value;
                    templates[currentLoadedTemplateIndex].customH = document.getElementById('custom-height').value;
                    templates[currentLoadedTemplateIndex].notes = document.getElementById('designer-notes') ? document.getElementById('designer-notes').value : ''; // حفظ الملاحظات

                    try {
                        saveTemplates(templates);
                        alert(`✅ تم تحديث القالب "${templates[currentLoadedTemplateIndex].name}" بنجاح!`);
                        return;
                    } catch(e) {
                        console.error(e);
                        alert('❌ عذراً، حدث خطأ في تحديث القالب.');
                        return;
                    }
                }
                // إذا اختار "لا"، سيستمر في حفظ قالب جديد
            }

            // حفظ كقالب جديد
            if (templates.length >= MAX_TEMPLATES) {
                alert('⚠️ عذراً، وصلت للحد الأقصى (10 قوالب). يرجى حذف قالب قديم أولاً.');
                return;
            }

            const name = prompt('أدخل اسم القالب الجديد:');
            if (!name || name.trim() === '') return;

            // جمع البيانات - الملاحظات تأتي مباشرة من الحقل (بدون localStorage)
            const notesValue = document.getElementById('designer-notes') ? document.getElementById('designer-notes').value : '';

            const template = {
                id: Date.now(),
                name: name.trim(),
                html: cleanedHTML,
                width: card.style.width,
                height: card.style.height,
                wVal: card.getAttribute('data-card-width'),
                hVal: card.getAttribute('data-card-height'),
                customW: document.getElementById('custom-width').value,
                customH: document.getElementById('custom-height').value,
                notes: notesValue // حفظ الملاحظات مع التصميم
            };

            try {
                templates.push(template);
                saveTemplates(templates, false); // حفظ كقالب خاص بالمستخدم
                console.log('✅ تم حفظ القالب مع الملاحظات:', template.notes); // debug
                alert(`✅ تم حفظ القالب "${name.trim()}" بنجاح!`);
            } catch(e) {
                console.error(e);
                alert('❌ عذراً، مساحة التخزين ممتلئة. حاول استخدام صور أقل دقة أو حذف قوالب قديمة.');
            }
        }

        // دالة جديدة للتأكد من الاختيار قبل التحميل
        function loadSelectedTemplate() {
            const select = document.getElementById('template-select');
            const index = select.value;
            if (index === "") {
                alert('يرجى اختيار قالب من القائمة أولاً.');
                return;
            }
            loadTemplate(index);
        }

        // دالة لفتح مشروع جديد مع سؤال حفظ القالب
        function createNewProject() {
            const card = document.getElementById('card');
            const hasElements = card.children.length > 0;

            if (!hasElements) {
                // إذا لم يكن هناك عناصر، أنشئ جديد مباشرة
                resetCanvas();
                return;
            }

            // فتح نافذة جديدة جميلة
            document.getElementById('new-project-modal').classList.remove('hidden');
        }

        // إغلاق نافذة المشروع الجديد
        function closeNewProjectModal() {
            document.getElementById('new-project-modal').classList.add('hidden');
        }

        // حفظ العمل الحالي وإنشاء جديد
        function saveCurrentAsTemplateAndNew() {
            // فتح نافذة حفظ باسم (save-as-modal) لحفظ في القوالب
            openSaveAsModal();
            document.getElementById('save-as-callback').value = 'newProject'; // علامة للرجوع بعد الحفظ
        }

        // === دوال لوحة المصمم (Designer Panel) ===
        function openDesignerPanel() {
            const panel = document.getElementById('designer-panel');
            panel.classList.remove('hidden');
            updateDesignerStats();
        }

        function closeDesignerPanel() {
            document.getElementById('designer-panel').classList.add('hidden');
        }

        function updateDesignerStats() {
            const card = document.getElementById('card');
            // حساب عدد العناصر (لا نحسب card-gradient)
            const elementCount = Math.max(0, card.children.length - 1);
            document.getElementById('element-count').textContent = elementCount;

            // حساب مقاس المربع
            const width = parseInt(card.style.width) / DPI_RATIO || 10;
            const height = parseInt(card.style.height) / DPI_RATIO || 10;
            document.getElementById('canvas-size').textContent = `${width.toFixed(1)} × ${height.toFixed(1)} سم`;

            // === استخراج الألوان المستخدمة (Used Colors) ===
            const usedColors = new Set();

            // قائمة الكلمات المحجوزة في Gradients لتجاهلها
            const ignoredWords = new Set(['linear', 'radial', 'gradient', 'to', 'right', 'left', 'top', 'bottom', 'deg', 'circle', 'at', 'center', 'transparent', 'none', 'url', 'repeat', 'no-repeat', 'scroll']);

            // دالة مساعدة لتنظيف وإضافة اللون
            const collectColor = (c) => {
                if (!c) return;
                const color = c.toString().trim().toLowerCase();
                if (ignoredWords.has(color) || color === 'rgba(0, 0, 0, 0)' || color === 'inherit' || color === 'none') return;
                try {
                    // التحقق من أن اللون صالح بوضعه في عنصر مؤقت (طريقة آمنة)
                    const s = new Option().style;
                    s.color = color;
                    if (s.color !== '') usedColors.add(color);
                } catch (e) {}
            };

            // دالة لاستخراج الألوان من التدرجات أو النصوص المعقدة
            const extractColorsFromString = (str) => {
                if (!str || str === 'none') return;
                // Regex for Hex, RGB, HSL, and Names (basic)
                const regex = /#[0-9a-fA-F]{3,8}|rgba?\([\d\s,.]+\)|hsla?\([\d\s,%.]+\)|[a-z]{3,}/gi;
                const matches = str.match(regex);
                if (matches) {
                    matches.forEach(m => collectColor(m));
                }
            };

            // الدوران على العناصر
            Array.from(card.children).forEach(child => {
                if (child.id === 'card-gradient') return; // تجاهل التدرج الخلفي

                // 1. فحص أنماط العنصر الأساسي
                if (child.style.color) collectColor(child.style.color);
                if (child.style.backgroundColor) collectColor(child.style.backgroundColor);
                if (child.style.borderColor) collectColor(child.style.borderColor);

                // فحص التدرجات (Gradients)
                if (child.style.backgroundImage && child.style.backgroundImage.includes('gradient')) {
                     extractColorsFromString(child.style.backgroundImage);
                }

                // 2. فحص النصوص
                const textElements = child.querySelectorAll('*');
                textElements.forEach(el => {
                     if (el.style.color) collectColor(el.style.color);
                     if (el.style.backgroundColor) collectColor(el.style.backgroundColor);
                });

                // 3. فحص SVG
                const svgElements = child.tagName === 'svg' ? [child] : child.querySelectorAll('svg, path, circle, rect');
                svgElements.forEach(el => {
                    collectColor(el.getAttribute('fill') || el.style.fill);
                    collectColor(el.getAttribute('stroke') || el.style.stroke);
                });
            });

            // تعبئة لوحة الألوان
            const paletteDiv = document.getElementById('used-colors-palette');
            if (paletteDiv) {
                paletteDiv.innerHTML = '';
                if (usedColors.size === 0) {
                    paletteDiv.innerHTML = '<span class="text-[10px] text-gray-400 italic">لا توجد عناصر ملونة</span>';
                } else {
                    Array.from(usedColors).slice(0, 18).forEach(color => {
                        const dot = document.createElement('div');
                        dot.className = 'w-4 h-4 rounded-full border border-gray-200 cursor-help transition hover:scale-110';
                        dot.style.backgroundColor = color;
                        dot.title = color; // ظهر كود اللون عند التمرير
                        paletteDiv.appendChild(dot);
                    });
                }
            }

            // تحديث حد الأحرف والملاحظات
            updateCharCount();
            loadDesignerNotes();
        }

        // === دوال ملاحظات المصمم ===
        function getMaxCharLimit() {
            return userTier === 'premium' ? 1000 : 280;
        }

        function updateCharCount() {
            const textarea = document.getElementById('designer-notes');
            const charCount = document.getElementById('char-count');

            if(!textarea || !charCount) return; // safety check

            const maxLimit = getMaxCharLimit();
            const currentLength = textarea.value.length;

            charCount.textContent = `${currentLength}/${maxLimit}`;
            textarea.maxLength = maxLimit;

            // تحديث الألوان بناءً على الامتلاء
            if (currentLength > maxLimit * 0.8) {
                charCount.classList.remove('bg-[#f59e0b]');
                charCount.classList.add('bg-red-500');
            } else {
                charCount.classList.remove('bg-red-500');
                charCount.classList.add('bg-[#f59e0b]');
            }
        }

        // لا نستخدم localStorage - الملاحظات فقط مع JSON (بيانات القالب)
        // updateCharCount() تُستدعى عند الكتابة فقط

        // إعادة تعيين canvas بدون حفظ
        function resetCanvasWithoutSave() {
            closeNewProjectModal();
            resetCanvas();
        }

        // إغلاق نافذة حفظ باسم
        // فتح نافذة حفظ باسم
        function openSaveAsModal() {
            document.getElementById('save-as-modal').classList.remove('hidden');
            document.getElementById('save-as-name').focus();
            // إعطاء اسم افتراضي (إنجليزي عام مع أرقام عشوائية)
            const randomNum = Math.floor(Math.random() * 1000000);
            const defaultName = `template_${randomNum}`;
            document.getElementById('save-as-name').value = defaultName;

            // إظهار خيار الملاحظات فقط إذا كان هناك ملاحظات
            const notesField = document.getElementById('designer-notes');
            const notesOption = document.getElementById('save-notes-option');
            const premiumOption = document.getElementById('notes-option-premium');
            const freeOption = document.getElementById('notes-option-free');

            if (notesField && notesOption && notesField.value.trim()) {
                notesOption.classList.remove('hidden');

                // إظهار الخيار المناسب حسب نوع المستخدم
                if (userTier === 'premium') {
                    premiumOption.classList.remove('hidden');
                    freeOption.classList.add('hidden');
                } else {
                    premiumOption.classList.add('hidden');
                    freeOption.classList.remove('hidden');
                }
            } else if (notesOption) {
                notesOption.classList.add('hidden');
            }
        }

        function closeSaveAsModal() {
            document.getElementById('save-as-modal').classList.add('hidden');
        }

        // --- وظائف مودال النجاح ---
        function showSuccessModal(message, title = 'تمت العملية') {
            const modal = document.getElementById('success-modal');
            const content = document.getElementById('success-modal-content');

            document.getElementById('success-modal-title').textContent = title;
            document.getElementById('success-modal-message').innerHTML = message; // Use innerHTML for formatting

            modal.classList.remove('hidden');
            // Trigger animation
            setTimeout(() => {
                modal.classList.remove('opacity-0');
                content.classList.remove('scale-90');
                content.classList.add('scale-100');
            }, 10);
        }

        function closeSuccessModal() {
            const modal = document.getElementById('success-modal');
            const content = document.getElementById('success-modal-content');

            modal.classList.add('opacity-0');
            content.classList.remove('scale-100');
            content.classList.add('scale-90');

            setTimeout(() => {
                modal.classList.add('hidden');
            }, 300);
        }

        // تنفيذ حفظ الملف باسم جديد (في القوالب المحفوظة)
        async function executeSaveAsFile() {
            const fileName = document.getElementById('save-as-name').value.trim();
            const callback = document.getElementById('save-as-callback').value || '';

            if (!fileName) {
                alert('❌ يرجى إدخال اسم المشروع');
                return;
            }

            try {
                // إعداد البيانات الكاملة للحفظ
                const card = document.getElementById('card');
                const projectData = {
                    name: fileName,
                    html: card.innerHTML,
                    width: card.style.width,
                    height: card.style.height,
                    wVal: card.getAttribute('data-card-width'),
                    hVal: card.getAttribute('data-card-height'),
                    customW: document.getElementById('custom-width').value,
                    customH: document.getElementById('custom-height').value,
                    timestamp: new Date().toLocaleString('ar-SA'),
                    version: "2.0"
                };

                // حفظ الملاحظات إذا اختار المستخدم ذلك
                const saveWithNotes = document.getElementById('save-with-notes');
                const notesField = document.getElementById('designer-notes');
                if (saveWithNotes && saveWithNotes.checked && notesField && notesField.value.trim()) {
                    projectData.notes = notesField.value.trim();
                }

                // 1. التنزيل المباشر كملف JSON (.dalal) للمستخدم
                const dataStr = JSON.stringify(projectData, null, 2);
                const blob = new Blob([dataStr], { type: "application/json" });
                const url = URL.createObjectURL(blob);

                const link = document.createElement('a');
                link.href = url;
                link.download = `${fileName}.template`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);

                // 2. الحفظ أيضاً في القوالب المحلية (للوصول السريع)
                try {
                    const templates = getTemplates();
                    // استخدام try-catch داخلي للتعامل مع مشكلة امتلاء التخزين
                    if (templates.length < MAX_TEMPLATES) {
                        // إضافة معرف فريد لتجنب التكرار
                        projectData.id = Date.now();
                        templates.push(projectData);
                        saveTemplates(templates, false); // false = ليس مشترك (خاص)
                    } else {
                        console.warn('Local templates full, file downloaded only.');
                    }
                } catch (storageError) {
                    console.error("خطأ في التخزين المحلي:", storageError);
                    // نتجاهل خطأ التخزين المحلي لأننا قمنا بتنزيل الملف بالفعل
                    // وهذا هو الأهم للمستخدم
                }

                showSuccessModal('تم حفظ المشروع بنجاح');
                closeSaveAsModal();
                document.getElementById('save-as-name').value = '';

                if (callback === 'newProject') {
                    closeNewProjectModal();
                    // تأخير بسيط لإظهار رسالة الحفظ قبل إعادة التعيين
                    setTimeout(() => {
                         resetCanvas();
                         document.getElementById('save-as-callback').value = '';
                    }, 1000);
                }

            } catch (err) {
                console.error(err);
                alert('❌ خطأ في الحفظ: ' + err.message);
            }
        }

        // دالة لتحميل المشروع من ملف
        function loadProjectFromFile(file) {
            const reader = new FileReader();

            reader.onload = function(e) {
                try {
                    const projectData = JSON.parse(e.target.result);

                    // تحقق من سلامة الملف
                    if (!projectData.html && !projectData.wVal && !projectData.width) {
                         throw new Error("Invalid project file");
                    }

                    // استعادة البيانات
                    const card = document.getElementById('card');
                    card.innerHTML = projectData.html;

                    // تصحيح مفاتيح البيانات (توافقية مع الإصدارات المختلفة)
                    const wVal = projectData.wVal || projectData.cardWidth;
                    const hVal = projectData.hVal || projectData.cardHeight;
                    const customW = projectData.customW || projectData.customWidth || '10';
                    const customH = projectData.customH || projectData.customHeight || '10';

                    // استعادة الأبعاد في الحقول
                    document.getElementById('custom-width').value = customW;
                    document.getElementById('custom-height').value = customH;

                    if (wVal && hVal) {
                        // استخدام دالة setCardSize لضمان تحديث كل شيء (المسطرة، التكبير، الورقة)
                        setCardSize(parseFloat(wVal), parseFloat(hVal));

                        // تحديث سمات البطاقة يدوياً للتأكد
                        card.setAttribute('data-card-width', wVal);
                        card.setAttribute('data-card-height', hVal);
                    } else if (projectData.width && projectData.height) {
                         // Fallback للنسخ القديمة جداً
                         card.style.width = projectData.width;
                         card.style.height = projectData.height;
                    }

                    // إعادة تفعيل الأحداث للعناصر (السحب، التحديد، إلخ)
                    rebindEvents();

                    // إعادة تعيين التدرج (مخفي افتراضياً)
                    hasGradient = false;
                    const grad = document.getElementById('card-gradient');
                    if(grad) grad.style.display = 'none';
                    const btn = document.getElementById('btn-grad');
                    if(btn) {
                        btn.classList.remove('bg-[#6366f1]', 'text-white');
                        btn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
                    }

                    // ضبط الزوم على 50% دائماً عند فتح ملف
                    setCustomZoom(50);

                    // استعادة الملاحظات من الملف
                    const notesField = document.getElementById('designer-notes');
                    if (projectData.notes && notesField) {
                        notesField.value = projectData.notes;
                        updateCharCount();
                    } else if (notesField) {
                        notesField.value = '';
                        updateCharCount();
                    }

                    // توسيط البطاقة في منطقة العمل
                    setTimeout(() => {
                        const workspace = document.getElementById('workspace');
                        if (workspace) {
                            const card = document.getElementById('card');
                            const cardRect = card.getBoundingClientRect();
                            const workspaceRect = workspace.getBoundingClientRect();

                            // حساب موقع التمرير للتوسيط
                            const scrollLeft = (workspace.scrollWidth - workspaceRect.width) / 2;
                            const scrollTop = (workspace.scrollHeight - workspaceRect.height) / 2;

                            workspace.scrollLeft = Math.max(0, scrollLeft);
                            workspace.scrollTop = Math.max(0, scrollTop);
                        }
                    }, 100);

                    showSuccessModal(`تم تحميل المشروع: ${projectData.name || 'بدون اسم'}`);

                } catch (err) {
                    console.error(err);
                    alert('❌ خطأ في قراءة ملف المشروع. الملف قد يكون تالفاً أو بصيغة غير صحيحة.');
                }
            };

            reader.readAsText(file);
        }

        // دالة لإعادة تعيين canvas للمشروع الجديد
        function resetCanvas() {
            const card = document.getElementById('card');
            card.innerHTML = '<div id="card-gradient"></div>'; // إعادة إنشاء التدرج مخفياً

            // إعادة تعيين الأبعاد الافتراضية
            const defaultSize = Math.round(6 * DPI_RATIO); // 6cm افتراضي
            document.getElementById('custom-width').value = '6';
            document.getElementById('custom-height').value = '6';

            setCardSize(defaultSize, defaultSize);

            // تصفير ال undo/redo
            undoStack = [];
            redoStack = [];

            // حفظ الحالة الأولية
            saveState();

            // إعادة تعيين التدرج
            hasGradient = false;
            const grad = document.getElementById('card-gradient');
            if(grad) grad.style.display = 'none';
            const btn = document.getElementById('btn-grad');
            if(btn) {
                btn.classList.remove('bg-[#6366f1]', 'text-white');
                btn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
            }

            // إعادة تعيين متغير القالب المحمل
            currentLoadedTemplateIndex = null;

            // حذف الملاحظات عند إنشاء عمل جديد
            if(document.getElementById('designer-notes')) {
                document.getElementById('designer-notes').value = '';
                updateCharCount();
            }

            // إعادة تعيين قائمة القوالب
            document.getElementById('template-select').value = '';

            showSuccessModal('تم بدء مشروع جديد بنجاح');
        }

        function loadTemplate(index) {
            if (index === "") return;

            if(!confirm('هل أنت متأكد من فتح القالب؟ سيتم استبدال العمل الحالي.')) {
                return;
            }

            const templates = getTemplates();
            const template = templates[index];

            if (template) {
                const card = document.getElementById('card');

                // استعادة الأبعاد
                card.style.width = template.width;
                card.style.height = template.height;
                card.setAttribute('data-card-width', template.wVal);
                card.setAttribute('data-card-height', template.hVal);

                // استعادة المحتوى
                card.innerHTML = template.html;

                // استعادة قيم الحقول
                if (template.customW) document.getElementById('custom-width').value = template.customW;
                if (template.customH) document.getElementById('custom-height').value = template.customH;

                // استعادة الملاحظات من بيانات القالب نفسه فقط (JSON)
                const notesField = document.getElementById('designer-notes');
                if (template.notes && notesField) {
                    notesField.value = template.notes;
                    updateCharCount();
                } else if (notesField) {
                    notesField.value = '';
                    updateCharCount();
                }

                // تحديث المسطرة والزوم
                const w = parseFloat(template.wVal);
                const h = parseFloat(template.hVal);
                setCardSize(w, h); // هذا سيعيد رسم المسطرة

                // إعادة تفعيل الأحداث للعناصر
                rebindEvents();

                // إعادة تعيين التدرج (مخفي افتراضياً)
                hasGradient = false;
                const grad = document.getElementById('card-gradient');
                if(grad) grad.style.display = 'none';
                const btn = document.getElementById('btn-grad');
                if(btn) {
                    btn.classList.remove('bg-[#6366f1]', 'text-white');
                    btn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
                }

                // تسجيل القالب المحمل حالياً
                currentLoadedTemplateIndex = index;

                // إعادة تصفير التحديد
                document.getElementById('template-select').value = "";
                undoStack = []; // تصفير التراجع لبداية جديدة
                redoStack = [];
            }
        }

        function deleteSelectedTemplate() {
            const select = document.getElementById('template-select');
            const index = select.value;

            if (index === "") {
                alert('يرجى اختيار قالب من القائمة أولاً لحذفه.');
                return;
            }

            const allTemplates = getTemplates();
            const selectedTemplate = allTemplates[index];

            // تحديد إذا كان القالب مشترك أم خاص
            const userTemplates = JSON.parse(localStorage.getItem(getUserTemplatesKey()) || '[]');
            const sharedTemplates = JSON.parse(localStorage.getItem(SHARED_TEMPLATES_KEY) || '[]');

            const isShared = sharedTemplates.some(t => t.id === selectedTemplate.id);

            if (isShared) {
                return;
            }

            if(confirm(`هل أنت متأكد من حذف هذا القالب؟\n"${selectedTemplate.name}"\n\nلا يمكن التراجع عن هذا الإجراء.`)) {
                // حذف من القوالب الخاصة فقط
                const updatedUserTemplates = userTemplates.filter(t => t.id !== selectedTemplate.id);
                saveTemplates(updatedUserTemplates, false);
                alert('✅ تم حذف القالب.');
                select.value = "";
            }
        }

        // --- ميزة استخراج الأصول (فتح كعناصر) ---
        function openTemplateAsAssets() {
            const select = document.getElementById('template-select');
            const index = select.value;

            if (index === "") {
                alert('يرجى اختيار قالب من القائمة أولاً لفتحه كعناصر.');
                return;
            }

            const templates = getTemplates();
            const template = templates[index];
            if (!template) return;

            // تحليل محتوى القالب لاستخراج الصور والنصوص
            const parser = new DOMParser();
            const doc = parser.parseFromString(template.html, 'text/html');

            const images = [];
            doc.querySelectorAll('.image-layer img').forEach(img => {
                images.push(img.src);
            });

            const texts = [];
            doc.querySelectorAll('.text-layer .user-text').forEach(txt => {
                if(txt.innerText.trim()) texts.push(txt.innerText);
            });

            if (images.length === 0 && texts.length === 0) {
                alert('هذا القالب لا يحتوي على صور أو نصوص قابلة للاستخراج.');
                return;
            }

            // تعبئة النافذة العائمة
            const contentDiv = document.getElementById('asset-content');
            contentDiv.innerHTML = '';

            // إضافة الصور
            images.forEach(src => {
                const item = document.createElement('div');
                item.className = 'asset-item';
                item.innerHTML = `<img src="${src}" alt="asset">`;
                item.onclick = () => addAssetImage(src);
                contentDiv.appendChild(item);
            });

            // إضافة النصوص
            texts.forEach(txt => {
                const item = document.createElement('div');
                item.className = 'asset-item';
                item.innerHTML = `<div class="asset-item-text">${txt.substring(0, 20)}${txt.length>20?'...':''}</div>`;
                item.onclick = () => { addTextToCanvas(txt, false); saveState(); };
                contentDiv.appendChild(item);
            });

            // إظهار النافذة
            document.getElementById('asset-window').style.display = 'flex';
        }

        // دالة مساعدة لإضافة صورة من رابط مباشر (للأصول)
        function addAssetImage(src) {
            const wrapper = createWrapper('image-layer');
            const contentWrapper = wrapper.querySelector('.content-wrapper');
            wrapper.style.width = '60%';
            wrapper.style.height = '60%';
            contentWrapper.style.width = '100%';
            contentWrapper.style.height = '100%';
            contentWrapper.style.overflow = 'hidden';
            contentWrapper.style.borderRadius = '8px';
            contentWrapper.style.display = 'flex';

            const img = document.createElement('img');
            img.crossOrigin = "anonymous";
            img.src = src;
            img.loading = "eager";
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'contain';
            img.style.pointerEvents = 'none';

            // حفظ الأصل
            wrapper.setAttribute('data-original-image', src);

            contentWrapper.appendChild(img);
            document.getElementById('card').appendChild(wrapper);
            selectEl(wrapper);
            setupInteract(wrapper, 'box');
            saveState();
        }

        // دالة لتحريك نافذة الأصول
        function initAssetWindowDrag() {
            const el = document.getElementById('asset-window');
            const header = document.getElementById('asset-header');

            let isDragging = false;
            let startX, startY, initialLeft, initialTop;

            header.addEventListener('mousedown', (e) => {
                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;
                initialLeft = el.offsetLeft;
                initialTop = el.offsetTop;
                e.preventDefault();
            });

            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                el.style.left = `${initialLeft + dx}px`;
                el.style.top = `${initialTop + dy}px`;
            });

            document.addEventListener('mouseup', () => {
                isDragging = false;
            });

            // Touch support for dragging window
            header.addEventListener('touchstart', (e) => {
                isDragging = true;
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
                initialLeft = el.offsetLeft;
                initialTop = el.offsetTop;
                e.preventDefault();
            });

            document.addEventListener('touchmove', (e) => {
                if (!isDragging) return;
                const dx = e.touches[0].clientX - startX;
                const dy = e.touches[0].clientY - startY;
                el.style.left = `${initialLeft + dx}px`;
                el.style.top = `${initialTop + dy}px`;
            });

            document.addEventListener('touchend', () => {
                isDragging = false;
            });
        }

        // --- وظائف الحفظ الجديدة المباشرة ---

        async function saveWorkDirectly() {
             const overlay = document.getElementById('export-overlay');
             const loadingText = overlay.querySelector('.text-white');
             if(loadingText) loadingText.innerText = "جاري حفظ العمل...";
             overlay.style.display = 'flex';

             try {
                // لا نلغي التحديد - نحتاج الصورة محددة للممحاة
                const card = document.getElementById('card');
                await new Promise(r => setTimeout(r, 200));

                // إزالة نمط الشطرنج مؤقتاً إذا كان موجوداً
                const hadTransparentPattern = card.classList.contains('transparent-pattern');
                if (hadTransparentPattern) {
                    card.classList.remove('transparent-pattern');
                    card.style.backgroundImage = 'none';
                    card.style.backgroundColor = 'transparent';
                }

                // الحفظ بالحجم الفعلي بدقة 300 DPI
                const pixelRatio = 4; // للحفاظ على جودة عالية
                const actualWidth = parseInt(card.getAttribute('data-card-width')) || card.offsetWidth;
                const actualHeight = parseInt(card.getAttribute('data-card-height')) || card.offsetHeight;

                // إعدادات التصدير
                const options = {
                    pixelRatio: pixelRatio,
                    cacheBust: true,
                    width: actualWidth,
                    height: actualHeight,
                    style: {
                        transform: 'none',
                        boxShadow: 'none',
                        margin: '0',
                        border: 'none',
                        backgroundImage: 'none'
                    }
                };

                // إذا لم يكن شفافاً، نضيف خلفية بيضاء
                if (!isTransparent) {
                    options.backgroundColor = '#ffffff';
                }

                const dataUrl = await htmlToImage.toPng(card, options);

                // إعادة نمط الشطرنج
                if (hadTransparentPattern) {
                    card.classList.add('transparent-pattern');
                    card.style.backgroundImage = '';
                    card.style.backgroundColor = 'transparent';
                }

                const link = document.createElement('a');
                link.download = `design-${Date.now()}.png`;
                link.href = dataUrl;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

             } catch (err) {
                 console.error(err);
                 alert("حدث خطأ أثناء الحفظ");
             } finally {
                 overlay.style.display = 'none';
             }
        }

        // دالة إغلاق مودال الطباعة A4 مع استعادة الزوم
        function closeA4Modal() {
            document.getElementById('save-modal').style.display = 'none';
            // استعادة الزوم إلى ما كان عليه قبل فتح المودال
            if (savedZoomBeforeA4 !== null) {
                setCustomZoom(savedZoomBeforeA4);
            }
        }

        async function generateA4Sheet() {
            const loadingText = document.querySelector('#export-overlay .text-white');
            if(loadingText) loadingText.innerText = "جاري معالجة الصور والخطوط...";

            const overlay = document.getElementById('export-overlay');
            overlay.style.display = 'flex';

            deselect();

            // حفظ مستوى الزوم الحالي
            savedZoomBeforeA4 = window.currentZoom || 100;
            const card = document.getElementById('card');

            try {
                // 1. إعادة تعيين الزوم (مهم جداً للدقة)
                setCustomZoom(100);

                // 2. انتظار تحميل الخطوط (حل لمشكلة الخطوط في الآيفون)
                if (document.fonts) {
                    await document.fonts.ready;
                }

                // 3. تحويل جميع الصور إلى Base64 (حل لمشكلة اختفاء الصور في الآيفون)
                // هذا يمنع المتصفح من حظر الصور الخارجية أثناء التصدير
                await convertAllImagesToDataURL(card);

                // 4. إزالة نمط الشطرنج مؤقتاً قبل التصوير (لكي تكون الصورة شفافة فعلاً)
                const hadTransparentPattern = card.classList.contains('transparent-pattern');
                if (hadTransparentPattern) {
                    card.classList.remove('transparent-pattern');
                    // إزالة الـ inline styles المتعلقة بالخلفية أيضاً
                    card.style.backgroundImage = 'none';
                    card.style.backgroundColor = 'transparent';
                }

                // --- إضافة تكتيك "الإحماء" المستوحى من ملفات القرآن ---
                try {
                    // دورة "إحماء" وهمية لتجهيز المتصفح ومحرك الرسم
                    await htmlToImage.toPng(card, {
                        quality: 0.1,
                        pixelRatio: 0.5,
                        width: 100, // حجم صغير جداً
                        height: 100
                    });
                } catch(e) {
                    // نتجاهل الـ error هنا، المهم المحاولة
                }

                // تأخير بسيط للاستقرار بعد الإحماء
                await new Promise(r => setTimeout(r, 500));

                if(loadingText) loadingText.innerText = "جاري إنشاء الملف...";

                let cardDataUrl = null;

                // كشف بسيط للجوال
                const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) || window.innerWidth < 800;
                // الآيفون يحتاج جودة أقل قليلاً لتفادي الانهيار، لكن التحويل لـ Base64 أعلاه هو الحل الحقيقي
                const qualityScale = isMobile ? 1.5 : 2;

                // --- استراتيجية التوليد المتعدد ---

                // دالة مساعدة لتشغيل htmlToImage
                const tryHtmlToImage = async (pixelRatioVal = 2) => {
                    if (typeof htmlToImage === 'undefined') throw new Error("htmlToImage missing");

                    // إعدادات التصدير
                    const options = {
                        pixelRatio: pixelRatioVal,
                        cacheBust: false,
                        skipAutoScale: true,
                        width: card.offsetWidth,
                        height: card.offsetHeight,
                        style: {
                            transform: 'none',
                            boxShadow: 'none',
                            margin: '0',
                            backgroundImage: 'none' // منع نمط الشطرنج
                        },
                        filter: (node) => {
                            return !node.classList || !node.classList.contains('control-box');
                        }
                    };

                    // إذا كان المستخدم اختار الشفافية، لا نضيف backgroundColor
                    // وإذا أراد خلفية، نضيفها بيضاء
                    if (!isTransparent) {
                        options.backgroundColor = '#ffffff';
                    }
                    // لا نضيف backgroundColor إطلاقاً للشفافية (هذا يجعل PNG شفاف)

                    return await htmlToImage.toPng(card, options);
                };

                // دالة مساعدة لتشغيل html2canvas
                const tryHtml2Canvas = async (scaleVal = 2) => {
                    if (typeof html2canvas === 'undefined') throw new Error("html2canvas missing");
                    // html2canvas أحياناً أفضل في التعامل مع التحويلات المعقدة
                    const canvas = await html2canvas(card, {
                        scale: scaleVal,
                        useCORS: true,
                        allowTaint: true,
                        backgroundColor: null, // شفاف
                        logging: false,
                        scrollX: 0, scrollY: 0, x: 0, y: 0,
                        width: card.offsetWidth,
                        height: card.offsetHeight
                    });
                    return canvas.toDataURL('image/png');
                };

                // محاولة التوليد
                try {
                     // نبدأ بـ htmlToImage لأنها أدق للنصوص
                    cardDataUrl = await Promise.race([
                        tryHtmlToImage(qualityScale),
                        new Promise((_, r) => setTimeout(() => r(new Error('Timeout 1')), 15000))
                    ]);
                } catch (err1) {
                    console.warn("فشلت المحاولة الأولى، جاري تجربة html2canvas...", err1);
                    try {
                        cardDataUrl = await Promise.race([
                            tryHtml2Canvas(qualityScale),
                            new Promise((_, r) => setTimeout(() => r(new Error('Timeout 2')), 10000))
                        ]);
                    } catch (err2) {
                        // محاولة أخيرة بجودة منخفضة
                        try {
                             cardDataUrl = await Promise.race([
                                tryHtmlToImage(1),
                                new Promise((_, r) => setTimeout(() => r(new Error('Timeout 3')), 5000))
                            ]);
                        } catch (err3) {
                            throw new Error("فشلت جميع محاولات إنشاء الصورة.");
                        }
                    }
                }

                // --- استعادة الصور الأصلية (مهم لتخفيف الذاكرة) ---
                restoreOriginalImages(card);

                // --- إعادة نمط الشطرنج إذا كان موجوداً ---
                if (hadTransparentPattern) {
                    card.classList.add('transparent-pattern');
                    card.style.backgroundImage = ''; // إعادة تفعيل CSS
                    card.style.backgroundColor = 'transparent';
                }

                if (!cardDataUrl) throw new Error("لم يتم إنشاء بيانات الصورة");

                currentCardData = cardDataUrl;

                // إعداد أبعاد A4 (300 DPI)
                const A4_WIDTH = 2480;
                const A4_HEIGHT = 3508;

                const cardW = card.offsetWidth;
                const cardH = card.offsetHeight;
                const GAP = 40;

                // حساب التوزيع
                const portraitCols = Math.floor((A4_WIDTH + GAP) / (cardW + GAP));
                const portraitRows = Math.floor((A4_HEIGHT + GAP) / (cardH + GAP));
                const portraitCount = portraitCols * portraitRows;

                const landscapeCols = Math.floor((A4_HEIGHT + GAP) / (cardW + GAP));
                const landscapeRows = Math.floor((A4_WIDTH + GAP) / (cardH + GAP));
                const landscapeCount = landscapeCols * landscapeRows;

                let finalCanvasW, finalCanvasH, cols, rows;

                if (landscapeCount > portraitCount) {
                    finalCanvasW = A4_HEIGHT; finalCanvasH = A4_WIDTH;
                    cols = landscapeCols; rows = landscapeRows;
                } else {
                    finalCanvasW = A4_WIDTH; finalCanvasH = A4_HEIGHT;
                    cols = portraitCols; rows = portraitRows;
                }

                currentA4Layout = {
                    canvasW: finalCanvasW, canvasH: finalCanvasH,
                    cols: cols, rows: rows,
                    cardW: cardW, cardH: cardH,
                    gap: GAP,
                    maxCopies: cols * rows
                };

                // عرض المودال بعد تجهيز الصورة
                const img = new Image();
                img.onload = () => {
                    cachedCardImage = img;

                    document.getElementById('a4-count').max = currentA4Layout.maxCopies;
                    document.getElementById('a4-count').value = currentA4Layout.maxCopies;
                    document.getElementById('a4-max-text').innerText = `(من أصل ${currentA4Layout.maxCopies})`;

                    renderA4Preview(currentA4Layout.maxCopies);

                    overlay.style.display = 'none';
                    document.getElementById('save-modal').style.display = 'flex';

                    // استعادة الزوم بعد النجاح
                    setCustomZoom(savedZoomBeforeA4);
                };
                img.onerror = () => { throw new Error("فشل تحميل الصورة المنشأة"); };
                img.src = cardDataUrl;

            } catch (err) {
                console.error("خطأ في A4:", err);
                overlay.style.display = 'none';
                // استعادة الزوم عند الفشل
                setCustomZoom(savedZoomBeforeA4);
                showInfoModal('حدثت مشكلة أثناء المعالجة. حاول تقليل عدد العناصر أو جودة الصور.', 'عذراً', '⚠️');
            }
        }

        // دالة للانتظار لتحميل جميع الصور
        function waitForImagesLoad(element) {
            const images = element.querySelectorAll('img');

            if (images.length === 0) {
                return Promise.resolve();
            }

            const promises = Array.from(images).map(img => {
                return new Promise(resolve => {
                    if (!img.src) {
                        resolve();
                        return;
                    }

                    if (img.complete && img.naturalWidth > 0) {
                        resolve();
                        return;
                    }

                    const onLoad = () => {
                        img.removeEventListener('load', onLoad);
                        img.removeEventListener('error', onLoad);
                        resolve();
                    };

                    img.addEventListener('load', onLoad, { once: true });
                    img.addEventListener('error', onLoad, { once: true });

                    setTimeout(resolve, 2000);
                });
            });

            return Promise.all(promises);
        }

        // دالة جديدة لتحديث المعاينة عند تغيير الرقم
        function updateA4Count() {
            const input = document.getElementById('a4-count');
            let count = parseInt(input.value);

            // التحقق من الحدود
            if (isNaN(count) || count < 1) count = 1;
            if (count > currentA4Layout.maxCopies) count = currentA4Layout.maxCopies;

            renderA4Preview(count);
        }

        // دالة الرسم المنفصلة
        function renderA4Preview(count) {
            if (!cachedCardImage || !currentA4Layout) return;

            const canvas = document.createElement('canvas');
            canvas.width = currentA4Layout.canvasW;
            canvas.height = currentA4Layout.canvasH;
            const ctx = canvas.getContext('2d');

            // إذا كان المستخدم اختار شفافية، نترك الكانفس شفاف، وإلا نملأه بالأبيض
            if (!isTransparent) {
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }

            const totalW = currentA4Layout.cols * currentA4Layout.cardW + (currentA4Layout.cols - 1) * currentA4Layout.gap;
            const totalH = currentA4Layout.rows * currentA4Layout.cardH + (currentA4Layout.rows - 1) * currentA4Layout.gap;
            const startX = (canvas.width - totalW) / 2;
            const startY = (canvas.height - totalH) / 2;

            let drawnCount = 0;
            const showCutLines = document.getElementById('show-cut-lines').checked;
            const cutLinesOpacity = document.getElementById('cut-lines-opacity').value / 100;

            // رسم النسخ حسب العدد المطلوب
            outerLoop:
            for (let j = 0; j < currentA4Layout.rows; j++) {
                for (let i = 0; i < currentA4Layout.cols; i++) {
                    if (drawnCount >= count) break outerLoop;

                    const x = startX + (i * (currentA4Layout.cardW + currentA4Layout.gap));
                    const y = startY + (j * (currentA4Layout.cardH + currentA4Layout.gap));

                    ctx.drawImage(cachedCardImage, x, y, currentA4Layout.cardW, currentA4Layout.cardH);

                    // إطار القص الرمادي - فقط إذا كان الـ checkbox مفعل مع الشفافية المتحكم بها
                    if (showCutLines) {
                        ctx.save();
                        ctx.globalAlpha = cutLinesOpacity;
                        ctx.strokeStyle = '#94a3b8';
                        ctx.lineWidth = 2;
                        ctx.strokeRect(x, y, currentA4Layout.cardW, currentA4Layout.cardH);
                        ctx.restore();
                    }

                    drawnCount++;
                }
            }

            // إضافة العلامة المائية (Watermark) - فقط للمستخدمين المجانيين
            if (userTier !== 'premium') {
                ctx.save();
                ctx.globalAlpha = 0.08; // شفافية 8% فقط
                ctx.fillStyle = '#000000'; // لون أسود خفيف جداً
                ctx.font = 'bold 180px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.rotate(-Math.PI / 4); // دوران 45 درجة

                // رسم النص على كامل الصفحة بمسافات أكبر (بدون تداخل)
                const diagonalLength = Math.sqrt(canvas.width * canvas.width + canvas.height * canvas.height);
                const startPosX = -diagonalLength / 2;
                const startPosY = -diagonalLength / 2;

                for (let x = startPosX; x < diagonalLength; x += 1000) {
                    for (let y = startPosY; y < diagonalLength; y += 800) {
                        ctx.fillText('despro.net', x, y);
                    }
                }

                ctx.restore();
            }

            const saveImg = document.getElementById('save-img');
            // إذا كان التصميم شفاف، استخدم PNG. وإلا استخدم JPEG بجودة 85% لتقليل الحجم
            const imgData = isTransparent ? canvas.toDataURL('image/png') : canvas.toDataURL('image/jpeg', 0.85);
            saveImg.src = imgData;
        }

        function downloadPDF() {
            const { jsPDF } = window.jspdf;
            const imgData = document.getElementById('save-img').src;
            // A4 size in mm: 210 x 297
            const pdf = new jsPDF('p', 'mm', 'a4');
            const width = pdf.internal.pageSize.getWidth();
            const height = pdf.internal.pageSize.getHeight();

            // حساب النسبة الصحيحة بناءً على حجم الصورة الفعلي
            const img = new Image();
            img.onload = function() {
                const imgWidth = img.width;
                const imgHeight = img.height;
                const imgAspectRatio = imgWidth / imgHeight;
                const pageAspectRatio = width / height;

                let finalWidth = width;
                let finalHeight = height;

                if(imgAspectRatio > pageAspectRatio) {
                    // الصورة أعرض
                    finalHeight = width / imgAspectRatio;
                } else {
                    // الصورة أطول
                    finalWidth = height * imgAspectRatio;
                }

                // وضع الصورة في الوسط
                const x = (width - finalWidth) / 2;
                const y = (height - finalHeight) / 2;

                pdf.addImage(imgData, 'PNG', x, y, finalWidth, finalHeight);

                const randomNum = Math.floor(Math.random() * 1000000);
                pdf.save(`template_${randomNum}.pdf`);
            };
            img.src = imgData;
        }

        async function sendToTelegramPDF(btnElement) {
            if (TG_BOT_TOKEN === "YOUR_BOT_TOKEN_HERE" || TG_CHAT_ID === "YOUR_CHAT_ID_HERE") {
                alert("الرجاء وضع التوكن والشات آيدي في الكود أولاً (في بداية السكربت)!");
                return;
            }

            const originalText = btnElement.innerHTML;
            btnElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الإرسال...';
            btnElement.disabled = true;
            btnElement.classList.add('opacity-75', 'cursor-not-allowed');

            try {
                const { jsPDF } = window.jspdf;
                const imgData = document.getElementById('save-img').src;
                // A4 size in mm: 210 x 297
                const pdf = new jsPDF('p', 'mm', 'a4');
                const width = pdf.internal.pageSize.getWidth();
                const height = pdf.internal.pageSize.getHeight();

                // حساب النسبة الصحيحة بناءً على حجم الصورة الفعلي
                const img = new Image();
                img.onload = async function() {
                    const imgWidth = img.width;
                    const imgHeight = img.height;
                    const imgAspectRatio = imgWidth / imgHeight;
                    const pageAspectRatio = width / height;

                    let finalWidth = width;
                    let finalHeight = height;

                    if(imgAspectRatio > pageAspectRatio) {
                        // الصورة أعرض
                        finalHeight = width / imgAspectRatio;
                    } else {
                        // الصورة أطول
                        finalWidth = height * imgAspectRatio;
                    }

                    // وضع الصورة في الوسط
                    const x = (width - finalWidth) / 2;
                    const y = (height - finalHeight) / 2;

                    pdf.addImage(imgData, 'PNG', x, y, finalWidth, finalHeight);

                    // تحويل الـ PDF إلى Blob
                    const pdfBlob = pdf.output('blob');

                    const randomNum = Math.floor(Math.random() * 1000000);

                    // تجهيز البيانات للإرسال
                    const formData = new FormData();
                    formData.append("chat_id", TG_CHAT_ID);
                    formData.append("document", pdfBlob, `template_${randomNum}.pdf`);
                    formData.append("caption", "تم إرسال التصميم 🎨✨");

                    // الإرسال إلى تليجرام
                    const response = await fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendDocument`, {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.ok) {
                        alert("✅ تم الإرسال بنجاح إلى تليجرام!");
                    } else {
                        console.error(result);
                        alert("❌ فشل الإرسال: " + (result.description || "خطأ غير معروف"));
                    }
                };
                img.onerror = function() {
                    alert("❌ فشل تحميل الصورة");
                };
                img.src = imgData;

            } catch (error) {
                console.error(error);
                alert("❌ حدث خطأ أثناء الاتصال بتليجرام");
            } finally {
                btnElement.innerHTML = originalText;
                btnElement.disabled = false;
                btnElement.classList.remove('opacity-75', 'cursor-not-allowed');
            }
        }

        // --- باقي الوظائف الأساسية ---

        // Helper functions for Image Pre-processing (Critical for iOS)

        async function convertAllImagesToDataURL(element) {
            const images = Array.from(element.querySelectorAll('img'));

            // استخدام تسلسل للمعالجة لتخفيف الضغط على المعالج في الآيفون
            // بدلاً من معالجة كل الصور دفعة واحدة
            for (const img of images) {
                // تجاهل الصور المخفية تماماً
                if (img.style.display === 'none' || getComputedStyle(img).opacity === '0') continue;

                // حفظ الرابط الأصلي للاستعادة
                if (!img.dataset.originalSrc) {
                    img.dataset.originalSrc = img.src;
                }

                try {
                    // 1. تحضير الصورة في الذاكرة (Canvas)
                    const dataUrl = await new Promise((resolve, reject) => {
                        const tempImg = new Image();
                        tempImg.crossOrigin = "Anonymous";

                        tempImg.onload = () => {
                            const canvas = document.createElement('canvas');
                            // تقليل الحجم أكثر للأمان في الآيفون (800px كافية جداً للطباعة المصغرة في A4)
                            const MAX_DIMENSION = 800;
                            let width = tempImg.naturalWidth;
                            let height = tempImg.naturalHeight;

                            if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
                                const ratio = Math.min(MAX_DIMENSION / width, MAX_DIMENSION / height);
                                width *= ratio;
                                height *= ratio;
                            }

                            canvas.width = width;
                            canvas.height = height;

                            const ctx = canvas.getContext('2d');
                            ctx.drawImage(tempImg, 0, 0, width, height);

                            resolve(canvas.toDataURL('image/png'));
                        };

                        tempImg.onerror = () => {
                            // محاولة أخيرة عبر fetch المباشر
                             fetch(img.src, { mode: 'cors' })
                                .then(r => r.blob())
                                .then(b => {
                                    const fr = new FileReader();
                                    fr.onload = () => resolve(fr.result);
                                    fr.readAsDataURL(b);
                                })
                                .catch(() => resolve(img.src)); // ابق على القديم
                        };

                        // كسر الكاش بقوة
                        const src = img.src;
                        if (src.startsWith('data:')) {
                            tempImg.src = src;
                        } else {
                            tempImg.src = src + (src.includes('?') ? '&' : '?') + 't=' + Date.now();
                        }
                    });

                    // 2. الخطوة الأهم: تعيين المصدر والانتظار حتى "يفهم" المتصفح الصورة الجديدة
                    img.src = dataUrl;
                    img.srcset = "";

                    // إجبار المتصفح على فك تشفير الصورة قبل الانتقال للتالية
                    if (img.decode) {
                        await img.decode().catch(() => {});
                    } else if (!img.complete) {
                        await new Promise(r => { img.onload = r; img.onerror = r; setTimeout(r, 1000); });
                    }

                } catch (e) {
                    console.warn('Error converting image:', e);
                }
            }
        }

        function restoreOriginalImages(element) {
            const images = element.querySelectorAll('img');
            images.forEach(img => {
                if (img.dataset.originalSrc) {
                    img.src = img.dataset.originalSrc;
                    delete img.dataset.originalSrc;
                }
            });
        }

        // يُستدعى بعد أي تغيير لحفظ الحالة الجديدة
        function saveState() {
            const card = document.getElementById('card');
            const currentState = {
                html: card.innerHTML,
                width: card.style.width,
                height: card.style.height
            };

            // تجنب حفظ نفس الحالة مرتين متتاليتين
            if (undoStack.length > 0) {
                const lastState = undoStack[undoStack.length - 1];
                if (lastState.html === currentState.html &&
                    lastState.width === currentState.width &&
                    lastState.height === currentState.height) {
                    return; // نفس الحالة، لا داعي للحفظ
                }
            }

            undoStack.push(currentState);
            // Keep max 50 states
            if (undoStack.length > 50) undoStack.shift();
            // Clear redo when new action is taken
            redoStack = [];

            console.log('State saved. Undo stack size:', undoStack.length);
        }

        function updateHistoryButtons() {
            // Visual feedback (optional)
        }

        function undoAction() {
            console.log('Undo called. Stack size:', undoStack.length);

            // نحتاج على الأقل حالتين: الحالية والسابقة
            if(undoStack.length < 2) {
                console.log('Nothing to undo - need at least 2 states');
                return;
            }

            // الحالة الحالية (آخر عنصر) نضعها في redo
            const currentState = undoStack.pop();
            redoStack.push(currentState);

            // الحالة السابقة (الآن آخر عنصر بعد pop)
            const previousState = undoStack[undoStack.length - 1];

            console.log('Restoring to previous state. Undo stack now:', undoStack.length);

            // استعادة الحالة السابقة
            applyState(previousState);
        }

        function redoAction() {
            console.log('Redo called. Stack size:', redoStack.length);

            if(redoStack.length === 0) {
                console.log('Nothing to redo');
                return;
            }

            // استرجاع الحالة من redo
            const nextState = redoStack.pop();

            // إضافتها إلى undo
            undoStack.push(nextState);

            console.log('Restoring next state. Undo stack now:', undoStack.length);

            // تطبيق الحالة
            applyState(nextState);
        }

        // تطبيق حالة بدون حفظها (لتجنب التكرار)
        function applyState(state) {
            const card = document.getElementById('card');

            if (typeof state === 'string') {
                card.innerHTML = state;
            } else {
                card.innerHTML = state.html;
                if (state.width && state.height) {
                    const w = parseFloat(state.width);
                    const h = parseFloat(state.height);
                    setCardSize(w, h);

                    const customWidth = document.getElementById('custom-width');
                    const customHeight = document.getElementById('custom-height');
                    if(customWidth && customHeight) {
                        const cmW = w / DPI_RATIO;
                        const cmH = h / DPI_RATIO;
                        customWidth.value = cmW.toFixed(2);
                        customHeight.value = cmH.toFixed(2);
                    }
                }
            }

            rebindEvents();
            deselect();
        }

        // دالة قديمة للتوافقية
        function restoreState(state) {
            applyState(state);
        }

        function rebindEvents() {
            document.querySelectorAll('.draggable-el').forEach(el => {
                // إزالة الخصائص القديمة لفرض إعادة ربط الأحداث
                el.removeAttribute('data-events-bound');
                setupInteract(el, el.classList.contains('text-layer') ? 'text' : 'box');
            });
        }

        function createWrapper(type) {
            const div = document.createElement('div');
            div.className = `draggable-el ${type} selected`;

            // تعيين z-index افتراضي حسب نوع العنصر
            const card = document.getElementById('card');
            const layers = card.querySelectorAll('.draggable-el:not(.bg-image)');
            let maxZ = 10;
            layers.forEach(layer => {
                const z = parseInt(layer.style.zIndex) || 10;
                if (z > maxZ) maxZ = z;
            });
            div.style.zIndex = maxZ + 1;

            const controls = `
                <div class="control-btn delete-btn" onclick="removeEl(this.parentNode)" ontouchend="removeEl(this.parentNode); event.preventDefault(); event.stopPropagation();"><i class="fas fa-times"></i></div>
                <div class="control-btn duplicate-btn" onclick="duplicateElement(this.parentNode)" ontouchend="duplicateElement(this.parentNode); event.preventDefault(); event.stopPropagation();"><i class="fas fa-clone"></i></div>
                <div class="control-btn rotate-btn" onclick="rotateElement(this.parentNode)" ontouchend="rotateElement(this.parentNode); event.preventDefault(); event.stopPropagation();"><i class="fas fa-redo"></i></div>
                <div class="control-btn layer-up-btn" onclick="bringToFront(this.parentNode)" ontouchend="bringToFront(this.parentNode); event.preventDefault(); event.stopPropagation();" title="للأمام"><i class="fas fa-arrow-up"></i></div>
                <div class="control-btn layer-down-btn" onclick="sendToBack(this.parentNode)" ontouchend="sendToBack(this.parentNode); event.preventDefault(); event.stopPropagation();" title="للخلف"><i class="fas fa-arrow-down"></i></div>
                <div class="move-handle" title="اسحب للتحريك"><i class="fas fa-arrows-alt"></i></div>
                <div class="handle resize-nw"></div>
                <div class="handle resize-ne"></div>
                <div class="handle resize-sw"></div>
                <div class="handle resize-se"></div>
                <div class="handle resize-n"></div>
                <div class="handle resize-e"></div>
                <div class="handle resize-s"></div>
                <div class="handle resize-w"></div>
            `;
            div.innerHTML = controls;

            const contentWrapper = document.createElement('div');
            contentWrapper.className = 'content-wrapper';
            contentWrapper.style.width = '100%';
            contentWrapper.style.height = '100%';
            div.appendChild(contentWrapper);

            div.insertBefore(contentWrapper, div.lastChild);

            return div;
        }

        function addUserText() {
            const input = document.getElementById('user-text-input');
            const text = input.value.trim();
            if(!text) return;

            addTextToCanvas(text, false);
            saveState();
            input.value = '';
        }

        function addTextToCanvas(content, isQuran) {
            const wrapper = createWrapper('text-layer');
            wrapper.style.color = '#1e293b';
            wrapper.style.fontSize = '30px';
            wrapper.style.fontFamily = "'Cairo', sans-serif";
            wrapper.style.fontWeight = '600';
            wrapper.style.letterSpacing = '0.3px';

            const textDiv = document.createElement('div');
            textDiv.className = 'user-text';
            textDiv.contentEditable = true;
            textDiv.innerText = content;
            textDiv.onblur = function() { if(this.innerText.trim() === '') this.innerText = 'نص...'; saveState(); };

            wrapper.appendChild(textDiv);
            document.getElementById('card').appendChild(wrapper);

            selectEl(wrapper);
            setupInteract(wrapper, 'text');
        }

        function toggleFrameDropdown() {
             const dropdown = document.getElementById('frames-dropdown');
             const shapesDropdown = document.getElementById('shapes-dropdown');

             // أغلق القوائم الأخرى
             if(shapesDropdown) shapesDropdown.classList.add('hidden');

             if (dropdown.classList.contains('hidden')) {
                 dropdown.classList.remove('hidden');
             } else {
                 dropdown.classList.add('hidden');
             }
        }

        function closeFramesDropdown() {
            const dropdown = document.getElementById('frames-dropdown');
            if(dropdown) dropdown.classList.add('hidden');
        }

        function addFrameType(type) {
            const wrapper = createWrapper('frame-layer');
            wrapper.style.borderColor = '#1e293b';
            wrapper.style.borderWidth = '3px';
            wrapper.style.backgroundColor = 'transparent';

            // تحديد الحجم بهوامش آمنة
            wrapper.style.width = '50%';
            wrapper.style.height = '50%';

            // تطبيق نوع الإطار
            if (type === 'circle') {
                 wrapper.style.borderRadius = '50%';
            } else if (type === 'rounded') {
                 // انحناء كبير كما طلب العميل
                 wrapper.style.borderRadius = '30px';
            } else {
                 wrapper.style.borderRadius = '0';
            }

            document.getElementById('card').appendChild(wrapper);
            selectEl(wrapper);
            setupInteract(wrapper, 'box');
            saveState();

            closeFramesDropdown();
        }

        // دالة قديمة، تركت للتوافق إذا تم استدعاؤها من مكان آخر
        function addFrame() {
            addFrameType('square');
        }

        function addShape() {
            // فتح/إغلاق dropdown اختيار الأشكال
            const dropdown = document.getElementById('shapes-dropdown');
            if (dropdown.classList.contains('hidden')) {
                dropdown.classList.remove('hidden');
            } else {
                dropdown.classList.add('hidden');
            }
        }

        function closeShapesDropdown() {
            const dropdown = document.getElementById('shapes-dropdown');
            dropdown.classList.add('hidden');
        }

        function addShapeType(type) {
            const wrapper = createWrapper('frame-layer');
            wrapper.style.width = '60%';
            wrapper.style.height = '60%';

            // جميع الأشكال بنفس اللون الأساسي
            wrapper.style.backgroundColor = '#6366f1';

            if (type === 'square') {
                wrapper.style.borderRadius = '2px';
            } else if (type === 'circle') {
                wrapper.style.borderRadius = '50%';
            } else if (type === 'line') {
                // خط مستقيم
                wrapper.style.width = '80%';
                wrapper.style.height = '2px';
                wrapper.style.backgroundColor = '#6366f1';
            } else if (type === 'rounded') {
                wrapper.style.borderRadius = '12px';
            }

            wrapper.style.borderWidth = '0px';
            document.getElementById('card').appendChild(wrapper);
            selectEl(wrapper);
            setupInteract(wrapper, 'box');
            saveState();
            closeShapesDropdown();
        }

        function addImageLayer(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const tempImg = new Image();
                    tempImg.src = e.target.result;
                    tempImg.onload = function() {
                        const card = document.getElementById('card');
                        const cardW = card.offsetWidth;
                        const cardH = card.offsetHeight;
                        
                        // حساب الحجم المناسب
                        const imgRatio = tempImg.width / tempImg.height;
                        const cardRatio = cardW / cardH;
                        let displayW, displayH;
                        
                        if (imgRatio > cardRatio) {
                            displayW = cardW * 0.9;
                            displayH = displayW / imgRatio;
                        } else {
                            displayH = cardH * 0.9;
                            displayW = displayH * imgRatio;
                        }
                        
                        // إنشاء طبقة صورة عادية قابلة للتحكم
                        const wrapper = createWrapper('image-layer');
                        wrapper.setAttribute('data-colorable', 'false');
                        wrapper.setAttribute('data-high-res', 'true');
                        
                        const contentWrapper = wrapper.querySelector('.content-wrapper');
                        contentWrapper.style.width = '100%';
                        contentWrapper.style.height = '100%';
                        contentWrapper.style.display = 'flex';
                        
                        const img = document.createElement('img');
                        img.crossOrigin = "anonymous";
                        img.src = e.target.result;
                        img.loading = "eager";
                        img.style.width = '100%';
                        img.style.height = '100%';
                        img.style.objectFit = 'contain';
                        img.style.pointerEvents = 'none';
                        
                        contentWrapper.appendChild(img);
                        
                        wrapper.style.width = displayW + 'px';
                        wrapper.style.height = displayH + 'px';
                        wrapper.style.left = (cardW / 2) + 'px';
                        wrapper.style.top = (cardH / 2) + 'px';
                        wrapper.style.transform = 'translate(-50%, -50%)';
                        
                        card.appendChild(wrapper);
                        
                        setTimeout(() => {
                            selectEl(wrapper);
                            setupInteract(wrapper, 'box');
                            saveState();
                        }, 50);
                    };
                };
                reader.readAsDataURL(input.files[0]);
                input.value = '';
            }
        }

        function addRegularImage(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const tempImg = new Image();
                    tempImg.src = e.target.result;
                    tempImg.onload = function() {
                        const wrapper = createWrapper('image-layer');
                        const contentWrapper = wrapper.querySelector('.content-wrapper');

                        // حساب الأبعاد المناسبة بناءً على نسبة العرض للارتفاع
                        const card = document.getElementById('card');
                        const cardRect = card.getBoundingClientRect();
                        const cardWidth = cardRect.width || card.offsetWidth;

                        // جعل العرض الافتراضي 50% من عرض الكارد (بدلاً من 60% ثابتة)
                        const targetWidth = cardWidth * 0.5;
                        const aspectRatio = tempImg.width / tempImg.height;
                        const targetHeight = targetWidth / aspectRatio;

                        wrapper.style.width = targetWidth + 'px';
                        wrapper.style.height = targetHeight + 'px';

                        contentWrapper.style.width = '100%';
                        contentWrapper.style.height = '100%';
                        contentWrapper.style.overflow = 'hidden';
                        contentWrapper.style.borderRadius = '8px';
                        contentWrapper.style.display = 'flex';

                        const img = document.createElement('img');
                        img.crossOrigin = "anonymous";
                        img.src = e.target.result;
                        img.loading = "eager";
                        img.style.width = '100%';
                        img.style.height = '100%';
                        // استخدام fill للسماح بالتشويه اليدوي إذا رغب المستخدم
                        // وبما أننا ضبطنا أبعاد الـ wrapper لتطابق الصورة، فلن تظهر مشوهة مبدئياً
                        img.style.objectFit = 'fill';
                        img.style.pointerEvents = 'none';
                        img.style.imageRendering = 'high-quality';

                        wrapper.setAttribute('data-original-image', e.target.result);
                        wrapper.setAttribute('data-colorable', 'true');

                        contentWrapper.appendChild(img);
                        document.getElementById('card').appendChild(wrapper);
                        selectEl(wrapper);
                        setupInteract(wrapper, 'box');
                        saveState();
                    };
                };
                reader.readAsDataURL(input.files[0]);
                input.value = '';
            }
        }

        function toggleEraserMode() {
            // إذا كانت الممحاة مفعلة - أوقفها
            if(eraserMode) {
                exitEraserMode();
                return;
            }
            
            // التحقق من وجود طبقة صورة محددة
            if(!activeEl || !activeEl.classList.contains("image-layer")) {
                showInfoModal("يرجى تحديد طبقة صورة أولاً لاستخدام الممحاة", "تنبيه", "🖼️");
                return;
            }
            eraserMode = true;

            if (eraserMode) {
                if (lassoMode) exitLassoMode();
                if (smartFillMode) exitSmartFillMode();
                if (typeof smartEraserMode !== 'undefined' && smartEraserMode) exitSmartEraserMode();
                magicMode = false;
                const magicControls = document.getElementById('magic-tolerance-control');
                if (magicControls) {
                    magicControls.classList.add('hidden');
                    magicControls.classList.remove('flex');
                }

                // لا نلغي التحديد - نحتاج الصورة محددة للممحاة
                const controls = document.getElementById('eraser-controls');
                controls.classList.add('active');

                document.getElementById('card').style.cursor = 'crosshair';
                initEraserCanvas();
                // Disable interaction with other layers while erasing
                document.querySelectorAll('.draggable-el').forEach(el => el.style.pointerEvents = 'none');
            } else {
                exitEraserMode();
                return;
            }
            updateToolButtons();
        }

        function toggleMagicMode() {
            magicMode = !magicMode;
            const magicControls = document.getElementById('magic-tolerance-control');
            if(magicMode) {
                document.getElementById('card').style.cursor = 'alias';
                magicControls.classList.remove('hidden');
                magicControls.classList.add('flex');
            } else {
                document.getElementById('card').style.cursor = 'crosshair';
                magicControls.classList.add('hidden');
                magicControls.classList.remove('flex');
            }
            updateToolButtons();
        }

        function exitEraserMode() {
            eraserMode = false;
            magicMode = false;

            const controls = document.getElementById('eraser-controls');
            controls.classList.remove('active');

            document.getElementById('card').style.cursor = 'default';
            if(eraserCanvas) {
                eraserCanvas.remove();
                eraserCanvas = null;
            }
            // Re-enable interaction with other layers
            document.querySelectorAll('.draggable-el').forEach(el => el.style.pointerEvents = '');
            updateToolButtons();
        }

        // --- دوال الممحاة الذكية (Smart Eraser) ---
        let smartEraserTargetEl = null; // حفظ الطبقة المستهدفة
        
        window.toggleSmartEraserMode = function() {
            const btn = document.getElementById('btn-smart-eraser');
            const btnTop = document.getElementById('btn-smart-eraser-top');
            
            // إذا كانت الممحاة مفعلة - أوقفها مباشرة بدون تحقق
            if(smartEraserMode) {
                smartEraserMode = false;
                smartEraserTargetEl = null;
                if(btn) btn.classList.remove('ring-2', 'ring-indigo-400');
                if(btnTop) btnTop.classList.remove('ring-2', 'ring-indigo-400');
                window.exitSmartEraserMode();
                updateToolButtons();
                return;
            }

            // التحقق من تحديد طبقة صورة أولاً عند التفعيل فقط
            if(!activeEl || !activeEl.classList.contains('image-layer')) {
                showInfoModal('يرجى تحديد طبقة صورة أولاً لاستخدام الممحاة الذكية', 'الممحاة الذكية', '🧹');
                return;
            }

            // حفظ الطبقة المستهدفة وتفعيل الممحاة
            smartEraserTargetEl = activeEl;
            smartEraserMode = true;
            
            if(magicMode) {
                magicMode = false;
                const mtc = document.getElementById('magic-tolerance-control');
                if(mtc) { mtc.classList.remove('flex'); mtc.classList.add('hidden'); }
            }
            if(btn) btn.classList.add('ring-2', 'ring-indigo-400');
            if(btnTop) btnTop.classList.add('ring-2', 'ring-indigo-400');
            window.initSmartEraserCanvas();
            document.getElementById('card').style.cursor = 'crosshair';
            updateToolButtons();
        }

        window.exitSmartEraserMode = function() {
            smartEraserMode = false;
            smartEraserTargetEl = null; // مسح الطبقة المحفوظة
            const btn = document.getElementById('btn-smart-eraser');
            const btnTop = document.getElementById('btn-smart-eraser-top');
            if(btn) btn.classList.remove('ring-2', 'ring-indigo-400');
            if(btnTop) btnTop.classList.remove('ring-2', 'ring-indigo-400');
            if(smartEraserCanvas) {
                smartEraserCanvas.remove();
                smartEraserCanvas = null;
            }
            if(eraserMode) {
                document.getElementById('card').style.cursor = 'crosshair';
            } else {
                document.getElementById('card').style.cursor = 'default';
            }
        }

        window.initSmartEraserCanvas = function() {
            if(smartEraserCanvas) smartEraserCanvas.remove();
            const card = document.getElementById('card');
            smartEraserCanvas = document.createElement('canvas');
            smartEraserCanvas.width = card.offsetWidth;
            smartEraserCanvas.height = card.offsetHeight;
            smartEraserCanvas.style.cssText = 'position:absolute;top:0;left:0;cursor:crosshair;z-index:550;';
            const ctx = smartEraserCanvas.getContext('2d');
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#6366f1';
            ctx.setLineDash([5, 5]);
            let isDrawing = false;
            let canDraw = true;
            let points = [];
            let drawStartTime = 0;

            function getPos(e) {
                const rect = smartEraserCanvas.getBoundingClientRect();
                const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
                const y = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
                return {x: x * (smartEraserCanvas.width / rect.width), y: y * (smartEraserCanvas.height / rect.height)};
            }

            function start(e) {
                isDrawing = true;
                drawStartTime = Date.now();
                points = [getPos(e)];
            }

            function move(e) {
                if(!isDrawing) return;
                e.preventDefault();
                points.push(getPos(e));
                ctx.clearRect(0, 0, smartEraserCanvas.width, smartEraserCanvas.height);
                // رسم دائرة البداية
                ctx.save();
                ctx.setLineDash([]);
                ctx.beginPath();
                ctx.arc(points[0].x, points[0].y, 8, 0, Math.PI * 2);
                ctx.fillStyle = "rgba(99, 102, 241, 0.5)";
                ctx.fill();
                ctx.strokeStyle = "#6366f1";
                ctx.lineWidth = 2;
                ctx.stroke();
                ctx.restore();
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(points[0].x, points[0].y);
                for(let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
                ctx.stroke();
                ctx.fillStyle = 'rgba(99, 102, 241, 0.15)';
                ctx.fill();
            }

            function end(e) {
                if(!isDrawing) return;
                e.preventDefault();
                isDrawing = false;
                
                const drawDuration = Date.now() - drawStartTime;
                if (drawDuration < 200 && points.length < 5) {
                    ctx.clearRect(0, 0, smartEraserCanvas.width, smartEraserCanvas.height);
                    points = [];
                    showSmartToolTutorial('smartEraser');
                    isDrawing = false;
                    return;
                }
                
                performSmartEraser(points);
                ctx.clearRect(0, 0, smartEraserCanvas.width, smartEraserCanvas.height);
                points = [];
            }

            smartEraserCanvas.addEventListener('mousedown', start);
            smartEraserCanvas.addEventListener('mousemove', move);
            smartEraserCanvas.addEventListener('mouseup', end);
            smartEraserCanvas.addEventListener('touchstart', start, {passive: false});
            smartEraserCanvas.addEventListener('touchmove', move, {passive: false});
            smartEraserCanvas.addEventListener('touchend', end);
            card.appendChild(smartEraserCanvas);
        }

        window.performSmartEraser = function(points) {
            if(points.length < 3) return;
            const card = document.getElementById('card');
            const cardRect = card.getBoundingClientRect();

            // استخدام الطبقة المحفوظة أو المحددة حالياً
            let targetEl = smartEraserTargetEl || activeEl;

            // إذا لم يكن محدداً، ابحث تحت نقطة البداية
            if(!targetEl || !targetEl.classList.contains('image-layer')) {
                const images = Array.from(card.querySelectorAll('.image-layer')).reverse();
                for(let img of images) {
                    const r = img.getBoundingClientRect();
                    const l = r.left - cardRect.left;
                    const t = r.top - cardRect.top;
                    if(points[0].x >= l && points[0].x <= l + r.width && points[0].y >= t && points[0].y <= t + r.height) {
                        targetEl = img;
                        break;
                    }
                }
            }

            if(!targetEl) return;
            const sourceImg = targetEl.querySelector('img');
            if(!sourceImg) return;

                        const imgLeft = targetEl.offsetLeft;
            const imgTop = targetEl.offsetTop;
            const imgWidth = targetEl.offsetWidth;
            const imgHeight = targetEl.offsetHeight;

            const naturalWidth = sourceImg.naturalWidth || imgWidth;
            const naturalHeight = sourceImg.naturalHeight || imgHeight;
            const ratioX = naturalWidth / imgWidth;
            const ratioY = naturalHeight / imgHeight;

            const cornerX = imgLeft - (imgWidth / 2);
            const cornerY = imgTop - (imgHeight / 2);

            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = naturalWidth;
            tempCanvas.height = naturalHeight;
            const tCtx = tempCanvas.getContext('2d');

            tCtx.drawImage(sourceImg, 0, 0, naturalWidth, naturalHeight);
            tCtx.globalCompositeOperation = 'destination-out';
            tCtx.beginPath();

            for(let i=0; i<points.length; i++) {
                const px = (points[i].x - cornerX) * ratioX;
                const py = (points[i].y - cornerY) * ratioY;
                if(i===0) tCtx.moveTo(px, py);
                else tCtx.lineTo(px, py);
            }
            tCtx.closePath();
            tCtx.fill();
            const newSrc = tempCanvas.toDataURL('image/png');
            sourceImg.src = newSrc;
            
            // تحديث الـ mask إذا كان هناك تدرج أو تلوين على الصورة
            const contentWrapper = targetEl.querySelector('.image-content-wrapper') || targetEl.querySelector('.content-wrapper');
            if(contentWrapper && (targetEl.hasAttribute('data-has-gradient') || targetEl.hasAttribute('data-has-color'))) {
                contentWrapper.style.webkitMaskImage = 'url(' + newSrc + ')';
                contentWrapper.style.maskImage = 'url(' + newSrc + ')';
            }
            
            saveState();
            // إنهاء الممحاة الذكية تلقائياً بعد المسح
            window.exitSmartEraserMode();
        }

        // --- دوال القص الذكي (Lasso) ---
        function toggleLassoMode() {
            // إذا كان القص مفعل - أوقفه
            if(lassoMode) {
                exitLassoMode();
                return;
            }
            
            // التحقق من وجود طبقة صورة محددة
            if(!activeEl || !activeEl.classList.contains('image-layer')) {
                showInfoModal('يرجى تحديد طبقة صورة أولاً للقص منها', 'القص الذكي', '✂️');
                return;
            }
            
            // حفظ الطبقة المستهدفة قبل أي تغيير
            lassoTargetEl = activeEl;
            lassoMode = true;

            if (lassoMode) {
                if (eraserMode) exitEraserMode();

                magicMode = false;
                document.getElementById('card').style.cursor = 'crosshair';
                initLassoCanvas();
            } else {
                exitLassoMode();
            }
            updateToolButtons();
        }

        function updateToolButtons() {
            const eraserBtn = document.getElementById('btn-eraser');
            const lassoBtn = document.getElementById('btn-lasso');
            const magicBtn = document.getElementById('btn-magic');
            const smartEraserBtn = document.getElementById('btn-smart-eraser');
            const smartEraserTopBtn = document.getElementById('btn-smart-eraser-top');
            const smartFillBtn = document.getElementById('btn-smart-fill');
            
            // قائمة بجميع الأزرار لإعادة تعيينها
            const allButtons = [eraserBtn, lassoBtn, magicBtn, smartEraserBtn, smartEraserTopBtn, smartFillBtn];

            allButtons.forEach(btn => {
                if(btn) {
                    btn.classList.remove('bg-[#6366f1]', 'text-white');
                    // إزالة ألوان الخلفية الفاتحة المستخدمة سابقاً
                    btn.classList.remove('bg-white'); 
                    // إعادة تعيين إلى الوضع الافتراضي الموحد
                    btn.classList.add('bg-[#f8fafc]', 'text-[#1e293b]'); 
                }
            });

            // دالة مساعدة لتفعيل الزر بلون موحد (أزرق ونص أبيض)
            const activate = (btn) => {
                if(btn) {
                    btn.classList.remove('bg-[#f8fafc]', 'text-[#1e293b]');
                    btn.classList.remove('bg-white');
                    btn.classList.add('bg-[#6366f1]', 'text-white');
                }
            };
            
            if(eraserMode) activate(eraserBtn);
            if(lassoMode) activate(lassoBtn);
            if(smartFillMode) activate(smartFillBtn);
            if(smartEraserMode) activate(smartEraserTopBtn);

            // الأزرار الفرعية (تظهر نشطة أيضاً إذا كان الوضع مفعلاً)
            if(magicMode && eraserMode) activate(magicBtn);
            if(smartEraserMode && eraserMode) activate(smartEraserBtn);
        }
        function initLassoCanvas() {
            if(lassoCanvas) lassoCanvas.remove();
            const card = document.getElementById('card');

            lassoCanvas = document.createElement('canvas');
            lassoCanvas.width = card.offsetWidth;
            lassoCanvas.height = card.offsetHeight;
            lassoCanvas.style.position = 'absolute';
            lassoCanvas.style.top = '0';
            lassoCanvas.style.left = '0';
            lassoCanvas.style.cursor = 'crosshair';
            lassoCanvas.style.zIndex = '500';

            const ctx = lassoCanvas.getContext('2d');
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#6366f1';
            ctx.setLineDash([5, 5]);

            let isDrawing = false;
            let canDraw = true;
            let points = [];
            let drawStartTime = 0;

            function getMousePos(e) {
                const rect = lassoCanvas.getBoundingClientRect();
                const scaleX = lassoCanvas.width / rect.width;
                const scaleY = lassoCanvas.height / rect.height;

                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;

                return {
                    x: (clientX - rect.left) * scaleX,
                    y: (clientY - rect.top) * scaleY
                };
            }

            function startDraw(e) {
                if(!canDraw) return;
                isDrawing = true;
                points = [];
                drawStartTime = Date.now();
                const pos = getMousePos(e);
                points.push(pos);
                ctx.beginPath();
                ctx.moveTo(pos.x, pos.y);
            }

            function draw(e) {
                if(!isDrawing) return;
                e.preventDefault();
                const pos = getMousePos(e);
                points.push(pos);
                ctx.lineTo(pos.x, pos.y);
                ctx.clearRect(0, 0, lassoCanvas.width, lassoCanvas.height);

                ctx.beginPath();
                if(points.length > 0) {
                    ctx.moveTo(points[0].x, points[0].y);
                    for(let i=1; i<points.length; i++) ctx.lineTo(points[i].x, points[i].y);
                }
                ctx.stroke();
            }

            function endDraw(e) {
                if(!canDraw || !isDrawing) return;
                e.preventDefault();
                e.stopPropagation();
                isDrawing = false;
                
                const drawDuration = Date.now() - drawStartTime;
                if (drawDuration < 200 && points.length < 5) {
                    ctx.clearRect(0, 0, lassoCanvas.width, lassoCanvas.height);
                    points = [];
                    showSmartToolTutorial('lasso');
                    isDrawing = false;
                    return;
                }
                
                ctx.closePath();
                ctx.stroke();
                performLassoCut(points);
                exitLassoMode();
            }

            lassoCanvas.addEventListener('mousedown', startDraw);
            lassoCanvas.addEventListener('mousemove', draw);
            lassoCanvas.addEventListener('mouseup', endDraw);

            lassoCanvas.addEventListener('touchstart', startDraw, {passive: false});
            lassoCanvas.addEventListener('touchmove', draw, {passive: false});
            lassoCanvas.addEventListener('touchend', endDraw);

            card.appendChild(lassoCanvas);
        }

        function performLassoCut(points) {
            // استخدام الطبقة المحفوظة أو المحددة حالياً
            const targetEl = lassoTargetEl || activeEl;
            if(!targetEl || points.length < 3) return;
            const sourceImg = targetEl.querySelector('img');
            if(!sourceImg) return;

            const oldEl = targetEl;
            const imgLeft = targetEl.offsetLeft;
            const imgTop = targetEl.offsetTop;
            const imgWidth = targetEl.offsetWidth;
            const imgHeight = targetEl.offsetHeight;

            const naturalWidth = sourceImg.naturalWidth || imgWidth;
            const naturalHeight = sourceImg.naturalHeight || imgHeight;
            const ratioX = naturalWidth / imgWidth;
            const ratioY = naturalHeight / imgHeight;

            const cornerX = imgLeft - (imgWidth / 2);
            const cornerY = imgTop - (imgHeight / 2);

            // حساب الـ bounding box للنقاط المقصوصة
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            for(let i = 0; i < points.length; i++) {
                const px = (points[i].x - cornerX) * ratioX;
                const py = (points[i].y - cornerY) * ratioY;
                if(px < minX) minX = px;
                if(py < minY) minY = py;
                if(px > maxX) maxX = px;
                if(py > maxY) maxY = py;
            }

            const croppedWidth = Math.max(1, maxX - minX);
            const croppedHeight = Math.max(1, maxY - minY);

            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = croppedWidth;
            tempCanvas.height = croppedHeight;
            const tCtx = tempCanvas.getContext('2d');

            tCtx.beginPath();
            const startX = (points[0].x - cornerX) * ratioX - minX;
            const startY = (points[0].y - cornerY) * ratioY - minY;

            tCtx.moveTo(startX, startY);
            for(let i=1; i<points.length; i++) {
                const px = (points[i].x - cornerX) * ratioX - minX;
                const py = (points[i].y - cornerY) * ratioY - minY;
                tCtx.lineTo(px, py);
            }
            tCtx.closePath();
            tCtx.clip();
            tCtx.drawImage(sourceImg, -minX, -minY, naturalWidth, naturalHeight);

            const newDataUrl = tempCanvas.toDataURL('image/png');

            const wrapper = createWrapper('image-layer');
            const contentWrapper = wrapper.querySelector('.content-wrapper');

            // استخدم حجم الـ canvas الحقيقي بدلاً من حساب نسبي
            const displayWidth = croppedWidth / ratioX;
            const displayHeight = croppedHeight / ratioY;

            wrapper.style.width = displayWidth + 'px';
            wrapper.style.height = displayHeight + 'px';
            wrapper.style.left = (imgLeft - imgWidth / 2 + minX / ratioX + displayWidth / 2) + 'px';
            wrapper.style.top = (imgTop - imgHeight / 2 + minY / ratioY + displayHeight / 2) + 'px';
            wrapper.style.transform = 'translate(-50%, -50%)';

            contentWrapper.style.width = '100%';
            contentWrapper.style.height = '100%';
            contentWrapper.style.display = 'flex';

            const newImg = document.createElement('img');
            newImg.src = newDataUrl;
            newImg.style.width = '100%';
            newImg.style.height = '100%';
            newImg.style.objectFit = 'contain';
            newImg.style.pointerEvents = 'none';

            contentWrapper.appendChild(newImg);
            document.getElementById('card').appendChild(wrapper);

            if(oldEl) oldEl.classList.remove('selected');

            setTimeout(() => {
                selectEl(wrapper);
                setupInteract(wrapper, 'box');
                saveState();
            }, 50);
        }

        function exitLassoMode() {
            lassoMode = false;
            lassoTargetEl = null; // مسح الطبقة المستهدفة
            if(updateToolButtons) updateToolButtons();
            document.getElementById('card').style.cursor = 'default';
            if(lassoCanvas) {
                lassoCanvas.remove();
                lassoCanvas = null;
            }
        }


        // --- دوال التلوين الذكي (Smart Fill) ---
        function toggleSmartFillMode() {
            smartFillMode = !smartFillMode;
            if (smartFillMode) {
                if (eraserMode) exitEraserMode();
                if (lassoMode) exitLassoMode();
                magicMode = false;
                document.getElementById('card').style.cursor = 'crosshair';
                initSmartFillCanvas();
            } else {
                exitSmartFillMode();
            }
            updateToolButtons();
        }

        function initSmartFillCanvas() {
            if(smartFillCanvas) smartFillCanvas.remove();
            const card = document.getElementById('card');
            smartFillCanvas = document.createElement('canvas');
            smartFillCanvas.width = card.offsetWidth;
            smartFillCanvas.height = card.offsetHeight;
            smartFillCanvas.style.position = 'absolute';
            smartFillCanvas.style.top = '0';
            smartFillCanvas.style.left = '0';
            smartFillCanvas.style.cursor = 'crosshair';
            smartFillCanvas.style.zIndex = '500';
            const ctx = smartFillCanvas.getContext('2d');
            ctx.lineWidth = 2;
            ctx.strokeStyle = smartFillColor;
            ctx.setLineDash([5, 5]);
            let isDrawing = false;
            let canDraw = true;
            let points = [];
            let drawStartTime = 0;
            function getMousePos(e) {
                const rect = smartFillCanvas.getBoundingClientRect();
                const scaleX = smartFillCanvas.width / rect.width;
                const scaleY = smartFillCanvas.height / rect.height;
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                return { x: (clientX - rect.left) * scaleX, y: (clientY - rect.top) * scaleY };
            }
            function startDraw(e) {
                if(!canDraw) return;
                isDrawing = true;
                points = [];
                drawStartTime = Date.now();
                const pos = getMousePos(e);
                points.push(pos);
                ctx.beginPath();
                ctx.moveTo(pos.x, pos.y);
            }
            function draw(e) {
                if(!isDrawing) return;
                e.preventDefault();
                const pos = getMousePos(e);
                points.push(pos);
                ctx.lineTo(pos.x, pos.y);
                ctx.clearRect(0, 0, smartFillCanvas.width, smartFillCanvas.height);
                ctx.beginPath();
                if(points.length > 0) {
                    ctx.moveTo(points[0].x, points[0].y);
                    for(let i=1; i<points.length; i++) ctx.lineTo(points[i].x, points[i].y);
                }
                ctx.stroke();
            }
            function endDraw(e) {
                if(!canDraw || !isDrawing) return;
                e.preventDefault();
                isDrawing = false;
                
                const drawDuration = Date.now() - drawStartTime;
                if (drawDuration < 200 && points.length < 5) {
                    ctx.clearRect(0, 0, smartFillCanvas.width, smartFillCanvas.height);
                    points = [];
                    showSmartToolTutorial('smartFill');
                    isDrawing = false;
                    return;
                }
                
                ctx.closePath();
                ctx.stroke();
                performSmartFill(points);
                exitSmartFillMode();
            }
            smartFillCanvas.addEventListener('mousedown', startDraw);
            smartFillCanvas.addEventListener('mousemove', draw);
            smartFillCanvas.addEventListener('mouseup', endDraw);
            smartFillCanvas.addEventListener('touchstart', startDraw, {passive: false});
            smartFillCanvas.addEventListener('touchmove', draw, {passive: false});
            smartFillCanvas.addEventListener('touchend', endDraw);
            card.appendChild(smartFillCanvas);
        }
        function performSmartFill(points) {
            if(points.length < 3) return;
            const card = document.getElementById('card');
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            for(let i = 0; i < points.length; i++) {
                if(points[i].x < minX) minX = points[i].x;
                if(points[i].y < minY) minY = points[i].y;
                if(points[i].x > maxX) maxX = points[i].x;
                if(points[i].y > maxY) maxY = points[i].y;
            }
            const shapeWidth = Math.max(1, maxX - minX);
            const shapeHeight = Math.max(1, maxY - minY);
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = shapeWidth;
            tempCanvas.height = shapeHeight;
            const tCtx = tempCanvas.getContext('2d');
            tCtx.beginPath();
            tCtx.moveTo(points[0].x - minX, points[0].y - minY);
            for(let i=1; i<points.length; i++) {
                tCtx.lineTo(points[i].x - minX, points[i].y - minY);
            }
            tCtx.closePath();
            tCtx.fillStyle = smartFillColor;
            tCtx.fill();
            const newDataUrl = tempCanvas.toDataURL('image/png');
            const wrapper = createWrapper('image-layer');
            const contentWrapper = wrapper.querySelector('.content-wrapper');
            wrapper.style.width = shapeWidth + 'px';
            wrapper.style.height = shapeHeight + 'px';
            wrapper.style.left = (minX + shapeWidth / 2) + 'px';
            wrapper.style.top = (minY + shapeHeight / 2) + 'px';
            wrapper.style.transform = 'translate(-50%, -50%)';
            contentWrapper.style.width = '100%';
            contentWrapper.style.height = '100%';
            contentWrapper.style.display = 'flex';
            const newImg = document.createElement('img');
            newImg.src = newDataUrl;
            newImg.style.width = '100%';
            newImg.style.height = '100%';
            newImg.style.objectFit = 'contain';
            newImg.style.pointerEvents = 'none';
            contentWrapper.appendChild(newImg);
            card.appendChild(wrapper);
            setTimeout(() => {
                selectEl(wrapper);
                setupInteract(wrapper, 'box');
                saveState();
            }, 50);
        }
        function exitSmartFillMode() {
            smartFillMode = false;
            updateToolButtons();
            document.getElementById('card').style.cursor = 'default';
            if(smartFillCanvas) {
                smartFillCanvas.remove();
                smartFillCanvas = null;
            }
        }
        function setSmartFillColor(color) {
            smartFillColor = color;
        }
        // --- Crop Tool Functions ---
        function toggleCropMode() {
            cropMode = !cropMode;
            const cropBtn = document.getElementById('btn-crop');

            if (cropMode) {
                // Disable other modes
                if (eraserMode) exitEraserMode();
                if (lassoMode) exitLassoMode();

                // Show crop overlay
                const overlay = document.getElementById('crop-overlay');
                overlay.classList.remove('hidden');

                // Initialize crop area
                const card = document.getElementById('card');
                const cardRect = card.getBoundingClientRect();
                const cardParentRect = document.getElementById('card-wrapper').getBoundingClientRect();

                // Set initial crop area (80% of card)
                const w = card.offsetWidth * 0.8;
                const h = card.offsetHeight * 0.8;
                const x = (card.offsetWidth - w) / 2;
                const y = (card.offsetHeight - h) / 2;

                const cropArea = document.getElementById('crop-area');
                cropArea.style.left = x + 'px';
                cropArea.style.top = y + 'px';
                cropArea.style.width = w + 'px';
                cropArea.style.height = h + 'px';

                cropStartX = x;
                cropStartY = y;
                cropStartWidth = w;
                cropStartHeight = h;

                // Attach event listeners
                attachCropEventListeners();

                // Update button style
                cropBtn.classList.add('bg-[#6366f1]', 'text-white');
                cropBtn.classList.remove('bg-[#f1f5f9]', 'text-[#475569]');
            } else {
                exitCropMode();
            }
        }

        function attachCropEventListeners() {
            const cropArea = document.getElementById('crop-area');
            const handles = ['tl', 'tr', 'bl', 'br', 't', 'b', 'l', 'r'];
            const card = document.getElementById('card');

            // Make crop area draggable
            cropArea.addEventListener('mousedown', startDragCrop);
            cropArea.addEventListener('touchstart', startDragCrop, { passive: false });

            // Make handles draggable
            handles.forEach(handle => {
                const el = document.getElementById('crop-handle-' + handle);
                el.addEventListener('mousedown', (e) => startResizeCrop(e, handle));
                el.addEventListener('touchstart', (e) => startResizeCrop(e, handle), { passive: false });
            });

            function startDragCrop(e) {
                if (handles.some(h => e.target.id === 'crop-handle-' + h)) return; // Don't drag from handles
                isDraggingCrop = true;
                cropInitialX = e.touches ? e.touches[0].clientX : e.clientX;
                cropInitialY = e.touches ? e.touches[0].clientY : e.clientY;
                cropStartX = parseFloat(cropArea.style.left);
                cropStartY = parseFloat(cropArea.style.top);

                document.addEventListener('mousemove', dragCrop);
                document.addEventListener('touchmove', dragCrop, { passive: false });
                document.addEventListener('mouseup', stopDragCrop);
                document.addEventListener('touchend', stopDragCrop);
            }

            function dragCrop(e) {
                if (!isDraggingCrop) return;
                e.preventDefault();

                // حساب Scale لضمان دقة السحب مع التكبير
                const zoomFactor = (window.currentZoom || 100) / 100;

                const currentX = e.touches ? e.touches[0].clientX : e.clientX;
                const currentY = e.touches ? e.touches[0].clientY : e.clientY;

                // نقسم الفرق على معامل التكبير لتحويل حركة الماوس (بكسل شاشة) إلى وحدات محلية
                const deltaX = (currentX - cropInitialX) / zoomFactor;
                const deltaY = (currentY - cropInitialY) / zoomFactor;

                let newX = cropStartX + deltaX;
                let newY = cropStartY + deltaY;

                // Keep within bounds
                newX = Math.max(0, Math.min(newX, card.offsetWidth - cropArea.offsetWidth));
                newY = Math.max(0, Math.min(newY, card.offsetHeight - cropArea.offsetHeight));

                cropArea.style.left = newX + 'px';
                cropArea.style.top = newY + 'px';
                updateCropOverlay();
            }

            function stopDragCrop() {
                isDraggingCrop = false;
                document.removeEventListener('mousemove', dragCrop);
                document.removeEventListener('touchmove', dragCrop);
                document.removeEventListener('mouseup', stopDragCrop);
                document.removeEventListener('touchend', stopDragCrop);
            }

            function startResizeCrop(e, handle) {
                e.preventDefault();
                e.stopPropagation();
                draggedHandle = handle;
                cropInitialX = e.touches ? e.touches[0].clientX : e.clientX;
                cropInitialY = e.touches ? e.touches[0].clientY : e.clientY;
                cropStartX = parseFloat(cropArea.style.left);
                cropStartY = parseFloat(cropArea.style.top);
                cropStartWidth = cropArea.offsetWidth;
                cropStartHeight = cropArea.offsetHeight;

                document.addEventListener('mousemove', resizeCrop);
                document.addEventListener('touchmove', resizeCrop, { passive: false });
                document.addEventListener('mouseup', stopResizeCrop);
                document.addEventListener('touchend', stopResizeCrop);
            }

            function resizeCrop(e) {
                if (!draggedHandle) return;
                e.preventDefault();

                // حساب Scale لضمان دقة التحجيم مع التكبير
                const zoomFactor = (window.currentZoom || 100) / 100;

                const currentX = e.touches ? e.touches[0].clientX : e.clientX;
                const currentY = e.touches ? e.touches[0].clientY : e.clientY;

                // تصحيح الحركة بناء على الزووم
                const deltaX = (currentX - cropInitialX) / zoomFactor;
                const deltaY = (currentY - cropInitialY) / zoomFactor;

                let newX = cropStartX;
                let newY = cropStartY;
                let newW = cropStartWidth;
                let newH = cropStartHeight;

                // Handle different corner/edge resizes
                if (draggedHandle.includes('l')) {
                    newX = Math.max(0, cropStartX + deltaX);
                    newW = cropStartWidth - (newX - cropStartX);
                }
                if (draggedHandle.includes('r')) {
                    newW = Math.max(20, cropStartWidth + deltaX);
                }
                if (draggedHandle.includes('t')) {
                    newY = Math.max(0, cropStartY + deltaY);
                    newH = cropStartHeight - (newY - cropStartY);
                }
                if (draggedHandle.includes('b')) {
                    newH = Math.max(20, cropStartHeight + deltaY);
                }

                // Keep within bounds
                newW = Math.min(newW, card.offsetWidth - newX);
                newH = Math.min(newH, card.offsetHeight - newY);

                cropArea.style.left = newX + 'px';
                cropArea.style.top = newY + 'px';
                cropArea.style.width = newW + 'px';
                cropArea.style.height = newH + 'px';
                updateCropOverlay();
            }

            function stopResizeCrop() {
                draggedHandle = null;
                document.removeEventListener('mousemove', resizeCrop);
                document.removeEventListener('touchmove', resizeCrop);
                document.removeEventListener('mouseup', stopResizeCrop);
                document.removeEventListener('touchend', stopResizeCrop);
            }
        }

        function updateCropOverlay() {
            const cropArea = document.getElementById('crop-area');
            const cropOverlay = document.getElementById('crop-overlay');
            const card = document.getElementById('card');

            // Update dimensions display (optional - for visual feedback)
            const x = parseFloat(cropArea.style.left);
            const y = parseFloat(cropArea.style.top);
            const w = cropArea.offsetWidth;
            const h = cropArea.offsetHeight;

            // Store for applying later
            cropArea.dataset.x = x;
            cropArea.dataset.y = y;
            cropArea.dataset.w = w;
            cropArea.dataset.h = h;
        }

        // Format number with thousand separators
        function formatNumberWithSeparators(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }

        function applyCrop() {
            const cropArea = document.getElementById('crop-area');
            const card = document.getElementById('card');

            const x = parseFloat(cropArea.style.left);
            const y = parseFloat(cropArea.style.top);
            const w = cropArea.offsetWidth;
            const h = cropArea.offsetHeight;

            // Save current state
            saveState();

            // First: Snapshot element dimensions to pixels to prevent distortion
            const allElements = Array.from(card.querySelectorAll('.draggable-el'));

            allElements.forEach(el => {
                // Get current logical size in pixels
                const currentW = el.offsetWidth;
                const currentH = el.offsetHeight;

                // Freeze dimensions with !important to override CSS classes like .bg-image
                el.style.cssText += `width: ${currentW}px !important; height: ${currentH}px !important;`;

                // If it was a bg-image, it is no longer distinct from a normal image in terms of sizing
                // We should also remove the class that forces position to 0,0 if we want it to move
                if (el.classList.contains('bg-image')) {
                    el.classList.remove('bg-image');
                    el.classList.add('image-layer'); // Ensure it keeps base styling

                    // We need to set its position explicitly because removing bg-image might reset it
                    // bg-image forced left:0, top:0.
                    // We want it to stay visually where it is (0,0 relative to OLD card).
                    el.style.left = '0px';
                    el.style.top = '0px';
                    // Reset transform because bg-image usually has none, but we might have added some
                    el.style.transform = 'none';
                }
            });

            // Second: Adjust all elements positions relative to crop area BEFORE changing card size
            const elementsToKeep = [];

            allElements.forEach(el => {
                // Use offsetLeft/Top which are in logical (unzoomed) pixels relative to the card
                // This fixes the issue where zoom level caused incorrect position calculations
                // NOTE: 'offsetLeft' returns the visual Left edge only if there's no transform shifting it.
                // Our elements have "transform: translate(-50%, -50%)" usually.
                // IF element has that transform, offsetLeft is roughly the Center X position.
                // IF element is bg-image (transform: none), offsetLeft is Left Edge.

                const hasCenterTransform = el.style.transform.includes('translate(-50%') ||
                                          getComputedStyle(el).transform !== 'none' && el.style.transform.includes('-50%');

                // We need the VISUAL bounding box relative to the card, in unzoomed CSS pixels.
                // Standard offsetLeft/Top logic:
                let visualX, visualY, visualW, visualH;

                // For bg-image (full width/height, no transform)
                if (el.classList.contains('bg-image')) {
                     visualX = 0;
                     visualY = 0;
                     visualW = card.offsetWidth;
                     visualH = card.offsetHeight;
                } else {
                    // Start with offset positions (usually center if transformed)
                    let baseX = el.offsetLeft;
                    let baseY = el.offsetTop;
                    const wEl = el.offsetWidth;
                    const hEl = el.offsetHeight;

                    if (hasCenterTransform) {
                        visualX = baseX - (wEl / 2);
                        visualY = baseY - (hEl / 2);
                    } else {
                        visualX = baseX;
                        visualY = baseY;
                    }
                    visualW = wEl;
                    visualH = hEl;
                }

                // Intersection Check (AABB)
                // Crop Box: x, y, w, h

                // Allow keeping if ANY part overlaps? Or mostly inside?
                // Let's use Overlap.
                const overlaps = (visualX < x + w) && (visualX + visualW > x) &&
                                 (visualY < y + h) && (visualY + visualH > y);

                if (overlaps) {

                    // Adjust position to new coordinate system
                    // New Card 0,0 corresponds to Old Card x,y

                    // If element was centered at (cx, cy) in old card.
                    // It should be centered at (cx - x, cy - y) in new card.

                    // IF element relies on Left/Top as Center:
                    if (hasCenterTransform) {
                         const currentLeft = el.offsetLeft; // Center X in old
                         const currentTop = el.offsetTop;   // Center Y in old

                         const newLeft = currentLeft - x;
                         const newTop = currentTop - y;

                         el.style.left = newLeft + 'px';
                         el.style.top = newTop + 'px';
                    }
                    else if (el.classList.contains('bg-image')) {
                        // Background image special case:
                        // It covers the whole old card.
                        // We want it to cover the new card (cropped view).
                        // BUT bg-image usually has "width: 100%, height: 100%".
                        // If we just leave it, it will shrink to fit the new small card (distorted or just cropped automatically).
                        // User expects "Crop" to act like a window.
                        // So we should probably convert it to a regular image OR adjust object-position?

                        // If it's an <img> inside a div.
                        // If we want to maintain the specific visual crop:
                        // The easiest way for bg-image is to let it fail/reset since it's "Background".
                        // OR, if the user cropped the canvas, valid "bg-image" concepts implies it resizes.
                        // BUT "Lasso/Crop studio" implies cutting the image.

                        // Let's assume typical elements for now.
                        // If it's bg-image, it auto-resizes.
                    }
                    else {
                        // Standard positioning (Left/Top corner)
                        const currentLeft = el.offsetLeft;
                        const currentTop = el.offsetTop;

                        const newLeft = currentLeft - x;
                        const newTop = currentTop - y;

                        el.style.left = newLeft + 'px';
                        el.style.top = newTop + 'px';
                    }

                    elementsToKeep.push(el);
                }
            });

            // Remove elements that are outside crop area
            allElements.forEach(el => {
                if (!elementsToKeep.includes(el)) {
                    el.remove();
                }
            });

            // Update card dimensions using DPI_RATIO
            const customWidth = document.getElementById('custom-width');
            const customHeight = document.getElementById('custom-height');

            // تحويل البكسل إلى سنتيمتر (DPI_RATIO هو بكسل لكل سم، وليس بكسل لكل إنش)
            // DPI_RATIO = 118.11 px/cm
            const newWidthMM = w / DPI_RATIO;
            const newHeightMM = h / DPI_RATIO;

            customWidth.value = newWidthMM.toFixed(2);
            customHeight.value = newHeightMM.toFixed(2);

            // Apply new card size
            setCardSize(w, h);

            // Also adjust gradient overlay if exists
            const gradientOverlay = document.getElementById('card-gradient');
            if (gradientOverlay) {
                gradientOverlay.style.width = w + 'px';
                gradientOverlay.style.height = h + 'px';
            }

            exitCropMode();
            saveState();
        }

        function exitCropMode() {
            cropMode = false;
            const cropBtn = document.getElementById('btn-crop');
            cropBtn.classList.remove('bg-[#6366f1]', 'text-white');
            cropBtn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');

            const overlay = document.getElementById('crop-overlay');
            overlay.classList.add('hidden');

            document.getElementById('card').style.cursor = 'default';
        }

        // --- Hand Tool Functions ---
        function toggleHandMode() {
            handMode = !handMode;
            const handBtn = document.getElementById('btn-hand');
            const previewArea = document.querySelector('.preview-area');

            if (handMode) {
                // Disable other modes
                if (eraserMode) exitEraserMode();
                if (lassoMode) exitLassoMode();
                if (cropMode) exitCropMode();

                // Update button style
                handBtn.classList.add('bg-[#6366f1]', 'text-white');
                handBtn.classList.remove('bg-[#f1f5f9]', 'text-[#475569]');

                // Change cursor
                previewArea.style.cursor = 'grab';

                // Add event listeners
                previewArea.addEventListener('mousedown', startHandDrag);
                previewArea.addEventListener('touchstart', startHandDrag, { passive: false });
            } else {
                exitHandMode();
            }
        }

        function startHandDrag(e) {
            if (!handMode) return;

            // Don't activate if clicking on elements inside card
            if (e.target.closest('.draggable-el')) return;

            e.preventDefault();
            isHandDragging = true;

            const previewArea = document.querySelector('.preview-area');
            previewArea.style.cursor = 'grabbing';

            handStartX = e.touches ? e.touches[0].clientX : e.clientX;
            handStartY = e.touches ? e.touches[0].clientY : e.clientY;
            handScrollLeft = previewArea.scrollLeft;
            handScrollTop = previewArea.scrollTop;

            document.addEventListener('mousemove', doHandDrag);
            document.addEventListener('touchmove', doHandDrag, { passive: false });
            document.addEventListener('mouseup', stopHandDrag);
            document.addEventListener('touchend', stopHandDrag);
        }

        function doHandDrag(e) {
            if (!isHandDragging) return;
            e.preventDefault();

            const previewArea = document.querySelector('.preview-area');
            const currentX = e.touches ? e.touches[0].clientX : e.clientX;
            const currentY = e.touches ? e.touches[0].clientY : e.clientY;

            const deltaX = currentX - handStartX;
            const deltaY = currentY - handStartY;

            previewArea.scrollLeft = handScrollLeft - deltaX;
            previewArea.scrollTop = handScrollTop - deltaY;
        }

        function stopHandDrag() {
            isHandDragging = false;

            const previewArea = document.querySelector('.preview-area');
            if (handMode) {
                previewArea.style.cursor = 'grab';
            }

            document.removeEventListener('mousemove', doHandDrag);
            document.removeEventListener('touchmove', doHandDrag);
            document.removeEventListener('mouseup', stopHandDrag);
            document.removeEventListener('touchend', stopHandDrag);
        }

        function exitHandMode() {
            handMode = false;
            isHandDragging = false;

            const handBtn = document.getElementById('btn-hand');
            if (handBtn) {
                handBtn.classList.remove('bg-[#6366f1]', 'text-white');
                handBtn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
            }

            const previewArea = document.querySelector('.preview-area');
            previewArea.style.cursor = 'default';

            // Remove event listeners
            previewArea.removeEventListener('mousedown', startHandDrag);
            previewArea.removeEventListener('touchstart', startHandDrag);
        }

        function initEraserCanvas() {
            const card = document.getElementById('card');
            if(eraserCanvas) eraserCanvas.remove();
            eraserCanvas = document.createElement('canvas');
            eraserCanvas.width = card.offsetWidth;
            eraserCanvas.height = card.offsetHeight;
            eraserCanvas.style.position = 'absolute';
            eraserCanvas.style.top = '0';
            eraserCanvas.style.left = '0';
            eraserCanvas.style.cursor = 'crosshair';
            eraserCanvas.style.zIndex = '200';
            const ctx = eraserCanvas.getContext('2d', { willReadFrequently: true });
            let isDrawing = false;

            eraserCanvas.addEventListener('mousedown', startErasing);
            eraserCanvas.addEventListener('touchstart', startErasing, { passive: false });

            function startErasing(e) {
                e.preventDefault();
                const rect = eraserCanvas.getBoundingClientRect();
                const cardRect = card.getBoundingClientRect();
                const x = (e.touches ? e.touches[0].clientX : e.clientX) - cardRect.left;
                const y = (e.touches ? e.touches[0].clientY : e.clientY) - cardRect.top;

                if(magicMode) {
                    saveState();
                    magicErase(x, y, ctx);
                    return;
                }
                isDrawing = true;
                saveState();
                erase(x, y, ctx);
            }

            // دالة الممحاة السحرية الجديدة (Flood Fill)
            function magicErase(x, y, ctx) {
                const protectBg = document.getElementById('eraser-protect-bg').checked;
                const images = Array.from(card.querySelectorAll('.image-layer')).reverse();

                for (let imgLayer of images) {
                    if(protectBg && imgLayer.classList.contains('bg-image')) continue;

                    const rect = imgLayer.getBoundingClientRect();
                    const cardRect = card.getBoundingClientRect();
                    const layerLeft = rect.left - cardRect.left;
                    const layerTop = rect.top - cardRect.top;

                    const relX = Math.floor(x - layerLeft);
                    const relY = Math.floor(y - layerTop);
                    const width = rect.width;
                    const height = rect.height;

                    // Check if click is inside this layer
                    if(relX >= 0 && relX < width && relY >= 0 && relY < height) {
                        const img = imgLayer.querySelector('img');
                        if(!img) continue;

                        // Create or use existing canvas
                        if(!imgLayer.magicCanvas) {
                            imgLayer.magicCanvas = document.createElement('canvas');
                            imgLayer.magicCanvas.width = img.naturalWidth || width;
                            imgLayer.magicCanvas.height = img.naturalHeight || height;
                            const magicCtx = imgLayer.magicCanvas.getContext('2d');
                            magicCtx.drawImage(img, 0, 0, imgLayer.magicCanvas.width, imgLayer.magicCanvas.height);
                        }

                        performFloodFill(imgLayer, relX, relY, width, height);
                        break;
                    }
                }

                function performFloodFill(imgLayer, clickX, clickY, displayWidth, displayHeight) {
                    const img = imgLayer.querySelector('img');
                    const canvas = imgLayer.magicCanvas;
                    const imgCtx = canvas.getContext('2d', { willReadFrequently: true });
                    const imageData = imgCtx.getImageData(0, 0, canvas.width, canvas.height);
                    const data = imageData.data;

                    // Scale click position to image coordinates
                    const scaleX = canvas.width / displayWidth;
                    const scaleY = canvas.height / displayHeight;
                    const imgX = Math.floor(clickX * scaleX);
                    const imgY = Math.floor(clickY * scaleY);

                    // Check bounds
                    if(imgX < 0 || imgX >= canvas.width || imgY < 0 || imgY >= canvas.height) return;

                    const startIdx = (imgY * canvas.width + imgX) * 4;
                    const sr = data[startIdx];
                    const sg = data[startIdx + 1];
                    const sb = data[startIdx + 2];
                    const sa = data[startIdx + 3];

                    if(sa === 0) return; // Clicked on transparent

                    const tolerance = magicTolerance;

                    function colorsMatch(r, g, b, a) {
                        if(a === 0) return false;
                        const dr = r - sr;
                        const dg = g - sg;
                        const db = b - sb;
                        return (Math.abs(dr) + Math.abs(dg) + Math.abs(db)) < (tolerance * 3 * 2.55);
                    }

                    // Flood fill using queue
                    const queue = [startIdx];
                    const visited = new Set();
                    visited.add(startIdx);

                    while(queue.length > 0) {
                        const idx = queue.shift();
                        data[idx + 3] = 0; // Make transparent

                        const pixelIndex = idx / 4;
                        const px = pixelIndex % canvas.width;
                        const py = Math.floor(pixelIndex / canvas.width);

                        // Check 4 neighbors
                        const neighbors = [
                            {x: px - 1, y: py},
                            {x: px + 1, y: py},
                            {x: px, y: py - 1},
                            {x: px, y: py + 1}
                        ];

                        for(let neighbor of neighbors) {
                            if(neighbor.x >= 0 && neighbor.x < canvas.width && neighbor.y >= 0 && neighbor.y < canvas.height) {
                                const nIdx = (neighbor.y * canvas.width + neighbor.x) * 4;
                                if(!visited.has(nIdx)) {
                                    visited.add(nIdx);
                                    const nr = data[nIdx];
                                    const ng = data[nIdx + 1];
                                    const nb = data[nIdx + 2];
                                    const na = data[nIdx + 3];

                                    if(colorsMatch(nr, ng, nb, na)) {
                                        queue.push(nIdx);
                                    }
                                }
                            }
                        }
                    }

                    imgCtx.putImageData(imageData, 0, 0);
                    const newSrc = canvas.toDataURL();
                    img.src = newSrc;
                    
                    // تحديث الـ mask إذا كان هناك تدرج أو تلوين على الصورة
                    const contentWrapper = imgLayer.querySelector('.image-content-wrapper') || imgLayer.querySelector('.content-wrapper');
                    if(contentWrapper && (imgLayer.hasAttribute('data-has-gradient') || imgLayer.hasAttribute('data-has-color'))) {
                        contentWrapper.style.webkitMaskImage = 'url(' + newSrc + ')';
                        contentWrapper.style.maskImage = 'url(' + newSrc + ')';
                    }
                }
            }

            function erase(x, y, ctx) {
                const protectBg = document.getElementById('eraser-protect-bg').checked;
                const images = card.querySelectorAll('.image-layer');
                images.forEach(imgLayer => {
                    if(protectBg && imgLayer.classList.contains('bg-image')) {
                        return;
                    }
                    const rect = imgLayer.getBoundingClientRect();
                    const cardRect = card.getBoundingClientRect();
                    const relX = rect.left - cardRect.left;
                    const relY = rect.top - cardRect.top;
                    const width = rect.width;
                    const height = rect.height;
                    if(x >= relX && x <= relX + width && y >= relY && y <= relY + height) {
                        const img = imgLayer.querySelector('img');
                        if(img && img.complete) {
                            // استخدم الدقة الأصلية للصورة، لا البكسل المعروض
                            const naturalWidth = img.naturalWidth || width;
                            const naturalHeight = img.naturalHeight || height;

                            if(!imgLayer.canvas) {
                                imgLayer.canvas = document.createElement('canvas');
                                imgLayer.canvas.width = naturalWidth;
                                imgLayer.canvas.height = naturalHeight;
                                const imgCtx = imgLayer.canvas.getContext('2d');
                                imgCtx.drawImage(img, 0, 0, naturalWidth, naturalHeight);
                            }

                            // حساب الإحداثيات بناءً على الدقة الأصلية
                            const scaleX = naturalWidth / width;
                            const scaleY = naturalHeight / height;
                            const scaledX = (x - relX) * scaleX;
                            const scaledY = (y - relY) * scaleY;
                            const scaledSize = (eraserSize / 2) * Math.max(scaleX, scaleY);

                            const imgCtx = imgLayer.canvas.getContext('2d');
                            imgCtx.globalCompositeOperation = 'destination-out';
                            imgCtx.shadowBlur = eraserSoftness * Math.max(scaleX, scaleY);
                            imgCtx.shadowColor = "black";
                            imgCtx.fillStyle = "black";
                            imgCtx.beginPath();
                            imgCtx.arc(scaledX, scaledY, scaledSize, 0, Math.PI * 2);
                            imgCtx.fill();
                            const newSrc = imgLayer.canvas.toDataURL();
                            img.src = newSrc;
                            
                            // تحديث الـ mask إذا كان هناك تدرج أو تلوين على الصورة
                            const contentWrapper = imgLayer.querySelector('.image-content-wrapper') || imgLayer.querySelector('.content-wrapper');
                            if(contentWrapper && (imgLayer.hasAttribute('data-has-gradient') || imgLayer.hasAttribute('data-has-color'))) {
                                contentWrapper.style.webkitMaskImage = 'url(' + newSrc + ')';
                                contentWrapper.style.maskImage = 'url(' + newSrc + ')';
                            }
                        }
                    }
                });
            }

            eraserCanvas.addEventListener('mousemove', (e) => {
                if(!isDrawing) return;
                const rect = eraserCanvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                erase(x, y, ctx);
            });

            eraserCanvas.addEventListener('touchmove', (e) => {
                if(!isDrawing) return;
                e.preventDefault();
                const rect = eraserCanvas.getBoundingClientRect();
                const x = e.touches[0].clientX - rect.left;
                const y = e.touches[0].clientY - rect.top;
                erase(x, y, ctx);
            });

            eraserCanvas.addEventListener('mouseup', () => { isDrawing = false; });
            eraserCanvas.addEventListener('touchend', () => { isDrawing = false; });

            card.appendChild(eraserCanvas);
        }

        document.addEventListener('DOMContentLoaded', () => {
            // تحميل القوالب من GitHub إذا لم تكن موجودة
            loadTemplatesFromGitHub();

            const eraserSizeInput = document.getElementById('eraser-size');
            const eraserSoftnessInput = document.getElementById('eraser-softness');
            const magicToleranceInput = document.getElementById('magic-tolerance');

            if(eraserSizeInput) {
                eraserSizeInput.addEventListener('input', (e) => {
                    eraserSize = parseInt(e.target.value);
                    document.getElementById('eraser-size-display').textContent = eraserSize;
                });
            }
            if(eraserSoftnessInput) {
                eraserSoftnessInput.addEventListener('input', (e) => {
                    eraserSoftness = parseInt(e.target.value);
                    document.getElementById('eraser-softness-display').textContent = eraserSoftness;
                });
            }
            if(magicToleranceInput) {
                magicToleranceInput.addEventListener('input', (e) => {
                    magicTolerance = parseInt(e.target.value);
                    document.getElementById('magic-tolerance-display').textContent = magicTolerance;
                });
            }

            // ربط event listeners للتدرج
            const color1Input = document.getElementById('gradient-color1');
            const color2Input = document.getElementById('gradient-color2');
            const opacityInput = document.getElementById('gradient-opacity');
            const directionInput = document.getElementById('gradient-direction');
            const opacityDisplay = document.getElementById('gradient-opacity-display');

            if(color1Input) color1Input.addEventListener('change', updateGradientPreview);
            if(color2Input) color2Input.addEventListener('change', updateGradientPreview);
            if(opacityInput) {
                opacityInput.addEventListener('input', (e) => {
                    opacityDisplay.textContent = e.target.value;
                    updateGradientPreview();
                });
            }
            if(directionInput) directionInput.addEventListener('change', updateGradientPreview);
        });

        function setupInteract(el, type) {
            if(el.hasAttribute('data-events-bound')) return;
            el.setAttribute('data-events-bound', 'true');

            el.addEventListener('click', function(e) {
                e.stopPropagation();
            });

            el.addEventListener('mousedown', startDrag);
            el.addEventListener('touchstart', startDrag, {passive: false});

            function startDrag(e) {
                // Fix for iOS delete button tap - Check this FIRST
                if(e.target.closest('.control-btn')) return;

                if(el.classList.contains('is-locked')) return;

                // === تعديل: التحقق من مقبض التحريك أولاً ===
                const isMoveHandle = e.target.classList.contains('move-handle') || e.target.closest('.move-handle');

                if (!isMoveHandle) {
                    // Content editable check - simple return allows focus
                    if(e.target.isContentEditable || e.target.closest('.user-text')) {
                        selectEl(el);
                        if (e.type === 'touchstart') {
                            e.target.focus();
                        }
                        return;
                    }
                }
                // ============================================

                const isTouch = e.type === 'touchstart';
                const startX = isTouch ? e.touches[0].clientX : e.clientX;
                const startY = isTouch ? e.touches[0].clientY : e.clientY;

                if(e.target.classList.contains('handle')) {
                    handleResize(e, el, e.target, startX, startY);
                    return;
                }

                if(el.classList.contains('frame-layer') && e.target === el) {
                    selectEl(el);
                    return;
                }


                // === تعديل جديد: السماح بالتحريك إذا كان العنصر محدداً مسبقاً ===
                // إذا لم يكن الضغط على المقبض ولم يكن العنصر محدداً، نكتفي بالتحديد (للسماح باختياره أولاً)
                if (!isMoveHandle && !el.classList.contains('selected')) {
                    selectEl(el);
                    return;
                }
                // أما إذا كان محدداً، فسيتم تجاوز هذا الشرط والسماح بالسحب من أي مكان (حل لمشكلة اختفاء المقبض)
                // ============================================

                e.preventDefault();
                e.stopPropagation();

                selectEl(el);

                const startLeft = el.offsetLeft;
                const startTop = el.offsetTop;

                function onMove(ev) {
                    ev.preventDefault();

                    // حساب الزووم لضمان حركة متطابقة
                    const zoomFactor = (window.currentZoom || 100) / 100;

                    const cx = isTouch ? ev.touches[0].clientX : ev.clientX;
                    const cy = isTouch ? ev.touches[0].clientY : ev.clientY;

                    // تقسيم الإزاحة على معامل الزووم
                    const dx = (cx - startX) / zoomFactor;
                    const dy = (cy - startY) / zoomFactor;

                    let newLeft = startLeft + dx;
                    let newTop = startTop + dy;

                    el.style.left = `${newLeft}px`;
                    el.style.top = `${newTop}px`;

                    const currentRotate = parseFloat(el.getAttribute('data-rotate')) || 0;
                    el.style.transform = `translate(-50%, -50%) rotate(${currentRotate}deg)`;
                }

                function onUp() {
                    document.removeEventListener(isTouch ? 'touchmove' : 'mousemove', onMove);
                    document.removeEventListener(isTouch ? 'touchend' : 'mouseup', onUp);
                    saveState();
                }

                document.addEventListener(isTouch ? 'touchmove' : 'mousemove', onMove, {passive: false});
                document.addEventListener(isTouch ? 'touchend' : 'mouseup', onUp);
            }
        }

        function handleResize(e, el, handle, startX, startY) {
            const isTouch = e.type === 'touchstart';
            const startW = el.offsetWidth;
            const startH = el.offsetHeight;
            const startLeft = el.offsetLeft;
            const startTop = el.offsetTop;
            // حفظ حجم الخط عند بدء السحب
            const startFontSize = parseFloat(window.getComputedStyle(el).fontSize);

            function onResize(ev) {
                ev.preventDefault();
                ev.stopPropagation();

                const cx = isTouch ? ev.touches[0].clientX : ev.clientX;
                const cy = isTouch ? ev.touches[0].clientY : ev.clientY;

                const dx = cx - startX;
                const dy = cy - startY;

                let newW = startW;
                let newH = startH;
                let newLeft = startLeft;
                let newTop = startTop;

                // حساب الأبعاد الجديدة بناءً على المقبض
                if (handle.classList.contains('resize-n') || handle.classList.contains('resize-ne') || handle.classList.contains('resize-nw')) {
                    let potentialH = startH - dy;
                    newH = Math.max(20, potentialH);
                    newTop = startTop - (newH - startH) / 2;
                } else if (handle.classList.contains('resize-s') || handle.classList.contains('resize-se') || handle.classList.contains('resize-sw')) {
                    let potentialH = startH + dy;
                    newH = Math.max(20, potentialH);
                    newTop = startTop + (newH - startH) / 2;
                }

                if (handle.classList.contains('resize-e') || handle.classList.contains('resize-ne') || handle.classList.contains('resize-se')) {
                    let potentialW = startW + dx;
                    newW = Math.max(20, potentialW);
                    newLeft = startLeft + (newW - startW) / 2;
                } else if (handle.classList.contains('resize-w') || handle.classList.contains('resize-nw') || handle.classList.contains('resize-sw')) {
                    let potentialW = startW - dx;
                    newW = Math.max(20, potentialW);
                    newLeft = startLeft - (newW - startW) / 2;
                }

                // === تعديل: منطق خاص للنصوص ===
                if (el.classList.contains('text-layer')) {
                    // إذا كان السحب من الزوايا (تكبير/تصغير تناسبي)
                    if (handle.classList.contains('resize-ne') || handle.classList.contains('resize-se') ||
                        handle.classList.contains('resize-nw') || handle.classList.contains('resize-sw')) {

                        // استخدام نسبة التغير في الارتفاع لتغيير حجم الخط
                        const ratio = newH / startH;
                        let newFS = startFontSize * ratio;

                        // حدود حجم الخط
                        if (newFS < 10) newFS = 10;
                        if (newFS > 300) newFS = 300;

                        // تطبيق حجم الخط الجديد
                        el.style.fontSize = newFS + 'px';

                        // تحديث الحقول والأرقام في اللوحة (بدون حفظ الحالة في كل إطار)
                        document.getElementById('font-size').value = parseInt(newFS);
                        document.getElementById('font-size-input').value = parseInt(newFS);
                        document.getElementById('top-font-size').value = parseInt(newFS);
                        document.getElementById('top-font-size-input').value = parseInt(newFS);

                        // جعل الأبعاد تلقائية لتناسب النص
                        el.style.width = 'auto';
                        el.style.height = 'auto';

                        // تحديث الموقع
                        el.style.left = newLeft + 'px';
                        el.style.top = newTop + 'px';

                    } else {
                        // إذا كان السحب من الجوانب (تغيير عرض فقط للتدفق)
                        if (handle.classList.contains('resize-e') || handle.classList.contains('resize-w')) {
                            el.style.width = newW + 'px';
                            el.style.height = 'auto';
                            el.style.left = newLeft + 'px';
                            el.style.top = newTop + 'px';
                        }
                    }
                } else {
                    // للكائنات الأخرى (صور، إطارات)
                    // التحجيم من الزوايا = الحفاظ على نسبة العرض للارتفاع
                    if ((handle.classList.contains('resize-ne') || handle.classList.contains('resize-se') ||
                         handle.classList.contains('resize-nw') || handle.classList.contains('resize-sw')) && !e.shiftKey) {

                        const aspectRatio = startW / startH;
                        const widthChangePct = Math.abs((newW - startW) / startW);
                        const heightChangePct = Math.abs((newH - startH) / startH);

                        if (widthChangePct > heightChangePct) {
                             // العرض هو الأساس
                             newH = newW / aspectRatio;

                             if (handle.classList.contains('resize-n') || handle.classList.contains('resize-ne') || handle.classList.contains('resize-nw')) {
                                newTop = startTop - (newH - startH) / 2;
                             } else {
                                newTop = startTop + (newH - startH) / 2;
                             }
                        } else {
                             // الارتفاع هو الأساس
                             newW = newH * aspectRatio;

                             if (handle.classList.contains('resize-nw') || handle.classList.contains('resize-sw') || handle.classList.contains('resize-w')) {
                                newLeft = startLeft - (newW - startW) / 2;
                             } else {
                                newLeft = startLeft + (newW - startW) / 2;
                             }
                        }
                    }
                    // التحجيم من الجوانب = تغيير حر (العرض أو الارتفاع فقط)
                    // لا نحتاج تعديل إضافي لأن القيم محسوبة مسبقاً

                    el.style.width = newW + 'px';
                    el.style.height = newH + 'px';
                    el.style.left = newLeft + 'px';
                    el.style.top = newTop + 'px';
                }

                updateControlsPosition(el);
            }

            function onUp() {
                document.removeEventListener(isTouch ? 'touchmove' : 'mousemove', onResize);
                document.removeEventListener(isTouch ? 'touchend' : 'mouseup', onUp);
                saveState();
            }

            document.addEventListener(isTouch ? 'touchmove' : 'mousemove', onResize, {passive: false});
            document.addEventListener(isTouch ? 'touchend' : 'mouseup', onUp);
        }

        let lastSelectionTime = 0;
        let lastSelectedElement = null; // متغير لتتبع آخر عنصر تم تحديده
        let mouseDownOnElement = null; // متغير لتتبع العنصر الذي تم الضغط عليه

        function selectEl(el) {
            if (el) updateControlsPosition(el);
            if(activeEl) activeEl.classList.remove('selected');

            activeEl = el;
            activeEl.classList.add('selected');
            lastSelectionTime = Date.now();
            lastSelectedElement = el;

            // إظهار النافذة العائمة وزر الإغلاق (للنصوص فقط الآن)
            const floatToolbar = document.getElementById('floating-context-toolbar');
            const closeFloatBtn = document.getElementById('close-floating-toolbar');

            if (el.classList.contains('image-layer') || el.classList.contains('frame-layer')) {
                 if(floatToolbar) floatToolbar.classList.add('hidden');
                 if(closeFloatBtn) closeFloatBtn.classList.add('hidden');
            } else {
                 if(floatToolbar) floatToolbar.classList.remove('hidden');
                 if(closeFloatBtn) closeFloatBtn.classList.remove('hidden');
            }

            const panel = document.getElementById('style-panel');
            panel.classList.remove('opacity-50', 'pointer-events-none');

            document.getElementById('quick-props').classList.remove('hidden');
            document.getElementById('quick-props').classList.add('active');
            // no-selection-msg يبقى ظاهر دائماً

            // تحديث قيمة الشفافية
            const currentOpacity = parseFloat(el.style.opacity) || 1;
            const opacityPercent = Math.round(currentOpacity * 100);
            document.getElementById('layer-opacity').value = opacityPercent;
            document.getElementById('opacity-value').textContent = opacityPercent + '%';

            document.getElementById('text-controls').classList.add('hidden');
            document.getElementById('frame-controls').classList.add('hidden');
            document.getElementById('frame-controls-toolbar').classList.add('hidden');
            document.getElementById('gradient-toggle-row').classList.add('hidden'); if(document.getElementById('text-alignment-row')) document.getElementById('text-alignment-row').classList.add('hidden'); // إخفاء زر التدرج مبدئياً
            if(document.getElementById('text-alignment-row')) document.getElementById('text-alignment-row').classList.add('hidden');

            document.getElementById('top-font-controls').classList.add('hidden');

            // إخفاء قسم لون النص افتراضياً
            document.getElementById('text-color-section').classList.add('hidden');

            // التحقق من العناصر القابلة للتلوين - جميع الصور ما عدا colorable = false
            if(el.classList.contains('image-layer') && el.getAttribute('data-colorable') !== 'false') {

                // إظهار زر التدرج للصور أيضاً
                document.getElementById('gradient-toggle-row').classList.remove('hidden');
                document.getElementById('gradient-toggle-row').classList.add('flex');

                // تحديث لون الـ input من لون الخلفية الحالي
                const currentBg = el.style.backgroundColor;
                if(currentBg && currentBg !== 'transparent') {
                    // if element exists
                    if(document.getElementById('colorable-color')) document.getElementById('colorable-color').value = rgbToHex(currentBg);
                }
            }

            if(el.classList.contains('text-layer')) {
                document.getElementById('text-controls').classList.remove('hidden');
                document.getElementById('top-font-controls').classList.remove('hidden');
                document.getElementById('top-font-controls').classList.add('flex');
                document.getElementById('gradient-toggle-row').classList.remove('hidden'); // إظهار زر التدرج للنصوص
                document.getElementById('gradient-toggle-row').classList.add('flex'); // إضافة flex للعرض الصحيح
                if(document.getElementById('text-alignment-row')) {
                    document.getElementById('text-alignment-row').classList.remove('hidden');
                    document.getElementById('text-alignment-row').classList.add('flex');
                }

                // تحديث حالة واجهة التدرج بناءً على هذا النص بالتحديد
                updateGradientUIState(el);

                // إظهار قسم لون النص فقط مع النصوص
                document.getElementById('text-color-section').classList.remove('hidden');

                const fSize = parseInt(window.getComputedStyle(el).fontSize); // Use computed style for accuracy
                document.getElementById('font-size').value = fSize;
                document.getElementById('font-size-input').value = fSize;
                document.getElementById('top-font-size').value = fSize;
                document.getElementById('top-font-size-input').value = fSize;

                const fontFamily = el.style.fontFamily.replace(/"/g, "'");
                document.getElementById('font-family').value = fontFamily;
                document.getElementById('top-font-family').value = fontFamily;
                document.getElementById('quick-color').value = rgbToHex(el.style.color);

                // تحديث لون النص في النافذة العائمة
                const textDiv = el.querySelector('.user-text');
                if (textDiv) {
                    const textColor = textDiv.style.color || el.style.color || '#1e293b';
                    document.getElementById('top-text-color').value = rgbToHex(textColor);
                }

                updateBoldButtonState();
            } else if(el.classList.contains('frame-layer')) {
                document.getElementById('frame-controls').classList.remove('hidden');
                document.getElementById('frame-controls-toolbar').classList.remove('hidden');
                document.getElementById('frame-controls-toolbar').classList.add('flex');
                const borderColor = el.style.borderColor || el.style.backgroundColor || '#334155';
                document.getElementById('border-color').value = rgbToHex(borderColor);
            }
        }

        // دالة تبديل البولد
        function toggleBold() {
            if (!activeEl) return;
            const currentWeight = activeEl.style.fontWeight;
            const btn = document.getElementById('btn-bold');

            if (currentWeight === 'bold' || currentWeight === '700') {
                activeEl.style.fontWeight = 'normal';
                btn.classList.remove('bg-[#6366f1]', 'text-white');
                btn.classList.add('bg-white', 'text-[#1e293b]');
            } else {
                activeEl.style.fontWeight = 'bold';
                btn.classList.add('bg-[#6366f1]', 'text-white');
                btn.classList.remove('bg-white', 'text-[#1e293b]');
            }
            saveState();
        }

        // تحديث حالة زر البولد عند التحديد
        function updateBoldButtonState() {
            const btn = document.getElementById('btn-bold');
            if (!activeEl || !btn) return;
            const currentWeight = activeEl.style.fontWeight;
            if (currentWeight === 'bold' || currentWeight === '700') {
                btn.classList.add('bg-[#6366f1]', 'text-white');
                btn.classList.remove('bg-white', 'text-[#1e293b]');
            } else {
                btn.classList.remove('bg-[#6366f1]', 'text-white');
                btn.classList.add('bg-white', 'text-[#1e293b]');
            }
        }

        const SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTiWBnSkPTGN8S3-QjqwSjpJicszKs2ZuwI40iPph2EWQhgz9F10c7LIjMwa_cdPJr40OoDmqZDbP5F/pub?output=csv";
        const CORS_PROXIES = [
            "https://cors-anywhere.herokuapp.com/",
            "https://api.allorigins.win/raw?url=",
            "https://thingproxy.freeboard.io/fetch/"
        ];

        let subscriptionData = {};

        async function loadSubscriptionData() {
            try {
                let response = null;
                let csvText = null;

                try {
                    response = await fetch(SHEET_CSV_URL, { mode: 'cors' });
                    if (response.ok) {
                        csvText = await response.text();
                    }
                } catch (e) {
                    // لا شيء
                }

                if (!csvText) {
                    for (let proxy of CORS_PROXIES) {
                        try {
                            let proxyUrl = proxy + encodeURIComponent(SHEET_CSV_URL);
                            response = await fetch(proxyUrl);
                            if (response.ok) {
                                csvText = await response.text();
                                break;
                            }
                        } catch (e) {
                            continue;
                        }
                    }
                }

                if (csvText) {
                    parseCSVData(csvText);
                    return true;
                } else {
                    throw new Error('فشل الوصول إلى البيانات');
                }
            } catch (error) {
                return false;
            }
        }

        function parseCSVData(csvText) {
            try {
                const lines = csvText.trim().split('\n');
                if (lines.length < 2) return;

                const headers = lines[0].split(',').map(h => h.trim().toLowerCase());

                const codeIndex = headers.findIndex(h => h.includes('code'));
                const nameIndex = headers.findIndex(h => h.includes('name'));
                const expiryIndex = headers.findIndex(h => h.includes('expiry'));

                for (let i = 1; i < lines.length; i++) {
                    if (!lines[i].trim()) continue;

                    const cells = lines[i].split(',').map(c => c.trim());
                    if (codeIndex >= 0 && nameIndex >= 0 && expiryIndex >= 0) {
                        const code = cells[codeIndex];
                        const name = cells[nameIndex];
                        const expiryDate = cells[expiryIndex];

                        if (code && name && expiryDate) {
                            subscriptionData[code] = {
                                name: name,
                                expiryDate: expiryDate
                            };
                        }
                    }
                }
            } catch (error) {
                // لا شيء
            }
        }

        async function verifyCode() {
    console.log("Starting verification...");
    const input = document.getElementById('login-code-input');
    const code = input.value.trim();
    const errorMsg = document.getElementById('login-error');
    const loginBtn = document.getElementById('login-btn');
    const loadingDiv = document.getElementById('login-loading');

    // إعادة ضبط الرسالة وإخفاءها بشكل كامل
    if(errorMsg) {
        errorMsg.style.display = 'none';
        errorMsg.classList.add('hidden');
        errorMsg.innerHTML = '';
    }

    if (!code) {
        if(errorMsg) {
            errorMsg.innerHTML = '<i class="fas fa-exclamation-circle ml-1"></i> أدخل الكود من فضلك';
            errorMsg.className = 'text-center p-3 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm font-bold animate-shake mt-4';
            errorMsg.style.display = 'block';
            errorMsg.classList.remove('hidden');
        }
        return;
    }

    if(loginBtn) loginBtn.disabled = true;

    // محاولة إظهار السبينر المدمج في الزر الجديد
    const btnText = document.getElementById('login-btn-text');
    const btnSpinner = document.getElementById('login-btn-spinner');

    if (btnText && btnSpinner) {
        btnText.style.opacity = '0';
        btnSpinner.classList.remove('hidden');
    } else if (loadingDiv) {
        // Fallback للتصميم القديم
        loadingDiv.style.display = 'block';
    }

    let success = false;

    try {
        // التأكد من تحميل البيانات
        if (typeof subscriptionData === 'undefined' || Object.keys(subscriptionData).length === 0) {
            const loaded = await loadSubscriptionData();
            if (!loaded) {
                throw new Error('فشل تحميل قاعدة البيانات، تحقق من الإنترنت');
            }
        }

        if (subscriptionData[code]) {
            const userData = subscriptionData[code];

            let expiryDate = null;
            const dateStr = userData.expiryDate.trim();

            // دعم تنسيقات مختلفة للتاريخ
            if (dateStr.match(/^\d{2}-\d{2}-\d{4}$/)) {
                const [day, month, year] = dateStr.split('-');
                expiryDate = new Date(`${year}-${month}-${day}`);
            }
            else if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
                expiryDate = new Date(dateStr);
            }
            else if (dateStr.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
                expiryDate = new Date(dateStr);
            }

            if (!expiryDate || isNaN(expiryDate.getTime())) {
                throw new Error('تاريخ صلاحية الكود غير صالح');
            }

            const today = new Date();
            today.setHours(0, 0, 0, 0);
            expiryDate.setHours(0, 0, 0, 0);

            if (expiryDate >= today) {
                success = true; // علامة النجاح لمنع إعادة تفعيل الزر

                // إنشاء Session ID عشوائي
                const sessionId = 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();

                // حفظ الجلسة
                const sessionObj = {
                        name: userData.name,
                        expiryDate: userData.expiryDate,
                        sessionId: sessionId
                };

                sessionStorage.setItem('studioName', userData.name);
                sessionStorage.setItem('expiryDate', userData.expiryDate);
                sessionStorage.setItem('sessionId', sessionId);
                localStorage.setItem('despro_session', JSON.stringify(sessionObj));

                // تعديل الـ tier إلى premium
                setPremiumUser();

                // تحديث العنوان
                updateStudioName(userData.name);

                // إعادة تحميل الصفحة لفتح الاستوديو
                window.location.reload();

            } else {
                const formattedDate = expiryDate.toLocaleDateString('ar-SA');
                if(errorMsg) {
                    errorMsg.innerHTML = `⏰ اشتراكك انتهى في ${formattedDate}<br><small style="font-size: 11px; color: #94a3b8; font-weight:normal;">تواصل مع الدعم الفني للتجديد</small>`;
                    errorMsg.className = 'text-center p-3 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm font-bold animate-shake mt-4';
                    errorMsg.style.display = 'block';
                    errorMsg.classList.remove('hidden');
                }
            }
        } else {
            if(errorMsg) {
                errorMsg.innerHTML = '<i class="fas fa-times-circle ml-1"></i> الكود غير صحيح أو غير موجود';
                errorMsg.className = 'text-center p-3 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm font-bold animate-shake mt-4';
                errorMsg.style.display = 'block';
                errorMsg.classList.remove('hidden');
            }
        }
    } catch (error) {
        console.error(error);
        if(errorMsg) {
            errorMsg.innerHTML = `<i class="fas fa-exclamation-triangle ml-1"></i> ${error.message || 'حدث خطأ غير متوقع'}`;
            errorMsg.className = 'text-center p-3 bg-amber-50 border border-amber-100 rounded-2xl text-amber-600 text-sm font-bold animate-shake mt-4';
            errorMsg.style.display = 'block';
            errorMsg.classList.remove('hidden');
        }
    } finally {
        // إعادة الزر لوضعه الطبيعي فقط في حالة الفشل
        if (!success) {
            if(loginBtn) loginBtn.disabled = false;
            if (btnText && btnSpinner) {
                btnText.style.opacity = '1';
                btnSpinner.classList.add('hidden');
            } else if (loadingDiv) {
                loadingDiv.style.display = 'none';
            }
        }
    }
}



        function updateStudioName(name) {
            document.title = `أستوديو ${name} | Studio`;
            const studioNameDisplay = document.getElementById('studio-name-display');
            if (studioNameDisplay) {
                studioNameDisplay.textContent = `أستوديو ${name}`;
            }
        }

        function showWelcomeNotification(name) {
            console.log(`مرحباً بك في أستوديو ${name}`);
        }

        window.addEventListener('load', async () => {
            loadSubscriptionData();
            applyTierRestrictions(); // تطبيق التقييدات عند التحميل
        });

        function deselect(e) {
            if(e && (e.target.closest(".draggable-el") || e.target.closest("#style-panel") || e.target.closest("#floating-context-toolbar") || e.target.closest("select") || e.target.closest("input") || e.target.closest(".controls-row") || e.target.closest("button") || e.target.closest("#eraser-controls") || e.target.closest("#smart-tool-tutorial-modal") || e.target.closest("#confirm-modal") || e.target.closest("#info-modal"))) return;

            if(activeEl) activeEl.classList.remove('selected');
            activeEl = null;

            // إلغاء وضع الممحاة عند إزالة التحديد
            if(eraserMode) exitEraserMode();

            // إخفاء النافذة العائمة
            const floatToolbar = document.getElementById('floating-context-toolbar');
            const closeFloatBtn = document.getElementById('close-floating-toolbar');
            if(floatToolbar) floatToolbar.classList.add('hidden');
            if(closeFloatBtn) closeFloatBtn.classList.add('hidden');

            document.getElementById('quick-props').classList.add('hidden');
            document.getElementById('quick-props').classList.remove('active');
            document.getElementById('text-controls').classList.add('hidden');
            document.getElementById('frame-controls').classList.add('hidden');
            document.getElementById('frame-controls-toolbar').classList.add('hidden');
            // document.getElementById('colorable-controls-toolbar').classList.add('hidden');
            document.getElementById('gradient-toggle-row').classList.add('hidden'); if(document.getElementById('text-alignment-row')) document.getElementById('text-alignment-row').classList.add('hidden');

            document.getElementById('top-font-controls').classList.add('hidden');
            document.getElementById('top-font-controls').classList.remove('flex');

            // no-selection-msg يبقى ظاهر دائماً

            // إخفاء شريط التدرج للعناصر
            const gradControls = document.getElementById('grad-controls');
            const btnGrad = document.getElementById('btn-grad');
            const elementGradInputs = document.getElementById('element-grad-inputs');
            const globalGradInputs = document.getElementById('global-grad-inputs');

            if(gradControls.classList.contains('active') && !elementGradInputs.classList.contains('hidden')) {
                // كان في وضع تدرج العنصر، نعيده للوضع العام
                elementGradInputs.classList.add('hidden');
                elementGradInputs.classList.remove('flex');
                globalGradInputs.classList.remove('hidden');
                globalGradInputs.classList.add('flex');

                // إذا ما فيه تدرج عام مفعل، نخفي الشريط كامل
                if(!hasGradient) {
                    gradControls.classList.remove('active');
                    btnGrad.classList.remove('bg-[#6366f1]', 'text-white');
                    btnGrad.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
                }
            }
        }

        // دالة إلغاء التحديد عند الضغط على البطاقة مباشرة
        function deselectOnCard(e) {
            // حماية: إذا ضغط على عنصر وفي حركة من الماوس للأسفل وللأعلى
            // نتجاهل الـ event إذا كانت الضغطة الأولى على عنصر
            const elementUnderClick = document.elementFromPoint(
                e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0),
                e.clientY || (e.touches && e.touches[0] ? e.touches[0].clientY : 0)
            );

            // إذا كان العنصر تحت المؤشر هو draggable-el أو بداخله
            if(elementUnderClick && elementUnderClick.closest('.draggable-el')) return;

            // فقط إذا ضغط على البطاقة الفارغة أو الـ gradient مباشرة
            if(e.target.id !== 'card' && e.target.id !== 'card-gradient') return;

            // إلغاء التحديد
            if(activeEl) activeEl.classList.remove('selected');
            activeEl = null;

            // إلغاء وضع الممحاة عند إزالة التحديد
            if(eraserMode) exitEraserMode();

            // إخفاء النافذة العائمة
            const floatToolbar = document.getElementById('floating-context-toolbar');
            const closeFloatBtn = document.getElementById('close-floating-toolbar');
            if(floatToolbar) floatToolbar.classList.add('hidden');
            if(closeFloatBtn) closeFloatBtn.classList.add('hidden');

            document.getElementById('quick-props').classList.add('hidden');
            document.getElementById('quick-props').classList.remove('active');
            document.getElementById('text-controls').classList.add('hidden');
            document.getElementById('frame-controls').classList.add('hidden');
            document.getElementById('frame-controls-toolbar').classList.add('hidden');
            // document.getElementById('colorable-controls-toolbar').classList.add('hidden');
            document.getElementById('gradient-toggle-row').classList.add('hidden'); if(document.getElementById('text-alignment-row')) document.getElementById('text-alignment-row').classList.add('hidden');

            document.getElementById('top-font-controls').classList.add('hidden');
            document.getElementById('top-font-controls').classList.remove('flex');

            // إخفاء شريط التدرج للعناصر
            const gradControls = document.getElementById('grad-controls');
            const btnGrad = document.getElementById('btn-grad');
            const elementGradInputs = document.getElementById('element-grad-inputs');
            const globalGradInputs = document.getElementById('global-grad-inputs');

            if(gradControls && gradControls.classList.contains('active') && elementGradInputs && !elementGradInputs.classList.contains('hidden')) {
                // كان في وضع تدرج العنصر، نعيده للوضع العام
                elementGradInputs.classList.add('hidden');
                elementGradInputs.classList.remove('flex');
                globalGradInputs.classList.remove('hidden');
                globalGradInputs.classList.add('flex');

                // إذا ما فيه تدرج عام مفعل، نخفي الشريط كامل
                if(!hasGradient) {
                    gradControls.classList.remove('active');
                    btnGrad.classList.remove('bg-[#6366f1]', 'text-white');
                    btnGrad.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
                }
            }
        }

        function toggleLock(el) {
            el.classList.toggle('is-locked');
            if(el.classList.contains('is-locked')) {
                el.classList.remove('selected');
                if(activeEl === el) deselect();
            }
        }

        // قائمة الخطوط المخصصة المرفوعة
        let customFonts = [];

        // قائمة الخطوط المفضلة (تُحفظ في localStorage)
        let favoriteFonts = JSON.parse(localStorage.getItem('dalal_fav_fonts') || '[]');

        // تحميل المفضلة عند بدء التشغيل
        function loadFavoriteFonts() {
            const favGroup = document.getElementById('fav-fonts-group');
            if (!favGroup) return;

            favGroup.innerHTML = '';

            if (favoriteFonts.length > 0) {
                favGroup.style.display = '';
                favoriteFonts.forEach(font => {
                    const opt = document.createElement('option');
                    opt.value = font.value;
                    opt.textContent = '⭐ ' + font.name;
                    opt.style.color = '#6366f1';
                    opt.style.fontWeight = 'bold';
                    favGroup.appendChild(opt);
                });
            } else {
                favGroup.style.display = 'none';
            }
        }

        // إضافة/إزالة خط من المفضلة
        function toggleFavoriteFont() {
            const select = document.getElementById('top-font-family');
            const currentValue = select.value;
            const currentText = select.options[select.selectedIndex]?.textContent || '';

            if (!currentValue || currentValue === '__ADD_CUSTOM_FONT__') {
                showInfoModal('اختر خطاً أولاً لإضافته للمفضلة', 'تنبيه', '⚠️');
                return;
            }

            const btn = document.getElementById('btn-fav-font');
            const existingIndex = favoriteFonts.findIndex(f => f.value === currentValue);

            if (existingIndex > -1) {
                // إزالة من المفضلة
                favoriteFonts.splice(existingIndex, 1);
                btn.textContent = '☆';
                btn.classList.remove('text-[#f59e0b]', 'border-[#f59e0b]');
                btn.classList.add('text-[#94a3b8]');
                showInfoModal('تم إزالة الخط من المفضلة', 'تم', '🗑️');
            } else {
                // إضافة للمفضلة
                const cleanName = currentText.replace(/^⭐\s*/, '').trim();
                favoriteFonts.push({ value: currentValue, name: cleanName });
                btn.textContent = '⭐';
                btn.classList.add('text-[#f59e0b]', 'border-[#f59e0b]');
                btn.classList.remove('text-[#94a3b8]');
                showInfoModal('تم إضافة الخط للمفضلة ⭐', 'تم', '⭐');
            }

            // حفظ في localStorage
            localStorage.setItem('dalal_fav_fonts', JSON.stringify(favoriteFonts));
            loadFavoriteFonts();
        }

        // تحديث زر المفضلة عند تغيير الخط
        function updateFavoriteButton(fontValue) {
            const btn = document.getElementById('btn-fav-font');
            if (!btn) return;

            const isFav = favoriteFonts.some(f => f.value === fontValue);
            if (isFav) {
                btn.textContent = '⭐';
                btn.classList.add('text-[#f59e0b]', 'border-[#f59e0b]');
                btn.classList.remove('text-[#94a3b8]');
            } else {
                btn.textContent = '☆';
                btn.classList.remove('text-[#f59e0b]', 'border-[#f59e0b]');
                btn.classList.add('text-[#94a3b8]');
            }
        }

        // دالة تطبيق لون النص مباشرة
        function applyTextColor(color) {
            if (!activeEl || !activeEl.classList.contains('text-layer')) return;

            // --- دعم التلوين الجزئي (Partial Selection) ---
            const selection = window.getSelection();
            if (selection.rangeCount > 0 && !selection.isCollapsed) {
                const range = selection.getRangeAt(0);
                if (activeEl.contains(range.commonAncestorContainer)) {
                    // تطبيق اللون على الجزء المحدد فقط
                    document.execCommand('styleWithCSS', false, true);
                    document.execCommand('foreColor', false, color);
                    return;
                }
            }

            const textDiv = activeEl.querySelector('.user-text');
            if (textDiv) {
                // إزالة التدرج إذا كان موجوداً
                textDiv.style.backgroundImage = '';
                textDiv.style.webkitBackgroundClip = '';
                textDiv.style.webkitTextFillColor = '';
                textDiv.style.backgroundClip = '';
                activeEl.removeAttribute('data-has-gradient');

                // تطبيق اللون الجديد
                textDiv.style.color = color;
                activeEl.style.color = color;

                // تحديث حقل اللون السريع
                const quickColor = document.getElementById('quick-color');
                if (quickColor) quickColor.value = color;

                // إعادة زر التدرج لحالته الطبيعية
                const btn = document.getElementById('btn-toggle-gradient');
                const settings = document.getElementById('floating-grad-settings');
                if (btn && settings) {
                    settings.classList.add('hidden');
                    settings.style.display = 'none';
                    btn.classList.remove('bg-indigo-100', 'text-indigo-700', 'border-indigo-300');
                    btn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
                    btn.innerHTML = '<i class="fas fa-fill-drip text-[8px]"></i> تدرج';
                }
            }
            saveState();
        }

        function handleFontSelection(selectEl) {
            const val = selectEl.value;
            if (val === '__ADD_CUSTOM_FONT__') {
                // فتح نافذة رفع الخط
                document.getElementById('custom-font-input').click();
                // إعادة القائمة للخط السابق
                setTimeout(() => {
                    if (activeEl) {
                        selectEl.value = activeEl.style.fontFamily || "'Cairo', sans-serif";
                    }
                }, 100);
            } else {
                updateStyle('fontFamily', val);
                updateFavoriteButton(val);
            }
        }

        async function handleCustomFontUpload(input) {
            if (!input.files || !input.files[0]) return;

            const file = input.files[0];
            const fontName = file.name.replace(/\.[^/.]+$/, "").replace(/[^a-zA-Z0-9\u0600-\u06FF]/g, '_');

            try {
                // قراءة الملف وتحويله لـ URL
                const fontUrl = URL.createObjectURL(file);

                // تسجيل الخط في المتصفح
                const newFont = new FontFace(fontName, `url(${fontUrl})`);
                await newFont.load();
                document.fonts.add(newFont);

                // إضافة الخط للقائمة إذا لم يكن موجوداً
                if (!customFonts.includes(fontName)) {
                    customFonts.push(fontName);

                    // إضافة الخط لقوائم الخطوط
                    const fontSelects = document.querySelectorAll('#top-font-family');
                    fontSelects.forEach(sel => {
                        // إيجاد خيار "إضافة خط مخصص" وإدراج قبله
                        const addOption = sel.querySelector('option[value="__ADD_CUSTOM_FONT__"]');
                        const separator = addOption ? addOption.previousElementSibling : null;

                        const newOption = document.createElement('option');
                        newOption.value = `'${fontName}', sans-serif`;
                        newOption.textContent = `✨ ${fontName} (مخصص)`;
                        newOption.style.color = '#10b981';
                        newOption.style.fontWeight = 'bold';

                        if (separator) {
                            sel.insertBefore(newOption, separator);
                        } else if (addOption) {
                            sel.insertBefore(newOption, addOption);
                        } else {
                            sel.appendChild(newOption);
                        }
                    });
                }

                // تطبيق الخط على العنصر المحدد
                if (activeEl) {
                    updateStyle('fontFamily', `'${fontName}', sans-serif`);
                    document.getElementById('top-font-family').value = `'${fontName}', sans-serif`;
                }

                showInfoModal(`تم إضافة الخط "${fontName}" بنجاح! 🎉`, 'نجاح', '✅');

            } catch (error) {
                console.error('Error loading font:', error);
                showInfoModal('فشل تحميل الخط. تأكد من أن الملف صالح.', 'خطأ', '❌');
            }

            input.value = ''; // إعادة تعيين الحقل
        }

        function updateStyle(prop, val) {
            if(!activeEl) return;

            // --- تعديل: دعم التلوين الجزئي عند استخدام لوحة الألوان الرئيسية ---
            if (prop === 'color' && activeEl.classList.contains('text-layer')) {
                const selection = window.getSelection();
                // Check if selection exists, is not empty, and intersects with activeEl
                if (selection && selection.rangeCount > 0 && !selection.isCollapsed) {
                    const range = selection.getRangeAt(0);
                    if (activeEl.contains(range.commonAncestorContainer) || activeEl.contains(range.startContainer)) {
                        document.execCommand('styleWithCSS', false, true);
                        document.execCommand('foreColor', false, val);

                        // Sync inputs but DON'T update the whole element style
                        const topTextColor = document.getElementById('top-text-color');
                        if (topTextColor) topTextColor.value = val;
                        const quickColor = document.getElementById('quick-color');
                        if (quickColor) quickColor.value = val;

                        saveState();
                        return; // Stop execution here for partial coloring
                    }
                }
            }
            // -----------------------------------------------------------------

            // تطبيق التغيير على العنصر الأساسي (الغلاف)
            activeEl.style[prop] = val;

            // إذا كنا نغير اللون ولم يكن هناك تحديد جزئي (أعلاه)، فهذا يعني أن المستخدم يريد تلوين النص بالكامل
            if (prop === 'color' && activeEl.classList.contains('text-layer')) {
                const textDiv = activeEl.querySelector('.user-text');
                if (textDiv) {
                    textDiv.style.color = val; // Force child to take color
                    // إزالة التلوين الداخلي السابق لتوحيد اللون
                    const spans = textDiv.querySelectorAll('span, font, b, i, u');
                    spans.forEach(span => {
                         // Reset inline color to inherit parent
                         if(span.style.color) span.style.color = '';
                         // If it's a font tag with color attr
                         if(span.tagName === 'FONT') span.removeAttribute('color');
                    });
                }
            }

            // إذا كنا نغير المحاذاة، نتأكد من تطبيقها على النص المقروء أيضاً إذا وجد
            if (prop === 'textAlign') {
                const userText = activeEl.querySelector('.user-text');
                if (userText) {
                    userText.style.textAlign = val; // Force consistency
                }
            }

            if(prop === 'fontSize') {
                const numVal = parseInt(val);
                document.getElementById('font-size').value = numVal;
                document.getElementById('font-size-input').value = numVal;
                document.getElementById('top-font-size').value = numVal;
                document.getElementById('top-font-size-input').value = numVal;
            }

            if(prop === 'color' || prop === 'borderColor') {
                document.getElementById('quick-color').value = val;
                // مزامنة لون النص في النافذة العائمة
                const topTextColor = document.getElementById('top-text-color');
                if (topTextColor) topTextColor.value = val;
                const surahLabel = activeEl.querySelector('.surah-label');
                if(surahLabel) surahLabel.style.color = val;
            }
            saveState();
        }

        // ========== دوال تلوين العناصر القابلة للتلوين ==========
        function updateColorableColor(color) {
            // يعمل على جميع الصور ما عدا اللي colorable = false
            if(!activeEl || activeEl.getAttribute('data-colorable') === 'false') return;
            if(!activeEl.classList.contains('image-layer')) return;

            const img = activeEl.querySelector('img');
            if(!img) return;

            // استخدام الصورة كـ mask والخلفية كلون
            const contentWrapper = activeEl.querySelector('.content-wrapper');
            if(contentWrapper) {
                contentWrapper.style.backgroundColor = color;
                contentWrapper.style.backgroundImage = 'none';
                contentWrapper.style.webkitMaskImage = `url(${img.src})`;
                contentWrapper.style.maskImage = `url(${img.src})`;
                contentWrapper.style.webkitMaskSize = '100% 100%';
                contentWrapper.style.maskSize = '100% 100%';
                contentWrapper.style.webkitMaskRepeat = 'no-repeat';
                contentWrapper.style.maskRepeat = 'no-repeat';
                contentWrapper.style.webkitMaskPosition = 'center';
                contentWrapper.style.maskPosition = 'center';
                img.style.opacity = '0';
                
                // تحديد أن الطبقة ملونة (للممحاة)
                activeEl.setAttribute('data-has-color', 'true');
            }
            saveState();
        }

        function updateColorableGradient() {
            // فقط تحديث preview - التطبيق الفعلي عند الضغط على زر تطبيق
        }

        function applyColorableGradient() {
            // يعمل على جميع الصور ما عدا اللي colorable = false
            if(!activeEl || activeEl.getAttribute('data-colorable') === 'false') return;
            if(!activeEl.classList.contains('image-layer')) return;

            const img = activeEl.querySelector('img');
            if(!img) return;

            const startColor = document.getElementById('colorable-grad-start').value;
            const endColor = document.getElementById('colorable-grad-end').value;

            // استخدام الصورة كـ mask والتدرج كخلفية
            const contentWrapper = activeEl.querySelector('.content-wrapper');
            if(contentWrapper) {
                contentWrapper.style.backgroundImage = `linear-gradient(to top, ${startColor}, ${endColor})`;
                contentWrapper.style.backgroundColor = 'transparent';
                contentWrapper.style.webkitMaskImage = `url(${img.src})`;
                contentWrapper.style.maskImage = `url(${img.src})`;
                contentWrapper.style.webkitMaskSize = '100% 100%';
                contentWrapper.style.maskSize = '100% 100%';
                contentWrapper.style.webkitMaskRepeat = 'no-repeat';
                contentWrapper.style.maskRepeat = 'no-repeat';
                contentWrapper.style.webkitMaskPosition = 'center';
                contentWrapper.style.maskPosition = 'center';
                img.style.opacity = '0';
            }
            saveState();
        }

        function resetColorableColor() {
            // يعمل على جميع الصور ما عدا اللي colorable = false
            if(!activeEl || activeEl.getAttribute('data-colorable') === 'false') return;
            if(!activeEl.classList.contains('image-layer')) return;

            // إزالة اللون والتدرج وإعادة الصورة
            const contentWrapper = activeEl.querySelector('.content-wrapper');
            const img = activeEl.querySelector('img');

            if(contentWrapper) {
                contentWrapper.style.backgroundColor = 'transparent';
                contentWrapper.style.backgroundImage = 'none';
                contentWrapper.style.webkitMaskImage = 'none';
                contentWrapper.style.maskImage = 'none';
            }
            if(img) {
                img.style.opacity = '1';
            }
            saveState();
        }

        // دالة تحديث شفافية الطبقة
        function updateLayerOpacity(val) {
            if(!activeEl) return;
            const opacity = val / 100;
            activeEl.style.opacity = opacity;
            document.getElementById('opacity-value').textContent = val + '%';
            saveState();
        }

        // دالة عرض النافذة الجميلة
        function showInfoModal(message, title = 'تنبيه', icon = '💡') {
            document.getElementById('info-modal-icon').textContent = icon;
            document.getElementById('info-modal-title').textContent = title;
            document.getElementById('info-modal-message').textContent = message;
            document.getElementById('info-modal').style.display = 'flex';
        }

        // دالة إغلاق النافذة الجميلة
        function closeInfoModal() {
            document.getElementById('info-modal').style.display = 'none';
        }
        
        // متغير لحفظ callback التأكيد
        let confirmCallback = null;
        
        // دالة عرض نافذة التأكيد الاحترافية
        function showConfirmModal(message, title = 'تأكيد', icon = '⚠️', onConfirm = null) {
            document.getElementById('confirm-modal-icon').textContent = icon;
            document.getElementById('confirm-modal-title').textContent = title;
            document.getElementById('confirm-modal-message').textContent = message;
            document.getElementById('confirm-modal').style.display = 'flex';
            confirmCallback = onConfirm;
            
            // إعداد زر التأكيد
            document.getElementById('confirm-modal-yes').onclick = function() {
                closeConfirmModal(true);
            };
        }
        
        // دالة إغلاق نافذة التأكيد
        function closeConfirmModal(confirmed) {
            document.getElementById('confirm-modal').style.display = 'none';
            if (confirmed && confirmCallback) {
                confirmCallback();
            }
            confirmCallback = null;
        }
        // دالة عرض نافذة تعليمية للأدوات الذكية عند الضغطة الواحدة
        function showSmartToolTutorial(toolType) {
            let title, icon, steps = [];
            
            if (toolType === 'lasso') {
                title = 'القص الذكي ✂️';
                icon = '✂️';
                steps = [
                    '1️⃣ اضغط مع الاستمرار على الماوس',
                    '2️⃣ ارسم شكلاً حول المنطقة المراد قصها',
                    '3️⃣ أكمل الشكل ثم ارفع إصبعك',
                    '🎯 سيتم قص المنطقة المحددة تلقائياً!'
                ];
            } else if (toolType === 'smartFill') {
                title = 'التلوين الذكي 🎨';
                icon = '🎨';
                steps = [
                    '1️⃣ اضغط مع الاستمرار على الماوس',
                    '2️⃣ ارسم شكلاً بالمنطقة المراد تلوينها',
                    '3️⃣ أكمل الشكل ثم ارفع إصبعك',
                    '🎯 سيتم تعبئة الشكل باللون المحدد!'
                ];
            } else if (toolType === 'smartEraser') {
                title = 'الممحاة الذكية 🧹';
                icon = '🧹';
                steps = [
                    '1️⃣ اضغط مع الاستمرار على الماوس',
                    '2️⃣ ارسم شكلاً حول المنطقة المراد مسحها',
                    '3️⃣ أكمل الشكل ثم ارفع إصبعك',
                    '🎯 سيتم مسح المنطقة المحددة تلقائياً!'
                ];
            }
            
            // إنشاء النافذة التعليمية الاحترافية
            const existingModal = document.getElementById('smart-tool-tutorial-modal');
            if (existingModal) existingModal.remove();
            
            const modal = document.createElement('div');
            modal.id = 'smart-tool-tutorial-modal';
            modal.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 100002;
                display: flex;
                align-items: flex-end;
                justify-content: center;
                pointer-events: none;
                animation: slideUp 0.4s ease;
            `;
            
            modal.innerHTML = `
                <style>
                    @keyframes slideUp { from { transform: translate(-50%, 50px); opacity: 0; } to { transform: translate(-50%, 0); opacity: 1; } }
                </style>
                <div style="
                    background: linear-gradient(145deg, #1e293b, #0f172a);
                    border-radius: 16px;
                    padding: 16px;
                    width: 280px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(99, 102, 241, 0.2);
                    position: relative;
                    overflow: hidden;
                    pointer-events: auto;
                ">
                    <!-- خلفية زخرفية -->
                    <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.05; background-image: radial-gradient(#6366f1 1px, transparent 1px); background-size: 20px 20px; pointer-events: none;"></div>
                    
                    <!-- الأيقونة والعنوان -->
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <div style="
                            width: 36px;
                            height: 36px;
                            background: linear-gradient(135deg, #6366f1, #8b5cf6);
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 18px;
                            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
                        ">${icon}</div>
                        <div>
                            <h3 style="
                                color: white;
                                font-size: 15px;
                                font-weight: 700;
                                margin: 0;
                            ">${title}</h3>
                            <p style="color: #94a3b8; font-size: 11px; margin: 2px 0 0 0;">تابع الخطوات التالية للبدء</p>
                        </div>
                    </div>
                    
                    <!-- رسم توضيحي متحرك (منقط) -->
                    <div style="
                        background: rgba(99, 102, 241, 0.05);
                        border: 1px dashed rgba(99, 102, 241, 0.2);
                        border-radius: 8px;
                        padding: 8px;
                        text-align: center;
                        margin-bottom: 12px;
                        height: 50px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <svg width="150" height="40" viewBox="0 0 200 80" style="overflow: visible;">
                            <defs>
                                <linearGradient id="drawGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
                                    <stop offset="100%" style="stop-color:#ec4899;stop-opacity:1" />
                                </linearGradient>
                                <mask id="dashedMask">
                                    <path d="M30,60 Q70,0 120,20 T170,40" 
                                          fill="none" 
                                          stroke="white" 
                                          stroke-width="8" 
                                          stroke-dasharray="300"
                                          stroke-dashoffset="300">
                                        <animate attributeName="stroke-dashoffset" from="300" to="0" dur="2s" repeatCount="indefinite" />
                                    </path>
                                </mask>
                            </defs>
                            
                            <!-- دائرة البداية المجوفة -->
                            <circle cx="30" cy="60" r="5" fill="#1e293b" stroke="#6366f1" stroke-width="2" />
                            
                            <!-- الخط المنقط (يظهر باستخدام القناع) -->
                            <path d="M30,60 Q70,0 120,20 T170,40" 
                                fill="none" 
                                stroke="url(#drawGrad)" 
                                stroke-width="4" 
                                stroke-linecap="round" 
                                stroke-dasharray="8 8" 
                                mask="url(#dashedMask)"
                            />
                        </svg>
                    </div>
                    
                    <!-- الخطوات -->
                    <div style="background: rgba(0, 0, 0, 0.2); border-radius: 8px; padding: 10px; margin-bottom: 12px;">
                        ${steps.map((step, i) => `
                            <div style="
                                display: flex;
                                align-items: flex-start;
                                gap: 8px;
                                margin-bottom: ${i < steps.length - 1 ? '6px' : '0'};
                            ">
                                <span style="
                                    color: ${i === steps.length - 1 ? '#10b981' : '#cbd5e1'};
                                    font-size: 11px;
                                    line-height: 1.4;
                                    ${i === steps.length - 1 ? 'font-weight: 600;' : ''}
                                ">${step}</span>
                            </div>
                        `).join('')}
                    </div>
                    
                    <button onclick="closeSmartToolTutorial()" style="
                        width: 100%;
                        background: linear-gradient(135deg, #6366f1, #8b5cf6);
                        color: white;
                        border: none;
                        padding: 8px;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 12px;
                        cursor: pointer;
                        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
                        transition: all 0.2s;
                    " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                       فهمت، إغلاق
                    </button>
                    
                    <!-- زر إغلاق صغير في الزاوية -->
                    <button onclick="closeSmartToolTutorial()" style="
                        position: absolute;
                        top: 8px;
                        right: 8px;
                        background: transparent;
                        border: none;
                        color: #64748b;
                        cursor: pointer;
                        padding: 4px;
                        border-radius: 50%;
                        font-size: 14px;
                    " onmouseover="this.style.backgroundColor='rgba(255,255,255,0.1)';this.style.color='#ef4444'" onmouseout="this.style.backgroundColor='transparent';this.style.color='#64748b'">
                        ✕
                    </button>
                </div>
            `;
            document.body.appendChild(modal);
            modal.addEventListener('mousedown', (e) => { e.stopPropagation(); });
            modal.addEventListener('click', (e) => { e.stopPropagation(); });
            modal.addEventListener('touchstart', (e) => { e.stopPropagation(); }, {passive: false});
        }
        function closeSmartToolTutorial() {
            const modal = document.getElementById('smart-tool-tutorial-modal');
            if (modal) modal.remove();
        }


        function removeEl(el) {
            el.remove();
            deselect();
            saveState();
            // تحديث قائمة الطبقات فوراً بعد الحذف
            if (typeof updateLayersList === 'function') {
                updateLayersList();
            }
        }

        function duplicateElement(el) {
            // عمل نسخة من العنصر
            const clone = el.cloneNode(true);

            // تحريك النسخة قليلاً لإظهار أنها جديدة
            const currentLeft = parseFloat(el.style.left) || 0;
            const currentTop = parseFloat(el.style.top) || 0;
            clone.style.left = (currentLeft + 20) + 'px';
            clone.style.top = (currentTop + 20) + 'px';

            // إضافة النسخة إلى الـ card
            const card = document.getElementById('card');
            card.appendChild(clone);

            // إعادة تفعيل الأحداث للعنصر الجديد
            rebindEvents();

            // تسجيل التغيير
            saveState();
        }

        function updateControlsPosition(el) {
            const angleDeg = parseFloat(el.getAttribute('data-rotate')) || 0;
            const angleRad = angleDeg * Math.PI / 180;

            const w = el.offsetWidth;
            const h = el.offsetHeight;

            // Visual Dimensions
            const cos = Math.abs(Math.cos(angleRad));
            const sin = Math.abs(Math.sin(angleRad));
            const vw = w * cos + h * sin;
            const vh = w * sin + h * cos;

            const buttons = [
                { el: el.querySelector('.delete-btn'), defaultX: -18 },
                { el: el.querySelector('.duplicate-btn'), defaultX: 28 },
                { el: el.querySelector('.rotate-btn'), defaultX: 74 },
                { el: el.querySelector('.layer-up-btn'), defaultX: 120 },
                { el: el.querySelector('.layer-down-btn'), defaultX: 166 }
            ];

            const btnRadius = 18;
            const btnCenterY_rel_top = -32; // -50 (top) + 18 (radius)

            const cosA = Math.cos(angleRad);
            const sinA = Math.sin(angleRad);

            buttons.forEach(item => {
                if(!item.el) return;

                const gx = -vw/2 + item.defaultX + btnRadius;
                const gy = -vh/2 + btnCenterY_rel_top;

                const lx = gx * cosA + gy * sinA;
                const ly = -gx * sinA + gy * cosA;

                item.el.style.left = `calc(50% + ${lx}px)`;
                item.el.style.top = `calc(50% + ${ly}px)`;
                item.el.style.bottom = 'auto';
                item.el.style.right = 'auto';
                item.el.style.transform = `translate(-50%, -50%) rotate(${-angleDeg}deg)`;
            });

            const moveHandle = el.querySelector('.move-handle');
            if(moveHandle) {
                const gx = 0;
                const gy = -vh/2 - 30; // -30 is center of handle (-50 top + 20 half height)

                const lx = gx * cosA + gy * sinA;
                const ly = -gx * sinA + gy * cosA;

                moveHandle.style.left = `calc(50% + ${lx}px)`;
                moveHandle.style.top = `calc(50% + ${ly}px)`;
                moveHandle.style.bottom = 'auto';
                moveHandle.style.right = 'auto';
                moveHandle.style.transform = `translate(-50%, -50%) rotate(${-angleDeg}deg)`;
            }
        }

        function rotateElement(el) {
            // الحصول على التدوير الحالي أو 0
            const currentRotate = parseFloat(el.getAttribute('data-rotate')) || 0;
            // إضافة 90 درجة
            const newRotate = (currentRotate + 90) % 360;

            // تطبيق التدوير مع الحفاظ على التمركز
            el.style.transform = `translate(-50%, -50%) rotate(${newRotate}deg)`;
            el.setAttribute('data-rotate', newRotate);

            updateControlsPosition(el);

            // تسجيل التغيير
            saveState();
        }

        // دالة إرسال الطبقة للأمام
        function bringToFront(el) {
            if (!el) return;
            const card = document.getElementById('card');
            const layers = card.querySelectorAll('.draggable-el:not(.bg-image)');
            let maxZ = 30;
            layers.forEach(layer => {
                const z = parseInt(layer.style.zIndex) || 0;
                if (z > maxZ) maxZ = z;
            });
            el.style.zIndex = maxZ + 1;
            saveState();
        }

        // دالة إرسال الطبقة للخلف
        function sendToBack(el) {
            if (!el) return;
            const card = document.getElementById('card');
            const layers = card.querySelectorAll('.draggable-el:not(.bg-image)');
            let minZ = 30;
            layers.forEach(layer => {
                const z = parseInt(layer.style.zIndex) || 30;
                if (z < minZ) minZ = z;
            });
            el.style.zIndex = Math.max(1, minZ - 1);
            saveState();
        }

        function deleteActive() {
            if(activeEl) removeEl(activeEl);
        }

        // دالة مزامنة إدخالات التدرج بين النافذة العائمة والإعدادات الرئيسية
        function syncGradientInputs(type, value) {
            if (type === 'start') {
                document.getElementById('grad-start-color').value = value;
            } else if (type === 'end') {
                document.getElementById('grad-end-color').value = value;
            } else if (type === 'angle') {
                document.getElementById('grad-angle').value = value;
            }
        }

        // دالة مزامنة من الإعدادات الرئيسية للنافذة العائمة
        function syncFloatGradientInputs(type, value) {
            const floatStart = document.getElementById('float-grad-start');
            const floatEnd = document.getElementById('float-grad-end');
            const floatAngle = document.getElementById('float-grad-angle');
            if (type === 'start' && floatStart) floatStart.value = value;
            else if (type === 'end' && floatEnd) floatEnd.value = value;
            else if (type === 'angle' && floatAngle) floatAngle.value = value;
        }

        function updateElementGradient() {
            if(!activeEl) return;

            const color1 = document.getElementById('grad-start-color').value;
            const color2 = document.getElementById('grad-end-color').value;
            const angle = document.getElementById('grad-angle').value;
            const opacityEl = document.getElementById('grad-opacity');
            const opacity = opacityEl ? opacityEl.value : '1';

            // مزامنة مع النافذة العائمة
            syncFloatGradientInputs('start', color1);
            syncFloatGradientInputs('end', color2);
            syncFloatGradientInputs('angle', angle);

            // Helper to convert hex to rgba
            const hexToRgba = (hex, alpha) => {
                const r = parseInt(hex.slice(1, 3), 16);
                const g = parseInt(hex.slice(3, 5), 16);
                const b = parseInt(hex.slice(5, 7), 16);
                return `rgba(${r}, ${g}, ${b}, ${alpha})`;
            };

            const rgba1 = hexToRgba(color1, opacity);
            const rgba2 = hexToRgba(color2, opacity);

            const gradient = `linear-gradient(${angle}deg, ${rgba1}, ${rgba2})`;

            if(activeEl.classList.contains('text-layer')) {
                // Apply gradient ONLY to the inner text div, not the wrapper
                const textDiv = activeEl.querySelector('.user-text');
                if(textDiv) {
                    if (!activeEl.hasAttribute('data-has-gradient')) {
                        activeEl.setAttribute('data-prev-color', textDiv.style.color);
                    }

                    textDiv.style.backgroundImage = gradient;
                    textDiv.style.webkitBackgroundClip = 'text';
                    textDiv.style.webkitTextFillColor = 'transparent';
                    textDiv.style.backgroundClip = 'text';
                    textDiv.style.color = 'transparent';
                    textDiv.style.display = 'inline-block'; // Important for clip to work
                    // تم إزالة pointerEvents: none للسماح بالتعديل

                    // Reset wrapper styles to prevent controls glitch
                    activeEl.style.backgroundImage = '';
                    activeEl.style.webkitBackgroundClip = '';
                    activeEl.style.webkitTextFillColor = '';
                     // Keep wrapper color as transparent wasn't good for controls
                    activeEl.style.color = '';
                }
            } else if(activeEl.classList.contains('image-layer') && activeEl.querySelector('img')) {
                // تفعيل التدرج للصور باستخدام Mask
                const img = activeEl.querySelector('img');
                const contentWrapper = activeEl.querySelector('.content-wrapper') || activeEl;

                // حفظ الحالة السابقة
                if (!activeEl.hasAttribute('data-has-gradient')) {
                     activeEl.setAttribute('data-prev-opacity', img.style.opacity || '1');
                }

                // تطبيق التدرج كخلفية
                contentWrapper.style.backgroundImage = gradient;
                contentWrapper.style.backgroundColor = 'transparent';

                // استخدام الصورة كـ Mask
                contentWrapper.style.webkitMaskImage = `url(${img.src})`;
                contentWrapper.style.maskImage = `url(${img.src})`;

                contentWrapper.style.webkitMaskSize = '100% 100%';
                contentWrapper.style.maskSize = '100% 100%';
                contentWrapper.style.webkitMaskRepeat = 'no-repeat';
                contentWrapper.style.maskRepeat = 'no-repeat';
                contentWrapper.style.webkitMaskPosition = 'center';
                contentWrapper.style.maskPosition = 'center';

                // إخفاء الصورة الأصلية
                img.style.opacity = '0';

            } else {
                if (!activeEl.hasAttribute('data-has-gradient')) {
                     let bg = activeEl.style.backgroundColor;
                     // التأكد من حفظ اللون الأصلي حتى لو لم يكن محدداً في style
                     if (!bg || bg === '') {
                         bg = window.getComputedStyle(activeEl).backgroundColor;
                     }
                     activeEl.setAttribute('data-prev-bg', bg);
                }
                activeEl.style.backgroundImage = gradient;
                activeEl.style.backgroundColor = 'transparent';
            }

            activeEl.setAttribute('data-has-gradient', 'true');
            activeEl.setAttribute('data-grad-start', color1);
            activeEl.setAttribute('data-grad-end', color2);
            activeEl.setAttribute('data-grad-angle', angle);
            activeEl.setAttribute('data-grad-opacity', opacity);
            saveState();
        }

        // دالة إزالة التدرج من النص
        function removeTextGradient() {
            if(!activeEl) return;

            if(activeEl.classList.contains('text-layer')) {
                const textDiv = activeEl.querySelector('.user-text');
                if(textDiv) {
                    textDiv.style.backgroundImage = 'none';
                    textDiv.style.webkitBackgroundClip = 'unset';
                    textDiv.style.webkitTextFillColor = 'unset';
                    textDiv.style.backgroundClip = 'unset';

                    const prevColor = activeEl.getAttribute('data-prev-color');
                    textDiv.style.color = prevColor && prevColor !== 'transparent' ? prevColor : '#1e293b';
                    textDiv.style.display = 'block';
                }
            } else if (activeEl.classList.contains('image-layer')) {
                const img = activeEl.querySelector('img');
                const contentWrapper = activeEl.querySelector('.content-wrapper') || activeEl;

                contentWrapper.style.backgroundImage = 'none';
                contentWrapper.style.webkitMaskImage = 'none';
                contentWrapper.style.maskImage = 'none';

                if (img) img.style.opacity = '1';
                activeEl.style.backgroundColor = 'transparent';
                if(contentWrapper !== activeEl) contentWrapper.style.backgroundColor = 'transparent';

            } else {
                activeEl.style.backgroundImage = 'none';

                const prevBg = activeEl.getAttribute('data-prev-bg');
                if (prevBg && prevBg !== 'transparent' && prevBg !== 'rgba(0, 0, 0, 0)') {
                    activeEl.style.backgroundColor = prevBg;
                } else {
                    // إذا لم يكن هناك لون محفوظ، نحافظ على الشفافية فقط إذا كان الإطار شفافاً بالأصل
                    // ولكن لتفادي مشكلة الاختفاء، إذا كان العنصر إطاراً له حدود، فالشفافية مقبولة
                    // أما إذا كان شكلاً (بدون حدود تقريباً) فيجب أن يكون له لون
                    const borderWidth = parseFloat(activeEl.style.borderWidth) || 0;
                    if (borderWidth > 0) {
                        activeEl.style.backgroundColor = 'transparent';
                    } else {
                         // افتراضي للأشكال إذا فقدنا اللون
                        activeEl.style.backgroundColor = '#6366f1';
                    }
                }
            }

            activeEl.removeAttribute('data-has-gradient');
            activeEl.removeAttribute('data-grad-start');
            activeEl.removeAttribute('data-grad-end');
            activeEl.removeAttribute('data-grad-angle');
            activeEl.removeAttribute('data-grad-opacity');
            // تنظيف السمات المؤقتة
            activeEl.removeAttribute('data-prev-bg');
            activeEl.removeAttribute('data-prev-color');

            saveState();
        }

        function toggleGradient() {
            // منع تفعيل التدرج على الخلفية إذا لم يتم تحديد عنصر
            if (!activeEl) {
                // عرض رسالة جميلة بدلاً من التنبيه العادي
                showInfoModal('يرجى تحديد عنصر (شكل أو نص) أولاً لتفعيل التدرج عليه.', 'تنبيه', '🎨');
                return;
            }

            const controls = document.getElementById('grad-controls');
            const btn = document.getElementById('btn-grad');
            const globalInputs = document.getElementById('global-grad-inputs');
            const elementInputs = document.getElementById('element-grad-inputs');

            // منطق تفعيل التدرج للعنصر المحدد فقط
            // نتحقق مما إذا كان تدرج العنصر مفعلاً حالياً
            const isShowingElementGrad = controls.classList.contains('active') && !elementInputs.classList.contains('hidden');

            if (isShowingElementGrad) {
                // إيقاف التدرج
                controls.classList.remove('active');
                btn.classList.remove('bg-[#6366f1]', 'text-white');
                btn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');

                // إزالة التدرج عند الإغلاق
                removeTextGradient();

                // إخفاء لوحة إعدادات العنصر وإظهار العامة
                elementInputs.classList.add('hidden');
                elementInputs.classList.remove('flex');
                globalInputs.classList.remove('hidden');
                globalInputs.classList.add('flex');
            } else {
                // تشغيل التدرج
                controls.classList.add('active');
                btn.classList.remove('bg-[#f1f5f9]', 'text-[#475569]');
                btn.classList.add('bg-[#6366f1]', 'text-white');

                // التأكد من ظهور إعدادات العنصر وإخفاء إعدادات الخلفية (Global)
                globalInputs.classList.add('hidden');
                globalInputs.classList.remove('flex');
                elementInputs.classList.remove('hidden');
                elementInputs.classList.add('flex');

                // تطبيق تدرج افتراضي إذا لم يكن للعنصر تدرج
                if(!activeEl.hasAttribute('data-has-gradient')) {
                    updateElementGradient();
                }
            }
        }

        function updateGlobalGradient() {
            const grad = document.getElementById('card-gradient');
            if(!grad) return;

            const startColor = document.getElementById('global-grad-start').value;
            const endColor = document.getElementById('global-grad-end').value;
            const opacity = document.getElementById('global-grad-opacity').value;
            const height = document.getElementById('global-grad-height').value;

            // Helper to convert hex to rgba
            const hexToRgba = (hex, alpha) => {
                const r = parseInt(hex.slice(1, 3), 16);
                const g = parseInt(hex.slice(3, 5), 16);
                const b = parseInt(hex.slice(5, 7), 16);
                return `rgba(${r}, ${g}, ${b}, ${alpha})`;
            };

            // Apply gradient using the chosen colors and opacity
            // Using "to top" to match previous behavior (Bottom -> Top)
            // Color 1 is start (Bottom), Color 2 is end (Top)
            const c1 = hexToRgba(startColor, opacity);
            const c2 = hexToRgba(endColor, opacity);

            grad.style.background = `linear-gradient(to top, ${c1}, ${c2})`;
            grad.style.opacity = '1'; // Opacity is handled in rgba
            grad.style.height = height + '%';
        }

        // متغير لحفظ لون الخلفية السابق
        let savedBgColor = '#ffffff';

        function setCardBackgroundColor(color) {
            isTransparent = false;
            savedBgColor = color; // حفظ اللون
            const card = document.getElementById('card');
            card.style.backgroundColor = color;
            card.classList.remove('transparent-pattern');
            const preview = document.getElementById('bg-color-preview');
            if(preview) preview.style.backgroundColor = color;
            // إعادة مظهر زر الشفافية للوضع العادي
            const btn = document.getElementById('btn-transparent');
            if (btn) {
                btn.classList.remove('bg-[#6366f1]', 'text-white');
                btn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
            }
            saveState();
        }

        function setCardTransparent() {
            isTransparent = true;
            const card = document.getElementById('card');
            card.style.backgroundColor = 'transparent';
            card.classList.add('transparent-pattern');
            // تحديث مظهر الزر
            const btn = document.getElementById('btn-transparent');
            if (btn) {
                btn.classList.add('bg-[#6366f1]', 'text-white');
                btn.classList.remove('bg-[#f1f5f9]', 'text-[#475569]');
            }
            saveState();
        }

        // دالة التبديل بين الشفافية والخلفية العادية
        function toggleTransparentMode() {
            const card = document.getElementById('card');
            if (isTransparent) {
                // إعادة اللون السابق
                setCardBackgroundColor(savedBgColor);
            } else {
                // تفعيل الشفافية
                setCardTransparent();
            }
        }

        function setCardSize(w, h) {
            const card = document.getElementById('card');
            // تعيين المقاس بدقة - بدون أي انضغاط أو توسع
            card.style.width = w + 'px';
            card.style.height = h + 'px';
            card.style.minWidth = w + 'px';
            card.style.maxWidth = w + 'px';
            card.style.minHeight = h + 'px';
            card.style.maxHeight = h + 'px';

            // حفظ المقاس في data attribute للطباعة
            card.setAttribute('data-card-width', w);
            card.setAttribute('data-card-height', h);

            // حساب zoom تلقائي للعرض في منطقة المعاينة
            const previewArea = document.querySelector('.preview-area');
            const maxWidth = previewArea.offsetWidth - 100; // مساحة إضافية للمساطر
            const maxHeight = previewArea.offsetHeight - 100; // مساحة إضافية للمساطر

            const zoomByWidth = (maxWidth / w) * 100;
            const zoomByHeight = (maxHeight / h) * 100;
            const autoZoom = Math.min(zoomByWidth, zoomByHeight, 200); // حد أقصى 200%

            // تطبيق الـ zoom الأمثل
            const optimalZoom = Math.max(25, Math.min(autoZoom, 200));
            setCustomZoom(optimalZoom);

            // تحديث عرض المقاس على الشاشة
            const displayEl = document.getElementById('size-display');
            if (displayEl) {
                const cmW = (w / DPI_RATIO).toFixed(2);
                const cmH = (h / DPI_RATIO).toFixed(2);
                displayEl.textContent = `${formatNumberWithSeparators(w)} × ${formatNumberWithSeparators(h)} px (${cmW} × ${cmH} سم)`;
            }

            // رسم المسطرة
            drawRulers(w, h);
        }

        // دالة رسم المسطرة
        function drawRulers(w, h) {
            const rulerH = document.getElementById('ruler-h');
            const rulerV = document.getElementById('ruler-v');

            if(!rulerH || !rulerV) return;

            rulerH.innerHTML = '';
            rulerV.innerHTML = '';

            const cmW = Math.ceil(w / DPI_RATIO);
            const cmH = Math.ceil(h / DPI_RATIO);

            // Horizontal Ruler
            for (let i = 0; i <= cmW; i++) {
                const leftPos = i * DPI_RATIO;
                if(leftPos > w) break;

                const tick = document.createElement('div');
                tick.className = 'tick';
                tick.style.left = leftPos + 'px';
                tick.style.bottom = '0';
                tick.style.width = '1px';
                tick.style.height = '100%';

                const num = document.createElement('span');
                num.className = 'tick-num';
                num.innerText = i;
                num.style.left = (leftPos + 4) + 'px'; // offset slightly
                num.style.bottom = '4px';

                rulerH.appendChild(tick);
                rulerH.appendChild(num);
            }

            // Vertical Ruler
            for (let i = 0; i <= cmH; i++) {
                const topPos = i * DPI_RATIO;
                if(topPos > h) break;

                const tick = document.createElement('div');
                tick.className = 'tick';
                tick.style.top = topPos + 'px';
                tick.style.left = '0';
                tick.style.height = '1px';
                tick.style.width = '100%';

                const num = document.createElement('span');
                num.className = 'tick-num';
                num.innerText = i;
                num.style.top = (topPos + 4) + 'px';
                num.style.left = '4px';

                rulerV.appendChild(tick);
                rulerV.appendChild(num);
            }
        }

        function setCustomZoom(zoomValue) {
            currentZoom = Math.max(25, Math.min(zoomValue, 200)); // بين 25% و 200%
            const zoomDecimal = currentZoom / 100;

            document.documentElement.style.setProperty('--card-zoom', zoomDecimal);

            // تحديث عرض النسبة
            const displayEl = document.getElementById('zoom-display');
            if (displayEl) {
                displayEl.textContent = `${Math.round(currentZoom)}%`;
            }

            // تحديث قيمة الـ slider
            const slider = document.getElementById('zoom-slider');
            if (slider) {
                slider.value = currentZoom;
            }

            saveState();
        }

        function applyCustomSizeSimple() {
            const wInput = document.getElementById('custom-width');
            const hInput = document.getElementById('custom-height');

            let widthCm = parseFloat(wInput.value);
            let heightCm = parseFloat(hInput.value);

            if (!widthCm || !heightCm || widthCm <= 0 || heightCm <= 0) {
                showInfoModal('الرجاء إدخال قيم صحيحة للعرض والارتفاع', 'تنبيه', '⚠️');
                return;
            }

            // تحويل السنتيمتر إلى بكسل بدقة (1 سم = 118.11 بكسل @ 300 DPI)
            const widthPx = Math.round(widthCm * DPI_RATIO);
            const heightPx = Math.round(heightCm * DPI_RATIO);

            // --- منطق تغيير حجم المحتوى (Scaling) ---
            const card = document.getElementById('card');
            // نستخدم style.width ونزيل 'px' لأنه أدق، أو نستخدم offsetWidth كبديل
            let oldW = parseFloat(card.style.width) || card.offsetWidth;
            let oldH = parseFloat(card.style.height) || card.offsetHeight;

            // تجنب القسمة على صفر أو القيم غير المنطقية
            if (oldW && oldH && oldW > 0 && oldH > 0) {
                const scaleX = widthPx / oldW;
                const scaleY = heightPx / oldH;

                // إذا كان الفرق صغيرا جداً، لا داعي للتغيير
                if (Math.abs(widthPx - oldW) > 1 || Math.abs(heightPx - oldH) > 1) {

                    const elements = card.querySelectorAll('.draggable-el');
                    elements.forEach(el => {
                        if (el.classList.contains('bg-image')) return; // الخلفيات تتغير تلقائياً

                        // تعديل الموقع (Left, Top)
                        // نعتمد على style.left لأنه يمثل القيمة المثبتة بـ px
                        if (el.style.left) {
                            // تنظيف القيمة من px
                            const currentLeft = parseFloat(el.style.left);
                            if (!isNaN(currentLeft)) {
                                el.style.left = (currentLeft * scaleX) + 'px';
                            }
                        }

                        if (el.style.top) {
                            const currentTop = parseFloat(el.style.top);
                            if (!isNaN(currentTop)) {
                                el.style.top = (currentTop * scaleY) + 'px';
                            }
                        }

                        // تعديل الحجم (Width, Height) إذا كان بـ px
                        if (el.style.width && el.style.width.endsWith('px')) {
                             const currentW = parseFloat(el.style.width);
                             if (!isNaN(currentW)) {
                                 el.style.width = (currentW * scaleX) + 'px';
                             }
                        }

                        if (el.style.height && el.style.height.endsWith('px')) {
                             const currentH = parseFloat(el.style.height);
                             if (!isNaN(currentH)) {
                                 el.style.height = (currentH * scaleY) + 'px';
                             }
                        }

                        // تعديل الخطوط (Font Size)
                        if (el.style.fontSize && el.style.fontSize.endsWith('px')) {
                             const currentFS = parseFloat(el.style.fontSize);
                             if (!isNaN(currentFS)) {
                                 // نستخدم scaleX كمقياس أساسي للنص للحفاظ على تناسقه
                                 el.style.fontSize = (currentFS * scaleX) + 'px';
                             }
                        }

                        // تعديل الحدود (Borders)
                        if (el.style.borderWidth && el.style.borderWidth.endsWith('px')) {
                             const currentBW = parseFloat(el.style.borderWidth);
                             if (!isNaN(currentBW)) {
                                 el.style.borderWidth = (currentBW * scaleX) + 'px';
                             }
                        }
                         if (el.style.borderRadius && el.style.borderRadius.endsWith('px')) {
                             const currentBR = parseFloat(el.style.borderRadius);
                             if (!isNaN(currentBR)) {
                                 el.style.borderRadius = (currentBR * scaleX) + 'px';
                             }
                        }
                    });
                }
            }
            // ----------------------------------------

            setCardSize(widthPx, heightPx);
            saveState();
        }

        function rgbToHex(rgb) {
            if(!rgb || rgb === 'transparent') return '#000000';
            if(rgb.startsWith('#')) return rgb;
            try {
                return '#' + rgb.match(/\d+/g).map(x => (+x).toString(16).padStart(2, '0')).join('');
            } catch(e) { return '#000000'; }
        }

        function downloadImage() {
            const img = document.getElementById('save-img');
            const link = document.createElement('a');
            link.href = img.src;
            // Generate random number for filename
            const randomNum = Math.floor(Math.random() * 1000000);
            link.download = `template_${randomNum}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function printDesignDirect() {
            // طباعة فورية - نفس ملف PDF بالضبط الذي يتم تحميله
            const imgData = document.getElementById('save-img').src;
            
            if (!imgData || imgData === '') {
                showInfoModal('⚠️ انتظر', 'يرجى الانتظار حتى يتم تحميل المعاينة');
                return;
            }
            
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF('p', 'mm', 'a4');
            const width = pdf.internal.pageSize.getWidth();
            const height = pdf.internal.pageSize.getHeight();
            
            const img = new Image();
            img.onload = function() {
                const imgWidth = img.width;
                const imgHeight = img.height;
                const imgAspectRatio = imgWidth / imgHeight;
                const pageAspectRatio = width / height;
                
                let finalWidth = width;
                let finalHeight = height;
                
                if(imgAspectRatio > pageAspectRatio) {
                    finalHeight = width / imgAspectRatio;
                } else {
                    finalWidth = height * imgAspectRatio;
                }
                
                const x = (width - finalWidth) / 2;
                const y = (height - finalHeight) / 2;
                
                pdf.addImage(imgData, 'PNG', x, y, finalWidth, finalHeight);
                
                // فتح PDF مباشرة للطباعة - نفس الملف بالضبط
                const pdfDataUri = pdf.output('bloburl');
                window.open(pdfDataUri, '_blank');
            };
            img.src = imgData;
        }

        // ===== دوال التحديد والحذف =====

        // ===== دوال الاستيراد والتحميل =====
        function exportTemplates() {
            const templates = getTemplates();
            if (templates.length === 0) {
                alert('⚠️ لا توجد قوالب لتحميلها!');
                return;
            }

            // إنشاء ملف JSON
            const dataStr = JSON.stringify(templates, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);

            // إنشاء رابط التحميل
            const link = document.createElement('a');
            link.href = url;
            link.download = `templates_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            alert('✅ تم تحميل القوالب بنجاح!');
        }

        function importTemplates() {
            // إنشاء input لاختيار الملف
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.style.display = 'none';

            input.onchange = (e) => {
                const file = e.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = (event) => {
                    try {
                        let importedTemplates = JSON.parse(event.target.result);

                        // معالجة حالة أن يكون الملف يحتوي على كائن واحد بدلاً من مصفوفة
                        if (!Array.isArray(importedTemplates)) {
                            // إذا كان كائن واحد، حوله إلى مصفوفة
                            if (typeof importedTemplates === 'object' && importedTemplates !== null) {
                                // تحقق إذا كان الكائن يحتوي على خاصية "templates"
                                if (Array.isArray(importedTemplates.templates)) {
                                    importedTemplates = importedTemplates.templates;
                                } else {
                                    importedTemplates = [importedTemplates];
                                }
                            } else {
                                alert('❌ صيغة الملف غير صحيحة! يجب أن يكون مصفوفة أو كائن يحتوي على مصفوفة.');
                                return;
                            }
                        }

                        // فلترة القوالب الفارغة أو غير الصحيحة
                        importedTemplates = importedTemplates.filter(t => t && typeof t === 'object');

                        if (importedTemplates.length === 0) {
                            alert('❌ لا توجد قوالب صحيحة في الملف!');
                            return;
                        }

                        // سؤال المستخدم
                        const currentTemplates = getTemplates();
                        let message = `سيتم استيراد ${importedTemplates.length} قالب.\n\n`;

                        if (currentTemplates.length > 0) {
                            message += 'هل تريد:\n✅ دمج القوالب مع الموجود\n❌ استبدال جميع القوالب';

                            if (confirm(message)) {
                                // دمج
                                const merged = [...currentTemplates, ...importedTemplates];
                                // إزالة التكرارات بناءً على الاسم
                                const uniqueTemplates = [];
                                const seen = new Set();
                                merged.forEach(t => {
                                    if (!seen.has(t.name)) {
                                        seen.add(t.name);
                                        uniqueTemplates.push(t);
                                    }
                                });

                                if (uniqueTemplates.length > MAX_TEMPLATES) {
                                    alert(`⚠️ سيتم حفظ أول ${MAX_TEMPLATES} قالب فقط (الحد الأقصى)`);
                                    saveTemplates(uniqueTemplates.slice(0, MAX_TEMPLATES));
                                } else {
                                    saveTemplates(uniqueTemplates);
                                }
                            } else {
                                // استبدال
                                if (importedTemplates.length > MAX_TEMPLATES) {
                                    alert(`⚠️ سيتم حفظ أول ${MAX_TEMPLATES} قالب فقط (الحد الأقصى)`);
                                    saveTemplates(importedTemplates.slice(0, MAX_TEMPLATES));
                                } else {
                                    saveTemplates(importedTemplates);
                                }
                            }
                        } else {
                            // لا توجد قوالب موجودة، استورد مباشرة
                            if (importedTemplates.length > MAX_TEMPLATES) {
                                alert(`⚠️ سيتم حفظ أول ${MAX_TEMPLATES} قالب فقط (الحد الأقصى)`);
                                saveTemplates(importedTemplates.slice(0, MAX_TEMPLATES));
                            } else {
                                saveTemplates(importedTemplates);
                            }
                        }

                        alert(`✅ تم استيراد ${importedTemplates.length} قالب بنجاح!`);
                    } catch(error) {
                        alert('❌ خطأ في قراءة الملف!\n' + error.message);
                        console.error('استيراد خطأ:', error);
                    }
                };

                reader.readAsText(file);
            };

            document.body.appendChild(input);
            input.click();
            document.body.removeChild(input);
        }

        // --- دوال فتح الملفات Universal File Handling ---
        function handleUniversalFile(input) {
            if (!input.files || !input.files[0]) return;
            const file = input.files[0];
            const fileType = file.name.split('.').pop().toLowerCase();

            // 1. Project Files (Template internal format)
            if (fileType === 'template' || fileType === 'json') {
                loadProjectFromFile(file);
                input.value = '';
                return;
            }

            // 2. High-Res Formats (PDF, AI, EPS) - Try PDF Header detection
            if (fileType === 'pdf' || fileType === 'ai' || fileType === 'eps') {
                const fileReader = new FileReader();
                fileReader.onload = function() {
                    const typedarray = new Uint8Array(this.result);
                    // محاولة القراءة كمستند PDF (لأن AI و EPS الحديثة تدعم PDF)
                    pdfjsLib.getDocument(typedarray).promise.then(function(pdf) {
                        tryOpenPdfContent(pdf);
                    }).catch(function(err) {
                        // إذا فشل كمستند PDF، حاول فتحه كصورة عادية (EPS/Imagine)
                        console.warn('PDF/AI render failed, falling back to image layer:', err);
                        addImageLayer(input);
                    });
                };
                fileReader.readAsArrayBuffer(file);
                input.value = '';
                return;
            }

            // 3. TIFF Files
            if (fileType === 'tif' || fileType === 'tiff') {
                openTifProject(file);
                input.value = '';
                return;
            }

            // 4. PSD (Warning Only)
            if(fileType === 'psd') {
                alert('تنبيه: سيتم فتح ملف PSD كصورة مدمجة (Flattened). لتحرير الطبقات، يرجى حفظها كملف PNG منفصل لكل طبقة.');
            }

            // 5. Default: Open as Image Layer (SVG, PNG, JPG, WEBP, etc.)
            // SVG opens here "as is" which renders perfectly in browsers
            addImageLayer(input);
            input.value = '';
        }

        // دالة مساعدة لفتح محتوى PDF/AI
        function tryOpenPdfContent(pdf) {
            pdf.getPage(1).then(function(page) {
                const scale = 3; // دقة عالية
                const viewport = page.getViewport({scale: scale});
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                const renderContext = {
                    canvasContext: context,
                    viewport: viewport
                };
                const renderTask = page.render(renderContext);
                renderTask.promise.then(function () {
                    const dataUrl = canvas.toDataURL('image/png');
                    const origW = viewport.width / scale;
                    const origH = viewport.height / scale;

                    // تحويل النقاط (72 DPI) إلى سم
                    const widthCm = (origW / 72) * 2.54;
                    const heightCm = (origH / 72) * 2.54;

                    // إضافة كطبقة صورة عادية قابلة للتحكم (بدون تغيير حجم البطاقة)
                    const card = document.getElementById('card');
                    const cardW = card.offsetWidth;
                    const cardH = card.offsetHeight;
                    
                    // حساب الحجم المناسب للصورة داخل البطاقة
                    const imgRatio = origW / origH;
                    const cardRatio = cardW / cardH;
                    let displayW, displayH;
                    
                    if (imgRatio > cardRatio) {
                        displayW = cardW * 0.9;
                        displayH = displayW / imgRatio;
                    } else {
                        displayH = cardH * 0.9;
                        displayW = displayH * imgRatio;
                    }
                    
                    // إنشاء طبقة صورة عادية قابلة للتحكم
                    const wrapper = createWrapper('image-layer');
                    wrapper.setAttribute('data-colorable', 'false');
                    wrapper.setAttribute('data-high-res', 'true');
                    
                    const contentWrapper = wrapper.querySelector('.content-wrapper');
                    contentWrapper.style.width = '100%';
                    contentWrapper.style.height = '100%';
                    contentWrapper.style.display = 'flex';
                    
                    const img = document.createElement('img');
                    img.src = dataUrl;
                    img.style.width = '100%';
                    img.style.height = '100%';
                    img.style.objectFit = 'contain';
                    img.style.pointerEvents = 'none';
                    
                    contentWrapper.appendChild(img);
                    
                    wrapper.style.width = displayW + 'px';
                    wrapper.style.height = displayH + 'px';
                    wrapper.style.left = (cardW / 2) + 'px';
                    wrapper.style.top = (cardH / 2) + 'px';
                    wrapper.style.transform = 'translate(-50%, -50%)';
                    
                    card.appendChild(wrapper);
                    
                    setTimeout(() => {
                        selectEl(wrapper);
                        setupInteract(wrapper, 'box');
                        saveState();
                    }, 50);
                    
                    showInfoModal('تم فتح الملف كطبقة عالية الدقة', 'تم بنجاح', '✅');
                });
            });
        }

        function openPdfProject(file) {
             // Deprecated in favor of handleUniversalFile logic, but kept just in case
             // Logic moved to tryOpenPdfContent
        }

        function openTifProject(fileInputOrFile) {
            let file;
            if (fileInputOrFile instanceof File) {
                file = fileInputOrFile;
            } else if (fileInputOrFile.files && fileInputOrFile.files[0]) {
                file = fileInputOrFile.files[0];
            } else {
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const buffer = e.target.result;
                    const ifds = UTIF.decode(buffer);
                    if (ifds.length === 0) {
                        showInfoModal('فشل قراءة ملف TIF', 'خطأ', '❌');
                        return;
                    }

                    const ifd = ifds[0];
                    UTIF.decodeImage(buffer, ifd);
                    const rgba = UTIF.toRGBA8(ifd);

                    let widthPx = ifd.width;
                    let heightPx = ifd.height;
                    let xRes = ifd.t282 ? (ifd.t282[0] / ifd.t282[1]) : 72;
                    let yRes = ifd.t283 ? (ifd.t283[0] / ifd.t283[1]) : 72;
                    let unit = ifd.t296 ? ifd.t296[0] : 2;

                    let widthCm, heightCm;
                    if (unit === 3) {
                        widthCm = widthPx / xRes;
                        heightCm = heightPx / yRes;
                    } else {
                        widthCm = (widthPx / xRes) * 2.54;
                        heightCm = (heightPx / yRes) * 2.54;
                    }

                    const newAppW = Math.round(widthCm * DPI_RATIO);
                    const newAppH = Math.round(heightCm * DPI_RATIO);

                    document.getElementById('custom-width').value = widthCm.toFixed(2);
                    document.getElementById('custom-height').value = heightCm.toFixed(2);

                    setCardSize(newAppW, newAppH);

                    const cnv = document.createElement('canvas');
                    cnv.width = widthPx;
                    cnv.height = heightPx;
                    const ctx = cnv.getContext('2d');
                    const imgData = ctx.createImageData(widthPx, heightPx);
                    imgData.data.set(rgba);
                    ctx.putImageData(imgData, 0, 0);

                    const dataUrl = cnv.toDataURL();

                    // إضافة كطبقة صورة عادية قابلة للتحكم
                    const card = document.getElementById('card');
                    const cardW = card.offsetWidth;
                    const cardH = card.offsetHeight;
                    
                    // حساب الحجم المناسب للصورة داخل البطاقة
                    const imgRatio = widthPx / heightPx;
                    const cardRatio = cardW / cardH;
                    let displayW, displayH;
                    
                    if (imgRatio > cardRatio) {
                        displayW = cardW * 0.9;
                        displayH = displayW / imgRatio;
                    } else {
                        displayH = cardH * 0.9;
                        displayW = displayH * imgRatio;
                    }
                    
                    // إنشاء طبقة صورة عادية قابلة للتحكم
                    const wrapper = createWrapper('image-layer');
                    wrapper.setAttribute('data-colorable', 'false');
                    wrapper.setAttribute('data-high-res', 'true');
                    
                    const contentWrapper = wrapper.querySelector('.content-wrapper');
                    contentWrapper.style.width = '100%';
                    contentWrapper.style.height = '100%';
                    contentWrapper.style.display = 'flex';
                    
                    const img = document.createElement('img');
                    img.src = dataUrl;
                    img.style.width = '100%';
                    img.style.height = '100%';
                    img.style.objectFit = 'contain';
                    img.style.pointerEvents = 'none';
                    
                    contentWrapper.appendChild(img);
                    
                    wrapper.style.width = displayW + 'px';
                    wrapper.style.height = displayH + 'px';
                    wrapper.style.left = (cardW / 2) + 'px';
                    wrapper.style.top = (cardH / 2) + 'px';
                    wrapper.style.transform = 'translate(-50%, -50%)';
                    
                    card.appendChild(wrapper);
                    
                    setTimeout(() => {
                        selectEl(wrapper);
                        setupInteract(wrapper, 'box');
                        saveState();
                    }, 50);
                    
                    showInfoModal('تم فتح ملف TIF كطبقة عالية الدقة', 'تم بنجاح', '✅');
                } catch(err) {
                    showInfoModal('خطأ في فتح ملف TIF: ' + err.message, 'خطأ', '❌');
                }
            };
            reader.readAsArrayBuffer(file);
        }


        // ==========================================
        //  وظائف النافذة العائمة (إغلاق + سحب)
        // ==========================================
        function closeFloatingToolbar() {
            const toolbar = document.getElementById('floating-context-toolbar');
            if (toolbar) toolbar.classList.add('hidden');

            // إلغاء تحديد العنصر النشط
            if (activeEl) {
                activeEl.classList.remove('selected');
                activeEl.querySelectorAll('.resize-handle').forEach(h => h.style.display = 'none');
                activeEl = null;

                // إخفاء لوحة الأنماط الجانبية
                document.getElementById('style-panel').classList.remove('open');
            }
        }

        // دالة تحديث حالة واجهة التدرج بناءً على العنصر المحدد
        function updateGradientUIState(el) {
            const settings = document.getElementById('floating-grad-settings');
            const btn = document.getElementById('btn-toggle-gradient');
            if (!settings || !btn) return;

            // فحص هل العنصر له تدرج مفعل
            const hasGradient = el && el.hasAttribute('data-has-gradient');

            if (hasGradient) {
                // العنصر له تدرج - إظهار إعدادات التدرج وتحديث الألوان
                settings.classList.remove('hidden');
                settings.style.display = 'flex';
                btn.classList.add('bg-indigo-100', 'text-indigo-700', 'border-indigo-300');
                btn.classList.remove('bg-[#f1f5f9]', 'text-[#475569]');
                btn.innerHTML = '<i class="fas fa-fill-drip"></i> إلغاء تدرج النص';

                // تحديث ألوان التدرج من العنصر
                const gradStart = el.getAttribute('data-grad-start') || '#6366f1';
                const gradEnd = el.getAttribute('data-grad-end') || '#ec4899';
                const gradAngle = el.getAttribute('data-grad-angle') || '90';
                document.getElementById('grad-start-color').value = gradStart;
                document.getElementById('grad-end-color').value = gradEnd;
                document.getElementById('grad-angle').value = gradAngle;
            } else {
                // العنصر ليس له تدرج - إخفاء الإعدادات وإعادة الزر للحالة الافتراضية
                settings.classList.add('hidden');
                settings.style.display = 'none';
                btn.classList.remove('bg-indigo-100', 'text-indigo-700', 'border-indigo-300');
                btn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
                btn.innerHTML = '<i class="fas fa-fill-drip"></i> تدرج النص';

                // إعادة ألوان التدرج للقيم الافتراضية
                document.getElementById('grad-start-color').value = '#6366f1';
                document.getElementById('grad-end-color').value = '#ec4899';
                document.getElementById('grad-angle').value = '90';
            }
        }

        // دالة تفعيل/إلغاء وضع التدرج من النافذة العائمة
        function toggleGradientMode() {
            const settings = document.getElementById('floating-grad-settings');
            const btn = document.getElementById('btn-toggle-gradient');

            if (settings.classList.contains('hidden')) {
                // تفعيل التدرج
                settings.classList.remove('hidden');
                settings.style.display = 'flex';
                btn.classList.add('bg-indigo-100', 'text-indigo-700', 'border-indigo-300');
                btn.classList.remove('bg-[#f1f5f9]', 'text-[#475569]');
                btn.innerHTML = '<i class="fas fa-fill-drip"></i> إلغاء تدرج النص';

                // تطبيق تدرج افتراضي إذا لم يكن موجوداً
                updateElementGradient();
            } else {
                // إلغاء التدرج
                settings.classList.add('hidden');
                settings.style.display = 'none';
                btn.classList.remove('bg-indigo-100', 'text-indigo-700', 'border-indigo-300');
                btn.classList.add('bg-[#f1f5f9]', 'text-[#475569]');
                btn.innerHTML = '<i class="fas fa-fill-drip"></i> تدرج النص';

                removeTextGradient();
            }
        }

        // دالة جعل العناصر قابلة للسحب من منطقة الإمساك (Header) - نسخة محسنة سلسة
        function makeElementDraggable(elmnt, handleId) {
            let startX = 0, startY = 0, initialLeft = 0, initialTop = 0;
            const header = document.getElementById(handleId);

            if (header) {
                header.onmousedown = dragMouseDown;
                header.ontouchstart = dragMouseDown;
            }

            function dragMouseDown(e) {
                e = e || window.event;

                // السماح بالنقر على الأزرار التفاعلية
                if(e.target.closest('button') || e.target.closest('.clickable')) {
                    return;
                }

                // إلغاء التحديد الافتراضي لمنع المشاكل أثناء السحب
                e.preventDefault();

                if(e.type === 'touchstart') {
                    startX = e.touches[0].clientX;
                    startY = e.touches[0].clientY;
                } else {
                    startX = e.clientX;
                    startY = e.clientY;
                }

                // حفظ الموقع الحالي للعنصر بدقة
                const rect = elmnt.getBoundingClientRect();
                initialLeft = rect.left;
                initialTop = rect.top;

                // إزالة الترانسفورم فوراً لتثبيت الحسابات
                elmnt.style.transform = "none";
                elmnt.style.left = initialLeft + "px";
                elmnt.style.top = initialTop + "px";
                // هام: تغليب البوزيشن ليكون فيكسد أو ابسلوت حسب الحاجة
                // هنا هو fixed حسب الـ CSS الأصلي

                document.onmouseup = closeDragElement;
                document.onmousemove = elementDrag;
                document.ontouchend = closeDragElement;
                document.ontouchmove = elementDrag;
            }

            function elementDrag(e) {
                e = e || window.event;
                e.preventDefault(); // منع التحريك الافتراضي للشاشة في اللمس

                let clientX, clientY;
                if(e.type === 'touchmove') {
                    clientX = e.touches[0].clientX;
                    clientY = e.touches[0].clientY;
                } else {
                    clientX = e.clientX;
                    clientY = e.clientY;
                }

                // حساب الإزاحة (offset)
                const deltaX = clientX - startX;
                const deltaY = clientY - startY;

                // تطبيق الموقع الجديد بناءً على الموقع الابتدائي + الإزاحة
                elmnt.style.left = (initialLeft + deltaX) + "px";
                elmnt.style.top = (initialTop + deltaY) + "px";
            }

            function closeDragElement() {
                document.onmouseup = null;
                document.onmousemove = null;
                document.ontouchend = null;
                document.ontouchmove = null;
            }
        }

        // تفعيل السحب للنافذة العائمة عند التحميل
        document.addEventListener('DOMContentLoaded', function() {
            const floatingToolbar = document.getElementById('floating-context-toolbar');
            if(floatingToolbar) {
                makeElementDraggable(floatingToolbar, 'floating-toolbar-header');
            }
            // تحميل الخطوط المفضلة
            loadFavoriteFonts();
        });

        // استدعاء فوري في حالة عدم انطلاق الحدث (لأن الصفحة محملة مسبقاً)
        if(document.getElementById('floating-context-toolbar')) {
             makeElementDraggable(document.getElementById('floating-context-toolbar'), 'floating-toolbar-header');
        }

        // ==========================================
        //  نظام الـ Freemium - دوال التقييد
        // ==========================================

        function restrictFonts() {
            // إذا كان المستخدم بريميوم، فتح كل شيء
            if (userTier === 'premium') {
                const fontSelects = document.querySelectorAll('select[id*="font"]');
                fontSelects.forEach(select => {
                    Array.from(select.options).forEach(option => {
                        option.disabled = false;
                        option.textContent = option.textContent.replace(' [PREMIUM]', '').replace('[PREMIUM] ', '');
                    });
                });
                return;
            }

            // للمستخدمين المجانيين - تطبيق التقييد
            const fontSelects = document.querySelectorAll('select[id*="font"]');
            fontSelects.forEach(select => {
                // عد جميع الخيارات (بدون "إضافة خط مخصص")
                let allOptions = Array.from(select.options).filter(opt =>
                    !opt.textContent.includes('إضافة خط مخصص') &&
                    !opt.textContent.includes('Add Custom Font')
                );

                let totalFonts = allOptions.length;
                let premiumStart = totalFonts - 6; // آخر 6 خطوط هي بريميوم

                // معالجة جميع الخيارات
                allOptions.forEach((option, index) => {
                    if (index < premiumStart) {
                        // الخطوط المفتوحة
                        option.disabled = false;
                        option.textContent = option.textContent.replace(' [PREMIUM]', '');
                    } else {
                        // آخر 6 خطوط = بريميوم
                        option.disabled = true;
                        if (!option.textContent.includes('[PREMIUM]')) {
                            option.textContent = option.textContent + ' [PREMIUM]';
                        }
                    }
                });

                // تعطيل "إضافة خط مخصص" دائماً للمجانيين
                const customFontOption = Array.from(select.options).find(opt =>
                    opt.textContent.includes('إضافة خط مخصص') ||
                    opt.textContent.includes('Add Custom Font')
                );
                if (customFontOption) {
                    customFontOption.disabled = true;
                    if (!customFontOption.textContent.includes('[PREMIUM]')) {
                        customFontOption.textContent = '[PREMIUM] ' + customFontOption.textContent;
                    }
                }
            });
        }

        function restrictShapes() {
            const shapesDropdown = document.getElementById('shapes-dropdown');
            if (shapesDropdown && userTier === 'free') {
                const items = shapesDropdown.querySelectorAll('[data-shape]');
                items.forEach((item, index) => {
                    if (index >= ITEMS_PER_CATEGORY_FREE) {
                        item.classList.add('locked-item');
                        item.style.opacity = '0.4';
                        item.style.pointerEvents = 'auto';
                        item.onclick = (e) => {
                            e.stopPropagation();
                            showPremiumModal('أشكال إضافية');
                        };
                    }
                });
            }
        }

        function restrictFrames() {
            const framesDropdown = document.getElementById('frames-dropdown');
            if (framesDropdown && userTier === 'free') {
                const items = framesDropdown.querySelectorAll('[data-frame]');
                items.forEach((item, index) => {
                    if (index >= ITEMS_PER_CATEGORY_FREE) {
                        item.classList.add('locked-item');
                        item.style.opacity = '0.4';
                        item.style.pointerEvents = 'auto';
                        item.onclick = (e) => {
                            e.stopPropagation();
                            showPremiumModal('إطارات إضافية');
                        };
                    }
                });
            }
        }

        // عند فتح أي dropdown، تطبيق التقييد
        function openDropdownWithRestrictions(dropdownId) {
            const dropdown = document.getElementById(dropdownId);
            if (dropdown && userTier === 'free') {
                setTimeout(() => {
                    if (dropdownId === 'shapes-dropdown') restrictShapes();
                    if (dropdownId === 'frames-dropdown') restrictFrames();
                }, 100);
            }
        }

        // عند الضغط على عنصر مقفل
        function handleLockedItemClick(e, itemName) {
            if (userTier === 'free') {
                e.stopPropagation();
                e.preventDefault();

                // تأثير التكبير
                const target = e.currentTarget;
                target.style.transform = 'scale(1.1)';
                setTimeout(() => target.style.transform = 'scale(1)', 300);

                // إظهار النافذة المشفوعة
                showPremiumModal(itemName);
            }
        }

        // نافذة البريميوم المشفوعة (محسنة ولطيفة)
        function showPremiumModal(featureName, imageSrc = null) {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                inset: 0;
                background: rgba(15, 23, 42, 0.6);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                backdrop-filter: blur(8px);
                transition: all 0.3s;
            `;

            // خلفية الصورة الضبابية إذا وجدت
            let backgroundStyle = '';
            if (imageSrc) {
                backgroundStyle = `
                    position: relative;
                    overflow: hidden;
                `;
            }

            modal.innerHTML = `
                <div style="
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 24px;
                    padding: 30px;
                    width: 320px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
                    text-align: center;
                    border: 1px solid rgba(255,255,255,0.5);
                    animation: slideIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    ${backgroundStyle}
                ">
                    ${imageSrc ? `
                        <div style="
                            position: absolute;
                            inset: 0;
                            background-image: url('${imageSrc}');
                            background-size: cover;
                            background-position: center;
                            filter: blur(20px);
                            opacity: 0.15;
                            z-index: 0;
                            transform: scale(1.2);
                        "></div>
                    ` : ''}

                    <div style="position: relative; z-index: 1;">
                        ${imageSrc ? `
                        <div style="
                            width: 140px;
                            height: 140px;
                            background: white;
                            border-radius: 20px;
                            margin: 0 auto 20px auto;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            box-shadow: 0 15px 35px rgba(99, 102, 241, 0.15);
                            border: 4px solid white;
                            overflow: hidden;
                            position: relative;
                        ">
                            <div style="
                                position: absolute;
                                top: 8px;
                                right: 8px;
                                background: #f472b6;
                                color: white;
                                font-size: 10px;
                                font-weight: bold;
                                padding: 2px 6px;
                                border-radius: 6px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            ">PREMIUM</div>
                            <img src="${imageSrc}" style="max-width: 90%; max-height: 90%; object-fit: contain; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));">
                        </div>
                        ` : `
                        <div style="
                            width: 60px;
                            height: 60px;
                            background: linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%);
                            border-radius: 50%;
                            margin: 0 auto 15px auto;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            box-shadow: 0 10px 20px rgba(99, 102, 241, 0.15);
                        ">
                            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 13a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v6a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2v-6" /><path d="M11 16a1 1 0 1 0 2 0a1 1 0 0 0 -2 0" /><path d="M8 11v-4a4 4 0 1 1 8 0v4" /></svg>
                        </div>
                        `}

                        <h2 style="color: #1e293b; font-size: 18px; margin-bottom: 8px; font-weight: 800;">
                            عنصر مميز ✨
                        </h2>

                        <p style="color: #64748b; font-size: 12px; margin-bottom: 20px; line-height: 1.6; font-weight: 600;">
                            هذا العنصر متاح فقط للمشتركين.<br>امتلك هذا العنصر وآلاف العناصر الأخرى الآن!
                        </p>

                        <button onclick="window.location.href = 'subscriptions.html'" style="
                            width: 100%;
                            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
                            color: white;
                            border: none;
                            padding: 12px;
                            border-radius: 14px;
                            font-weight: bold;
                            font-size: 13px;
                            cursor: pointer;
                            margin-bottom: 10px;
                            transition: all 0.3s;
                            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
                        " onmouseover="this.style.transform='translateY(-2px) shadow-lg'" onmouseout="this.style.transform='translateY(0)'">
                            ترقية للباقة الكاملة 💎
                        </button>

                        <button onclick="this.parentElement.parentElement.parentElement.remove();" style="
                            width: 100%;
                            background: transparent;
                            color: #94a3b8;
                            border: none;
                            padding: 8px;
                            border-radius: 10px;
                            font-weight: bold;
                            font-size: 11px;
                            cursor: pointer;
                            transition: all 0.3s;
                        " onmouseover="this.style.color='#64748b'" onmouseout="this.style.color='#94a3b8'">
                            ليس الآن
                        </button>
                    </div>
                </div>

                <style>
                    @keyframes slideIn {
                        from { transform: scale(0.95) translateY(10px); opacity: 0; }
                        to { transform: scale(1) translateY(0); opacity: 1; }
                    }
                </style>
            `;

            document.body.appendChild(modal);
            modal.onclick = (e) => {
                if (e.target === modal) modal.remove();
            };
        }

        // فتح صفحة الدخول البريميوم
        function openPremiumLogin() {
            document.getElementById('login-overlay').style.display = 'flex';
        }

        // تبديل الـ overlay (إظهار/إخفاء)
        function toggleLoginOverlay() {
            const overlay = document.getElementById('login-overlay');
            if (overlay.style.display === 'none' || overlay.style.display === '') {
                overlay.style.display = 'flex';
            } else {
                overlay.style.display = 'none';
            }
        }

        // تحديث الـ tier بعد الدخول البريميوم
        function setPremiumUser() {
            updateUserTier(true);
            // إزالة التقييدات
            document.querySelectorAll('.locked-item').forEach(item => {
                item.classList.remove('locked-item');
                item.style.opacity = '1';
            });
            // إخفاء الـ overlay بعد الدخول الناجح
            document.getElementById('login-overlay').style.display = 'none';
        }
        // ==========================================

        // استدعاء عند تحميل الصفحة
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(restrictFonts, 500);
        });

// ========== إدارة الجلسة (Session Management) ==========

function checkSession() {
    const sessionStr = localStorage.getItem('despro_session');
    if (sessionStr) {
        try {
            const session = JSON.parse(sessionStr);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            // التحقق من تاريخ التاريخ
            let expiryDate = null;
            const dateStr = session.expiryDate.trim();
            if (dateStr.match(/^\d{2}-\d{2}-\d{4}$/)) {
                const [day, month, year] = dateStr.split('-');
                expiryDate = new Date(`${year}-${month}-${day}`);
            } else if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
                expiryDate = new Date(dateStr);
            } else if (dateStr.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
                expiryDate = new Date(dateStr);
            }
            expiryDate.setHours(0, 0, 0, 0);

            if (expiryDate >= today) {
                // الجلسة صالحة
                userTier = 'premium';
                document.documentElement.setAttribute('data-tier', 'premium');
                updateStudioName(session.name);
                updateFooterForUser(session.name);

                // تحديث العبارة في الهيدر للبريميوم
                const subtitleEl = document.getElementById('studio-subtitle-display');
                if(subtitleEl) {
                    subtitleEl.innerHTML = '<span>مساحة مخصصة</span><span style="color: #cccccc; margin: 0 8px; font-weight: 300;">|</span><span>حيث أنت ✨</span>';
                    subtitleEl.classList.remove('text-slate-600');
                    subtitleEl.classList.add('text-[#555555]');
                }
                setTimeout(function() {
                    const el = document.getElementById('studio-subtitle-display');
                    if(el) {
                        el.innerHTML = '<span>مساحة مخصصة</span><span style="color: #cccccc; margin: 0 8px; font-weight: 300;">|</span><span>حيث أنت ✨</span>';
                        el.classList.remove('text-slate-600');
                        el.classList.add('text-[#555555]');
                    }
                }, 500);
                setTimeout(function() {
                    const el = document.getElementById('studio-subtitle-display');
                    if(el) {
                        el.innerHTML = '<span>مساحة مخصصة</span><span style="color: #cccccc; margin: 0 8px; font-weight: 300;">|</span><span>حيث أنت ✨</span>';
                        el.classList.remove('text-slate-600');
                        el.classList.add('text-[#555555]');
                    }
                }, 1500);

                // إخفاء زر الدخول إن وجد
                const loginOverlay = document.getElementById('login-overlay');
                if(loginOverlay) loginOverlay.style.display = 'none';
            } else {
                // الجلسة منتهية
                logoutUser();
            }
        } catch (e) {
            console.error('Session error', e);
            logoutUser();
        }
    }
}

function updateFooterForUser(name) {
    const authContainer = document.getElementById('auth-container');

    if (authContainer) {
        authContainer.innerHTML = `
            <div class="flex items-center gap-2">
                <div class="flex items-center justify-center gap-2 px-5 py-2 bg-[#fbbf24]/10 rounded-lg border border-[#fbbf24]/20 text-[#fbbf24] text-xs font-bold shadow-sm">
                    <i class="fas fa-crown text-[#fbbf24] text-[10px]"></i>
                    <span>${name}</span>
                </div>
                <button type="button" id="logout-btn" class="flex items-center justify-center gap-1.5 px-2 py-1 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white text-[10px] font-bold rounded-lg border border-white/10 transition-all shadow-sm" title="تسجيل خروج">
                    <i class="fas fa-sign-out-alt text-[10px]"></i>
                    <span class="font-sans tracking-wide">Log out</span>
                </button>
            </div>
        `;

        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function() {
                logoutUser();
            });
        }
    }

    const studioTitle = document.getElementById('studio-name-display');
    if(studioTitle) {
        studioTitle.innerHTML = `استوديو ${name} 🎨`;
    }
}

function logoutUser() {
    localStorage.removeItem('despro_session');
    localStorage.removeItem('userTier');
    sessionStorage.removeItem('studioName');
    sessionStorage.removeItem('expiryDate');
    sessionStorage.removeItem('sessionId');
    window.location.reload();
}
document.addEventListener('DOMContentLoaded', checkSession);
document.addEventListener('DOMContentLoaded', loadAssetsLibraryFromGitHub);


// ============ دوال الطبقات (Layers Panel) ============

function toggleLayersPanel() {
    const content = document.getElementById('layers-panel-content');
    const arrow = document.getElementById('layers-panel-arrow');
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        content.classList.add('flex');
        arrow.style.transform = 'rotate(-90deg)';
    } else {
        content.classList.add('hidden');
        content.classList.remove('flex');
        arrow.style.transform = 'rotate(0deg)';
    }
}


function toggleLayerVisibility(button, elementId) {
    const card = document.getElementById('card');
    const element = card?.querySelector(`[data-element-id="${elementId}"]`);

    if (element) {
        element.style.display = element.style.display === 'none' ? '' : 'none';
        button.querySelector('i').classList.toggle('fa-eye-slash');
        button.classList.toggle('opacity-50');
    }
}

function deleteElement(elementId) {
    const card = document.getElementById('card');
    const element = card?.querySelector(`[data-element-id="${elementId}"]`);

    if (element) {
        showConfirmModal('هل أنت متأكد من حذف هذا العنصر؟', 'حذف العنصر', '🗑️', function() {
            removeEl(element);
        });
    }
}

document.addEventListener('DOMContentLoaded', updateLayersList);

// تحديث الطبقات عند تغيير الاختيار
const originalSelectEl = selectEl;
selectEl = function(el) {
    originalSelectEl(el);
    if (typeof updateLayersList === 'function') {
        updateLayersList();
    }
};





document.addEventListener('DOMContentLoaded', updateLayersList);

// Override to ensure update on open

// === FIXED updateLayersList - finds ALL elements ===

// === تحريك الطبقة للأعلى (z-index أكبر) ===
function moveLayerUp(elementId) {
    const card = document.getElementById('card');
    const element = card.querySelector('[data-element-id="' + elementId + '"]');
    if (!element) return;

    const allElements = Array.from(card.querySelectorAll('.draggable-el'));
    const currentZ = parseInt(element.style.zIndex) || 10;

    // البحث عن العنصر الذي فوقه مباشرة
    let nextHigherZ = Infinity;
    let swapElement = null;

    allElements.forEach(el => {
        if (el === element) return;
        const z = parseInt(el.style.zIndex) || 10;
        if (z > currentZ && z < nextHigherZ) {
            nextHigherZ = z;
            swapElement = el;
        }
    });

    if (swapElement) {
        // تبديل z-index
        element.style.zIndex = nextHigherZ;
        swapElement.style.zIndex = currentZ;
    } else {
        // لا يوجد عنصر فوقه، زد z-index بـ 1
        element.style.zIndex = currentZ + 1;
    }

    updateLayersList();
    saveState();
}

// === تحريك الطبقة للأسفل (z-index أقل) ===
function moveLayerDown(elementId) {
    const card = document.getElementById('card');
    const element = card.querySelector('[data-element-id="' + elementId + '"]');
    if (!element) return;

    const allElements = Array.from(card.querySelectorAll('.draggable-el'));
    const currentZ = parseInt(element.style.zIndex) || 10;

    // البحث عن العنصر الذي تحته مباشرة
    let nextLowerZ = -Infinity;
    let swapElement = null;

    allElements.forEach(el => {
        if (el === element) return;
        const z = parseInt(el.style.zIndex) || 10;
        if (z < currentZ && z > nextLowerZ) {
            nextLowerZ = z;
            swapElement = el;
        }
    });

    if (swapElement) {
        // تبديل z-index
        element.style.zIndex = nextLowerZ;
        swapElement.style.zIndex = currentZ;
    } else if (currentZ > 1) {
        // لا يوجد عنصر تحته، قلل z-index بـ 1
        element.style.zIndex = currentZ - 1;
    }

    updateLayersList();
    saveState();
}

// === نسخة محدثة مع أزرار الترتيب ===
function updateLayersList() {
    const card = document.getElementById('card');
    const layersList = document.getElementById('layers-list');

    if (!card || !layersList) return;

    const elements = card.querySelectorAll('.draggable-el');

    if (elements.length === 0) {
        layersList.innerHTML = '<div class="text-center text-[10px] text-[#64748b] py-4">لا توجد عناصر في منطقة العمل</div>';
        return;
    }

    layersList.innerHTML = '';

    // ترتيب العناصر حسب z-index (الأعلى أولاً)
    const elementsArray = Array.from(elements).sort((a, b) => {
        return (parseInt(b.style.zIndex) || 10) - (parseInt(a.style.zIndex) || 10);
    });

    elementsArray.forEach((element, index) => {
        let elementId = element.getAttribute('data-element-id');
        if (!elementId) {
            elementId = 'el-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
            element.setAttribute('data-element-id', elementId);
        }

        // الحصول على اسم التصنيف والصورة المصغرة
        const categoryName = element.getAttribute('data-category-name');
        const thumbSrc = element.getAttribute('data-thumb');

        let elementType = '';
        let icon = 'fa-square';

        if (element.classList.contains('text-layer')) {
            elementType = 'نص';
            icon = 'fa-font';
        } else if (element.classList.contains('image-layer')) {
            elementType = 'صورة';
            icon = 'fa-image';
        } else if (element.classList.contains('frame-layer')) {
            elementType = 'إطار';
            icon = 'fa-vector-square';
        } else if (element.classList.contains('shape-layer')) {
            elementType = 'شكل';
            icon = 'fa-shapes';
        } else {
            elementType = 'عنصر';
        }

        // استخدام اسم التصنيف إذا كان موجود
        const displayName = categoryName || elementType;

        // أيقونة خاصة للتصنيفات
        if (categoryName) {
            if (categoryName.includes('زخارف') || categoryName.includes('إطارات')) icon = 'fa-vector-square';
            else if (categoryName.includes('رمضان')) icon = 'fa-moon';
            else if (categoryName.includes('ورد') || categoryName.includes('زهور')) icon = 'fa-seedling';
            else if (categoryName.includes('كرتون') || categoryName.includes('شخصيات')) icon = 'fa-user';
        }

        const isSelected = element.classList.contains('selected');
        const isHidden = element.style.display === 'none';

        const layerItem = document.createElement('div');
        layerItem.className = 'layer-item p-2 rounded-lg border transition-all cursor-pointer flex items-center gap-2 ' +
            (isSelected
                ? 'bg-[#6366f1] text-white border-[#6366f1]'
                : 'bg-white border-[#e2e8f0] text-[#1e293b] hover:border-[#6366f1]');

        // الصورة المصغرة أو الأيقونة
        let thumbHtml = '';
        if (thumbSrc) {
            thumbHtml = '<img src="' + thumbSrc + '" class="w-6 h-6 object-contain rounded bg-[#f1f5f9] flex-shrink-0" onerror="this.style.display=\'none\'">';
        } else {
            thumbHtml = '<i class="fas ' + icon + ' flex-shrink-0"></i>';
        }

        layerItem.innerHTML = '<div class="flex-1 flex items-center gap-2 min-w-0">' +
            thumbHtml +
            '<div class="flex-1 min-w-0">' +
                '<div class="text-[10px] font-bold truncate">' + displayName + '</div>' +
            '</div>' +
        '</div>' +
        '<div class="flex items-center gap-0.5" onclick="event.stopPropagation()">' +
            '<button class="p-1 text-[10px] hover:bg-[#e2e8f0] rounded transition" onclick="moveLayerUp(\'' + elementId + '\')" title="تقديم للأمام">' +
                '<i class="fas fa-chevron-up"></i>' +
            '</button>' +
            '<button class="p-1 text-[10px] hover:bg-[#e2e8f0] rounded transition" onclick="moveLayerDown(\'' + elementId + '\')" title="إرسال للخلف">' +
                '<i class="fas fa-chevron-down"></i>' +
            '</button>' +
            '<button class="p-1 text-[10px] hover:opacity-70 transition ' + (isHidden ? 'opacity-50' : '') + '" onclick="toggleLayerVisibility(this, \'' + elementId + '\')" title="إظهار/إخفاء">' +
                '<i class="fas ' + (isHidden ? 'fa-eye-slash' : 'fa-eye') + '"></i>' +
            '</button>' +
            '<button class="p-1 text-[10px] hover:text-red-500 transition" onclick="deleteElement(\'' + elementId + '\')" title="حذف">' +
                '<i class="fas fa-trash"></i>' +
            '</button>' +
        '</div>';

        layerItem.addEventListener('click', function(e) {
            if (!e.target.closest('button')) {
                selectEl(element);
                updateLayersList();
            }
        });

        layersList.appendChild(layerItem);
    });
}
 
