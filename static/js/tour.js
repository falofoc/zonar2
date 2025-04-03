// ZONAR App Tour Guide
document.addEventListener('DOMContentLoaded', function() {
    // Check if this is the user's first visit (or if they requested the tour)
    const showTour = localStorage.getItem('zonar_show_tour') === 'true' || new URLSearchParams(window.location.search).has('tour');
    
    // Only show tour on main page
    if (!showTour || !document.querySelector('.main-content')) {
        return;
    }
    
    // Initialize Shepherd Tour
    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            cancelIcon: {
                enabled: true
            },
            classes: 'shepherd-theme-arrows custom-shepherd-theme',
            scrollTo: true,
            modalOverlayOpeningRadius: 4
        },
        exitOnEsc: true,
        keyboardNavigation: true
    });

    // Define tour steps
    // Welcome step
    tour.addStep({
        id: 'welcome',
        title: document.dir === 'rtl' ? 'مرحباً بك في تطبيق زونار!' : 'Welcome to ZONAR!',
        text: document.dir === 'rtl' 
            ? 'مرحباً بك في زونار! دعنا نستعرض معاً كيفية تتبع أسعار منتجات أمازون.'
            : 'Welcome to ZONAR! Let\'s walk through how to track Amazon product prices.',
        buttons: [
            {
                text: document.dir === 'rtl' ? 'إغلاق' : 'Skip Tour',
                action: tour.complete,
                classes: 'shepherd-button-secondary'
            },
            {
                text: document.dir === 'rtl' ? 'التالي' : 'Next',
                action: tour.next,
                classes: 'shepherd-button-primary'
            }
        ]
    });

    // Add Product Step
    tour.addStep({
        id: 'add-product',
        title: document.dir === 'rtl' ? 'إضافة منتج جديد' : 'Add a New Product',
        text: document.dir === 'rtl'
            ? 'انقر هنا لإضافة منتج جديد من أمازون. كل ما تحتاجه هو رابط المنتج من موقع أمازون السعودية.'
            : 'Click here to add a new Amazon product. All you need is the product link from amazon.sa.',
        attachTo: {
            element: '.add-product-btn',
            on: 'bottom'
        },
        buttons: [
            {
                text: document.dir === 'rtl' ? 'السابق' : 'Back',
                action: tour.back,
                classes: 'shepherd-button-secondary'
            },
            {
                text: document.dir === 'rtl' ? 'التالي' : 'Next',
                action: tour.next,
                classes: 'shepherd-button-primary'
            }
        ]
    });

    // Product Card Step
    if (document.querySelector('.product-card')) {
        tour.addStep({
            id: 'product-card',
            title: document.dir === 'rtl' ? 'بطاقة المنتج' : 'Product Card',
            text: document.dir === 'rtl'
                ? 'هنا ستجد معلومات المنتج مثل السعر الحالي وتاريخ تغيرات السعر. يتم تحديث الأسعار تلقائياً يومياً.'
                : 'Here you\'ll find product information like current price and price history. Prices are automatically updated daily.',
            attachTo: {
                element: '.product-card',
                on: 'bottom'
            },
            buttons: [
                {
                    text: document.dir === 'rtl' ? 'السابق' : 'Back',
                    action: tour.back,
                    classes: 'shepherd-button-secondary'
                },
                {
                    text: document.dir === 'rtl' ? 'التالي' : 'Next',
                    action: tour.next,
                    classes: 'shepherd-button-primary'
                }
            ]
        });

        // Target Price Step
        tour.addStep({
            id: 'target-price',
            title: document.dir === 'rtl' ? 'السعر المستهدف' : 'Target Price',
            text: document.dir === 'rtl'
                ? 'يمكنك تحديد سعر مستهدف لتلقي إشعار عندما ينخفض سعر المنتج إلى أو أقل من هذا السعر.'
                : 'You can set a target price to receive a notification when the product price drops to or below this price.',
            attachTo: {
                element: '.target-price',
                on: 'bottom'
            },
            buttons: [
                {
                    text: document.dir === 'rtl' ? 'السابق' : 'Back',
                    action: tour.back,
                    classes: 'shepherd-button-secondary'
                },
                {
                    text: document.dir === 'rtl' ? 'التالي' : 'Next',
                    action: tour.next,
                    classes: 'shepherd-button-primary'
                }
            ]
        });

        // Buy Button Step
        tour.addStep({
            id: 'buy-button',
            title: document.dir === 'rtl' ? 'زر الشراء' : 'Buy Button',
            text: document.dir === 'rtl'
                ? 'عندما يكون السعر مناسبًا، انقر هنا للانتقال مباشرة إلى صفحة المنتج على أمازون.'
                : 'When the price is right, click here to go directly to the product page on Amazon.',
            attachTo: {
                element: '.btn-buy',
                on: 'top'
            },
            buttons: [
                {
                    text: document.dir === 'rtl' ? 'السابق' : 'Back',
                    action: tour.back,
                    classes: 'shepherd-button-secondary'
                },
                {
                    text: document.dir === 'rtl' ? 'التالي' : 'Next',
                    action: tour.next,
                    classes: 'shepherd-button-primary'
                }
            ]
        });

        // Check Price Step
        tour.addStep({
            id: 'check-price',
            title: document.dir === 'rtl' ? 'تحديث السعر يدوياً' : 'Manually Check Price',
            text: document.dir === 'rtl'
                ? 'يمكنك تحديث سعر المنتج في أي وقت بالنقر على زر تحديث السعر.'
                : 'You can refresh the product price anytime by clicking the Check Price button.',
            attachTo: {
                element: '.btn-outline-primary',
                on: 'left'
            },
            buttons: [
                {
                    text: document.dir === 'rtl' ? 'السابق' : 'Back',
                    action: tour.back,
                    classes: 'shepherd-button-secondary'
                },
                {
                    text: document.dir === 'rtl' ? 'التالي' : 'Next',
                    action: tour.next,
                    classes: 'shepherd-button-primary'
                }
            ]
        });
    }

    // Notifications Step
    tour.addStep({
        id: 'notifications',
        title: document.dir === 'rtl' ? 'الإشعارات' : 'Notifications',
        text: document.dir === 'rtl'
            ? 'ستظهر هنا إشعارات تغيرات الأسعار والتنبيهات الهامة الأخرى. سيتم إرسال إشعارات البريد الإلكتروني أيضاً عند تغير الأسعار.'
            : 'Price change notifications and other important alerts will appear here. Email notifications will also be sent when prices change.',
        attachTo: {
            element: '.notifications-dropdown',
            on: 'bottom'
        },
        buttons: [
            {
                text: document.dir === 'rtl' ? 'السابق' : 'Back',
                action: tour.back,
                classes: 'shepherd-button-secondary'
            },
            {
                text: document.dir === 'rtl' ? 'التالي' : 'Next',
                action: tour.next,
                classes: 'shepherd-button-primary'
            }
        ]
    });

    // Search Step
    if (document.querySelector('.search-form')) {
        tour.addStep({
            id: 'search',
            title: document.dir === 'rtl' ? 'البحث عن المنتجات' : 'Search Products',
            text: document.dir === 'rtl'
                ? 'يمكنك البحث عن منتجاتك هنا عن طريق اسم المنتج أو الاسم المخصص.'
                : 'You can search for your products here by product name or custom name.',
            attachTo: {
                element: '.search-form',
                on: 'bottom'
            },
            buttons: [
                {
                    text: document.dir === 'rtl' ? 'السابق' : 'Back',
                    action: tour.back,
                    classes: 'shepherd-button-secondary'
                },
                {
                    text: document.dir === 'rtl' ? 'التالي' : 'Next',
                    action: tour.next,
                    classes: 'shepherd-button-primary'
                }
            ]
        });
    }

    // Language Switch Step
    tour.addStep({
        id: 'language',
        title: document.dir === 'rtl' ? 'تغيير اللغة' : 'Change Language',
        text: document.dir === 'rtl'
            ? 'يمكنك التبديل بين اللغتين العربية والإنجليزية بالنقر هنا.'
            : 'You can switch between Arabic and English languages by clicking here.',
        attachTo: {
            element: '.lang-switch',
            on: 'bottom'
        },
        buttons: [
            {
                text: document.dir === 'rtl' ? 'السابق' : 'Back',
                action: tour.back,
                classes: 'shepherd-button-secondary'
            },
            {
                text: document.dir === 'rtl' ? 'التالي' : 'Next',
                action: tour.next,
                classes: 'shepherd-button-primary'
            }
        ]
    });

    // Final Step
    tour.addStep({
        id: 'finish',
        title: document.dir === 'rtl' ? 'أنت جاهز الآن!' : 'You\'re All Set!',
        text: document.dir === 'rtl'
            ? 'مبروك! أنت الآن تعرف كيفية استخدام زونار لتتبع أسعار منتجات أمازون. إذا كنت بحاجة إلى مساعدة إضافية، يمكنك العودة إلى هذا الدليل في أي وقت من قائمة المستخدم.'
            : 'Congratulations! You now know how to use ZONAR to track Amazon product prices. If you need additional help, you can return to this guide anytime from the user menu.',
        buttons: [
            {
                text: document.dir === 'rtl' ? 'السابق' : 'Back',
                action: tour.back,
                classes: 'shepherd-button-secondary'
            },
            {
                text: document.dir === 'rtl' ? 'إنهاء' : 'Finish',
                action: tour.complete,
                classes: 'shepherd-button-primary'
            }
        ]
    });

    // Save that tour has been seen
    tour.on('complete', function() {
        localStorage.setItem('zonar_show_tour', 'false');
    });

    // Start the tour
    setTimeout(function() {
        tour.start();
    }, 1000);
}); 