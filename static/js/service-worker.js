// ZONAR Service Worker - تمكين ميزات PWA وإشعارات الويب
const CACHE_NAME = 'zonar-cache-v1';
const STATIC_ASSETS = [
  '/',
  '/static/css/styles.css',
  '/static/js/app.js',
  '/static/img/pwa/icon-192x192.png',
  '/static/img/pwa/icon-512x512.png',
  '/static/manifest.json'
];

// تثبيت Service Worker وتخزين الموارد الأساسية
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('تخزين الموارد الأساسية في ذاكرة التخزين المؤقت');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// تنشيط Service Worker وحذف التخزين المؤقت القديم
self.addEventListener('activate', (event) => {
  const currentCaches = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return cacheNames.filter((cacheName) => !currentCaches.includes(cacheName));
    }).then((cachesToDelete) => {
      return Promise.all(cachesToDelete.map((cacheToDelete) => {
        return caches.delete(cacheToDelete);
      }));
    }).then(() => self.clients.claim())
  );
});

// استراتيجية الشبكة أولاً، والرجوع إلى التخزين المؤقت
self.addEventListener('fetch', (event) => {
  // لا تتداخل مع طلبات API
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/admin/') ||
      event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // إذا كان الطلب ناجحًا، قم بتحديث التخزين المؤقت
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // إذا فشل الطلب، استرجع من التخزين المؤقت
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          
          // إذا كان الطلب لصفحة HTML، قم بإرجاع صفحة وضع عدم الاتصال
          if (event.request.headers.get('accept').includes('text/html')) {
            return caches.match('/offline.html');
          }
          
          return new Response('حدث خطأ في الاتصال', { 
            status: 503,
            statusText: 'خدمة غير متوفرة',
            headers: new Headers({
              'Content-Type': 'text/plain;charset=UTF-8'
            })
          });
        });
      })
  );
});

// معالجة الإشعارات
self.addEventListener('push', (event) => {
  const options = {
    body: 'تم تغيير سعر أحد المنتجات التي تتابعها!',
    icon: '/static/img/pwa/icon-192x192.png',
    badge: '/static/img/pwa/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: '/'
    },
    dir: 'rtl',
    actions: [
      {
        action: 'view',
        title: 'عرض المنتج',
        icon: '/static/img/pwa/view-product.png'
      },
      {
        action: 'close',
        title: 'إغلاق',
        icon: '/static/img/pwa/close.png'
      }
    ]
  };

  try {
    // استخدام البيانات من الإشعار إذا كانت متوفرة
    if (event.data) {
      const data = event.data.json();
      
      options.title = data.title || 'إشعار من زونار';
      options.body = data.body || options.body;
      options.tag = data.tag || 'default';
      options.data.url = data.url || '/';
      
      // ضبط صورة مخصصة إذا كانت متوفرة
      if (data.image) {
        options.image = data.image;
      }
    }
  } catch (err) {
    console.error('خطأ في معالجة بيانات الإشعار:', err);
  }

  event.waitUntil(
    self.registration.showNotification(options.title, options)
  );
});

// التعامل مع النقر على الإشعارات
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  let url = '/';
  
  // التحقق من الإجراء المتخذ
  if (event.action === 'view' && event.notification.data && event.notification.data.url) {
    url = event.notification.data.url;
  } else if (event.action === 'close') {
    return; // لا تفتح أي شيء عند النقر على "إغلاق"
  } else if (event.notification.data && event.notification.data.url) {
    // النقر على الإشعار نفسه
    url = event.notification.data.url;
  }

  event.waitUntil(
    clients.matchAll({ type: 'window' })
      .then((windowClients) => {
        // التحقق مما إذا كان التطبيق مفتوحًا بالفعل
        for (const client of windowClients) {
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        
        // إذا لم يكن التطبيق مفتوحًا، قم بفتح نافذة جديدة
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// استقبال رسائل من التطبيق
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
}); 