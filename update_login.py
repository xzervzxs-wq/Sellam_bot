
import os

file_path = 'despro/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'async function verifyCode() {'
end_marker = 'function updateStudioName(name) {'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers")
    exit(1)

new_code = """async function verifyCode() {
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
            if (dateStr.match(/^\\d{2}-\\d{2}-\\d{4}$/)) {
                const [day, month, year] = dateStr.split('-');
                expiryDate = new Date(`${year}-${month}-${day}`);
            }
            else if (dateStr.match(/^\\d{4}-\\d{2}-\\d{2}$/)) {
                expiryDate = new Date(dateStr);
            }
            else if (dateStr.match(/^\\d{2}\\/\\d{2}\\/\\d{4}$/)) {
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

"""

# Preserve indentation logic by simply replacing the chunk text (assuming new_code is relatively clean)
# We need to be careful about not deleting updateStudioName
# The replacement should go from start_idx up to end_idx (exclusive of end_marker)

# We check if there's whitespace before end_marker we want to preserve?
# Actually, strict replacement is fine.

final_content = content[:start_idx] + new_code + "\n\n        " + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Updated verifyCode successfully")
