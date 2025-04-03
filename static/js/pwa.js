// تسجيل Service Worker وإدارة إشعارات التطبيق
document.addEventListener('DOMContentLoaded', function() {
    // تسجيل Service Worker للعمل كـ PWA
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/js/service-worker.js')
                .then((reg) => {
                    console.log('Service Worker تم تسجيله بنجاح:', reg.scope);
                    
                    // التحقق من وجود تحديثات للخدمة العاملة
                    reg.onupdatefound = () => {
                        const installingWorker = reg.installing;
                        
                        installingWorker.onstatechange = () => {
                            if (installingWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                // هناك تحديث جديد متاح
                                showUpdateNotification();
                            }
                        };
                    };
                })
                .catch(error => {
                    console.error('فشل تسجيل Service Worker:', error);
                });
        });
    } else {
        console.log('Service Worker غير مدعوم في هذا المتصفح');
    }
    
    // تحقق من إمكانية إضافة التطبيق إلى الشاشة الرئيسية (PWA)
    let deferredPrompt;
    const addToHomeBtn = document.getElementById('add-to-home');
    
    // إخفاء زر التثبيت في البداية
    if (addToHomeBtn) {
        addToHomeBtn.style.display = 'none';
    }
    
    // استمع لحدث beforeinstallprompt
    window.addEventListener('beforeinstallprompt', (e) => {
        // منع ظهور النافذة المنبثقة التلقائية
        e.preventDefault();
        
        // حفظ الحدث للاستخدام لاحقًا
        deferredPrompt = e;
        
        // إظهار زر الإضافة إلى الشاشة الرئيسية
        if (addToHomeBtn) {
            addToHomeBtn.style.display = 'block';
            
            // إضافة معالج حدث النقر
            addToHomeBtn.addEventListener('click', () => {
                // إظهار مطالبة التثبيت
                deferredPrompt.prompt();
                
                // انتظار اختيار المستخدم
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('تمت إضافة التطبيق إلى الشاشة الرئيسية');
                        
                        // إظهار رسالة نجاح للمستخدم
                        showSuccessToast('تم تثبيت التطبيق بنجاح على جهازك!');
                    } else {
                        console.log('رفض المستخدم إضافة التطبيق');
                    }
                    
                    // إعادة تعيين المتغير
                    deferredPrompt = null;
                    
                    // إخفاء الزر
                    addToHomeBtn.style.display = 'none';
                });
            });
        }
    });
    
    // التعامل مع حدث appinstalled
    window.addEventListener('appinstalled', (evt) => {
        console.log('تم تثبيت التطبيق بنجاح');
    });
    
    // إعداد إشعارات الويب عند تسجيل الدخول
    const notifyBtn = document.getElementById('enable-notifications');
    
    if (notifyBtn) {
        // التحقق من دعم الإشعارات وحالة الإذن
        if ('Notification' in window) {
            if (Notification.permission === 'granted') {
                notifyBtn.style.display = 'none'; // إخفاء الزر إذا كان الإذن ممنوحًا بالفعل
            } else if (Notification.permission === 'denied') {
                notifyBtn.textContent = 'السماح بالإشعارات';
                notifyBtn.disabled = true;
                notifyBtn.classList.add('disabled');
            } else {
                notifyBtn.addEventListener('click', requestNotificationPermission);
            }
        } else {
            notifyBtn.style.display = 'none'; // إخفاء الزر إذا كانت الإشعارات غير مدعومة
        }
    }
});

// طلب إذن الإشعارات
function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.log('هذا المتصفح لا يدعم إشعارات الويب');
        return;
    }
    
    Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
            console.log('تم منح إذن الإشعارات');
            subscribeUserToPush();
            
            // إخفاء زر تفعيل الإشعارات
            const notifyBtn = document.getElementById('enable-notifications');
            if (notifyBtn) {
                notifyBtn.style.display = 'none';
            }
            
            // عرض رسالة نجاح
            showSuccessToast('تم تفعيل الإشعارات بنجاح!');
            
            // إرسال إشعار ترحيبي
            sendWelcomeNotification();
        } else {
            console.log('تم رفض إذن الإشعارات');
            showErrorToast('لن تتمكن من استلام إشعارات تغير الأسعار');
        }
    });
}

// الاشتراك في خدمة Push
function subscribeUserToPush() {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        navigator.serviceWorker.ready.then((reg) => {
            // التحقق من وجود اشتراك سابق
            reg.pushManager.getSubscription().then((subscription) => {
                if (subscription === null) {
                    // إنشاء اشتراك جديد
                    const vapidPublicKey = 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U';
                    const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
                    
                    reg.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: convertedVapidKey
                    }).then((newSubscription) => {
                        console.log('تم الاشتراك في خدمة Push:', newSubscription);
                        // إرسال معلومات الاشتراك إلى الخادم
                        sendSubscriptionToServer(newSubscription);
                    }).catch((err) => {
                        console.error('فشل الاشتراك في خدمة Push:', err);
                    });
                } else {
                    // الاشتراك موجود بالفعل
                    console.log('المستخدم مشترك بالفعل في خدمة Push');
                }
            });
        });
    }
}

// تحويل المفتاح العام إلى تنسيق مناسب
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// إرسال معلومات الاشتراك إلى الخادم
function sendSubscriptionToServer(subscription) {
    // تنفيذ طلب AJAX لإرسال الاشتراك إلى الخادم
    fetch('/save-subscription', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(subscription),
    })
    .then(response => {
        if (response.ok) {
            console.log('تم إرسال معلومات الاشتراك بنجاح إلى الخادم');
        } else {
            console.error('فشل إرسال معلومات الاشتراك إلى الخادم');
        }
    })
    .catch(error => {
        console.error('خطأ أثناء إرسال معلومات الاشتراك:', error);
    });
}

// إرسال إشعار ترحيبي
function sendWelcomeNotification() {
    // التحقق من دعم الإشعارات وأن الإذن ممنوح
    if ('Notification' in window && Notification.permission === 'granted') {
        navigator.serviceWorker.ready.then((registration) => {
            registration.showNotification('مرحبًا بك في زونار!', {
                body: 'سيتم إشعارك عند تغير أسعار المنتجات التي تتابعها.',
                icon: '/static/img/pwa/icon-192x192.png',
                badge: '/static/img/pwa/badge-72x72.png',
                vibrate: [100, 50, 100],
                dir: 'rtl',
                data: {
                    url: '/'
                },
                actions: [
                    {
                        action: 'explore',
                        title: 'استكشاف التطبيق',
                        icon: '/static/img/pwa/explore.png'
                    }
                ]
            });
        });
    }
}

// إظهار رسالة تحديث التطبيق
function showUpdateNotification() {
    const updateToast = document.createElement('div');
    updateToast.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    updateToast.innerHTML = `
    <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header">
            <strong class="me-auto">تحديث جديد متاح</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="إغلاق"></button>
        </div>
        <div class="toast-body">
            <p>يوجد تحديث جديد للتطبيق. قم بتحديث التطبيق للاستفادة من الميزات الجديدة.</p>
            <button class="btn btn-primary btn-sm update-btn">تحديث الآن</button>
        </div>
    </div>`;
    
    document.body.appendChild(updateToast);
    
    // إضافة معالج حدث للزر
    const updateBtn = updateToast.querySelector('.update-btn');
    updateBtn.addEventListener('click', () => {
        // إرسال رسالة لتحديث Service Worker
        navigator.serviceWorker.ready.then((registration) => {
            registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        });
        
        // تحديث الصفحة بعد وقت قصير
        setTimeout(() => {
            window.location.reload();
        }, 500);
    });
}

// إظهار رسالة نجاح
function showSuccessToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    toast.innerHTML = `
    <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header bg-success text-white">
            <strong class="me-auto">نجاح</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="إغلاق"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    </div>`;
    
    document.body.appendChild(toast);
    
    // إزالة التنبيه بعد 3 ثوانٍ
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// إظهار رسالة خطأ
function showErrorToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    toast.innerHTML = `
    <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header bg-danger text-white">
            <strong class="me-auto">تنبيه</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="إغلاق"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    </div>`;
    
    document.body.appendChild(toast);
    
    // إزالة التنبيه بعد 3 ثوانٍ
    setTimeout(() => {
        toast.remove();
    }, 3000);
} 