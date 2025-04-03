// ZONAR Mobile Tour Guide
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on a mobile device
    const isMobile = window.innerWidth <= 768;
    
    // Check if this is a user that should see the tour
    const showTour = localStorage.getItem('zonar_show_tour') === 'true' || 
                     new URLSearchParams(window.location.search).has('tour');
    
    // Check if authenticated and on the main page
    const isAuthenticated = document.body.classList.contains('user-authenticated');
    const isMainPage = document.querySelector('.main-content') !== null;
    
    // Only continue if we should show the tour
    if (!isMobile || !showTour || !isMainPage || !isAuthenticated) {
        return;
    }
    
    // Disable standard tour if we're using mobile tour
    localStorage.setItem('zonar_show_tour', 'false');
    
    // Create mobile tour elements
    initMobileTour();
});

function initMobileTour() {
    // Select the language direction and set up translations
    const isRTL = document.dir === 'rtl';
    
    // Define tour steps with language support
    const tourSteps = [
        {
            id: 'welcome',
            title: isRTL ? 'مرحباً بك في تطبيق زونار!' : 'Welcome to ZONAR!',
            content: isRTL 
                ? 'مرحباً بك في زونار! دعنا نستعرض معاً كيفية تتبع أسعار منتجات أمازون باستخدام تطبيقنا على الجوال.'
                : 'Welcome to ZONAR! Let\'s learn how to track Amazon product prices using our mobile app.',
            image: createWelcomePreview(),
            targetElement: null
        },
        {
            id: 'add-product',
            title: isRTL ? 'إضافة منتج جديد' : 'Add a New Product',
            content: isRTL
                ? 'اضغط على زر "+" لإضافة منتج جديد من أمازون. كل ما تحتاجه هو رابط المنتج من موقع أمازون السعودية.'
                : 'Tap the "+" button to add a new Amazon product. All you need is the product link from amazon.sa.',
            image: createAddProductPreview(),
            targetElement: '.add-product-btn',
            targetPosition: { x: 'center', y: 'top' }
        },
        {
            id: 'search',
            title: isRTL ? 'البحث عن المنتجات' : 'Search Products',
            content: isRTL
                ? 'استخدم شريط البحث للعثور على منتجاتك عن طريق اسم المنتج أو الاسم المخصص.'
                : 'Use the search bar to find your products by product name or custom name.',
            image: createSearchPreview(),
            targetElement: '.search-form',
            targetPosition: { x: 'center', y: 'top' }
        },
        {
            id: 'product-card',
            title: isRTL ? 'بطاقة المنتج' : 'Product Card',
            content: isRTL
                ? 'هنا ستجد معلومات المنتج مثل السعر الحالي وتاريخ تغيرات السعر. يتم تحديث الأسعار تلقائياً يومياً.'
                : 'Here you\'ll find product information including current price and price history. Prices are automatically updated daily.',
            image: createProductCardPreview(),
            targetElement: '.product-card',
            targetPosition: { x: 'center', y: 'center' }
        },
        {
            id: 'target-price',
            title: isRTL ? 'السعر المستهدف' : 'Target Price',
            content: isRTL
                ? 'اضبط السعر المستهدف للحصول على إشعار عندما ينخفض سعر المنتج إلى أو أقل من هذا السعر. اضغط على رمز التعديل لضبط السعر المستهدف.'
                : 'Set a target price to receive a notification when the product price drops to or below this price. Tap the edit icon to set your target price.',
            image: createTargetPricePreview(),
            targetElement: '.target-price',
            targetPosition: { x: 'left', y: 'center' }
        },
        {
            id: 'check-price',
            title: isRTL ? 'تحديث السعر يدوياً' : 'Check Price Manually',
            content: isRTL
                ? 'يمكنك تحديث سعر المنتج في أي وقت بالضغط على زر "تحديث السعر".'
                : 'You can refresh the product price anytime by tapping the "Check Price" button.',
            image: createPriceTrackingPreview(),
            targetElement: '.btn-check-price',
            targetPosition: { x: 'center', y: 'bottom' }
        },
        {
            id: 'buy-button',
            title: isRTL ? 'زر الشراء' : 'Buy Button',
            content: isRTL
                ? 'عندما يكون السعر مناسبًا، اضغط هنا للانتقال مباشرة إلى صفحة المنتج على أمازون.'
                : 'When the price is right, tap here to go directly to the product page on Amazon.',
            image: null,
            targetElement: '.btn-buy',
            targetPosition: { x: 'center', y: 'center' }
        },
        {
            id: 'notifications',
            title: isRTL ? 'الإشعارات' : 'Notifications',
            content: isRTL
                ? 'ستظهر هنا إشعارات تغيرات الأسعار والتنبيهات الهامة الأخرى. اضغط على رمز الجرس للوصول إلى إشعاراتك.'
                : 'Price change notifications and other important alerts will appear here. Tap the bell icon to access your notifications.',
            image: createNotificationPreview(),
            targetElement: '.notifications-dropdown',
            targetPosition: { x: 'center', y: 'bottom' }
        },
        {
            id: 'language-theme',
            title: isRTL ? 'تغيير اللغة والمظهر' : 'Language & Theme',
            content: isRTL
                ? 'يمكنك تغيير اللغة بين العربية والإنجليزية وتبديل المظهر بين الوضع الفاتح والداكن من قائمة الإعدادات.'
                : 'You can change the language between Arabic and English and switch between light and dark theme from the settings menu.',
            image: null,
            targetElement: '.nav-icon-btn',
            targetPosition: { x: 'right', y: 'bottom' }
        },
        {
            id: 'finish',
            title: isRTL ? 'أنت جاهز الآن!' : 'You\'re All Set!',
            content: isRTL
                ? 'مبروك! أنت الآن تعرف كيفية استخدام زونار لتتبع أسعار منتجات أمازون على جهازك المحمول. إذا كنت بحاجة إلى مساعدة إضافية، يمكنك الرجوع إلى هذا الدليل في أي وقت.'
                : 'Congratulations! You now know how to use ZONAR to track Amazon product prices on your mobile device. If you need additional help, you can return to this guide anytime.',
            image: null,
            targetElement: null
        }
    ];

    // Create tour elements
    createTourElements(tourSteps);
    
    // Add floating tour button after tour completes
    document.body.insertAdjacentHTML('beforeend', `
        <button id="mobileTourStartBtn" class="mobile-tour-start-btn">
            <i class="bi bi-info-circle"></i>
        </button>
    `);
    
    // Add event listener to the floating button
    document.getElementById('mobileTourStartBtn').addEventListener('click', function() {
        startMobileTour();
    });
    
    // Start the tour after a short delay
    setTimeout(function() {
        startMobileTour();
    }, 1000);
}

function createTourElements(steps) {
    // Create mobile tour container
    const tourOverlay = document.createElement('div');
    tourOverlay.className = 'mobile-tour-overlay';
    tourOverlay.id = 'mobileTourOverlay';
    
    const tourContainer = document.createElement('div');
    tourContainer.className = 'mobile-tour-container';
    tourContainer.id = 'mobileTourContainer';
    
    // Create initial content
    tourContainer.innerHTML = `
        <div class="mobile-tour-header">
            <div>
                <h3 class="mobile-tour-title" id="mobileTourTitle"></h3>
                <div class="mobile-tour-step-counter" id="mobileTourStepCounter"></div>
            </div>
            <button class="mobile-tour-close" id="mobileTourClose">
                <i class="bi bi-x-lg"></i>
            </button>
        </div>
        <div class="mobile-tour-content" id="mobileTourContent"></div>
        <div id="mobileTourImageContainer"></div>
        <div class="mobile-tour-indicator-container" id="mobileTourIndicators"></div>
        <div class="mobile-tour-footer">
            <button class="mobile-tour-btn mobile-tour-btn-secondary" id="mobileTourPrev">
                ${document.dir === 'rtl' ? 'السابق' : 'Previous'}
            </button>
            <button class="mobile-tour-btn mobile-tour-btn-primary" id="mobileTourNext">
                ${document.dir === 'rtl' ? 'التالي' : 'Next'}
            </button>
        </div>
    `;
    
    // Create pointer element
    const pointer = document.createElement('div');
    pointer.className = 'mobile-tour-pointer';
    pointer.id = 'mobileTourPointer';
    
    // Add indicators
    const indicatorsContainer = tourContainer.querySelector('#mobileTourIndicators');
    steps.forEach((step, index) => {
        const indicator = document.createElement('div');
        indicator.className = 'mobile-tour-indicator';
        indicator.setAttribute('data-step', index);
        indicatorsContainer.appendChild(indicator);
    });
    
    // Add to DOM
    document.body.appendChild(tourOverlay);
    document.body.appendChild(tourContainer);
    document.body.appendChild(pointer);
    
    // Add event listeners
    document.getElementById('mobileTourClose').addEventListener('click', endMobileTour);
    document.getElementById('mobileTourNext').addEventListener('click', nextTourStep);
    document.getElementById('mobileTourPrev').addEventListener('click', prevTourStep);
    
    // Add tour data to window object for access
    window.mobileTour = {
        steps: steps,
        currentStep: 0,
        active: false
    };
}

function startMobileTour() {
    // Set tour as active and show first step
    window.mobileTour.active = true;
    window.mobileTour.currentStep = 0;
    
    // Show overlay and container
    document.getElementById('mobileTourOverlay').classList.add('active');
    document.getElementById('mobileTourContainer').classList.add('active');
    
    // Hide start button while tour is active
    if (document.getElementById('mobileTourStartBtn')) {
        document.getElementById('mobileTourStartBtn').style.display = 'none';
    }
    
    // Show first step
    showTourStep(0);
}

function endMobileTour() {
    // Hide tour elements
    document.getElementById('mobileTourOverlay').classList.remove('active');
    document.getElementById('mobileTourContainer').classList.remove('active');
    document.getElementById('mobileTourPointer').classList.remove('active');
    
    // Remove any highlights
    const highlightedElement = document.querySelector('.mobile-tour-highlight');
    if (highlightedElement) {
        highlightedElement.classList.remove('mobile-tour-highlight');
    }
    
    // Mark as seen in localStorage
    localStorage.setItem('zonar_show_tour', 'false');
    
    // Show start button again
    if (document.getElementById('mobileTourStartBtn')) {
        document.getElementById('mobileTourStartBtn').style.display = 'flex';
    }
    
    // Set as inactive
    window.mobileTour.active = false;
}

function showTourStep(stepIndex) {
    const steps = window.mobileTour.steps;
    
    // Validate step index
    if (stepIndex < 0 || stepIndex >= steps.length) {
        return;
    }
    
    // Update current step
    window.mobileTour.currentStep = stepIndex;
    const step = steps[stepIndex];
    
    // Update title and content
    document.getElementById('mobileTourTitle').textContent = step.title;
    document.getElementById('mobileTourContent').textContent = step.content;
    
    // Update step counter
    document.getElementById('mobileTourStepCounter').textContent = 
        `${document.dir === 'rtl' ? 'الخطوة' : 'Step'} ${stepIndex + 1}/${steps.length}`;
    
    // Update image if available
    const imageContainer = document.getElementById('mobileTourImageContainer');
    imageContainer.innerHTML = '';
    if (step.image) {
        const img = document.createElement('img');
        img.src = step.image;
        img.className = 'mobile-tour-image';
        img.alt = step.title;
        imageContainer.appendChild(img);
    }
    
    // Update indicators
    document.querySelectorAll('.mobile-tour-indicator').forEach((indicator, idx) => {
        indicator.classList.toggle('active', idx === stepIndex);
    });
    
    // Update button labels for last step
    const nextBtn = document.getElementById('mobileTourNext');
    if (stepIndex === steps.length - 1) {
        nextBtn.textContent = document.dir === 'rtl' ? 'إنهاء' : 'Finish';
    } else {
        nextBtn.textContent = document.dir === 'rtl' ? 'التالي' : 'Next';
    }
    
    // Disable prev button on first step
    document.getElementById('mobileTourPrev').disabled = stepIndex === 0;
    
    // Remove previous highlight
    const prevHighlighted = document.querySelector('.mobile-tour-highlight');
    if (prevHighlighted) {
        prevHighlighted.classList.remove('mobile-tour-highlight');
    }
    
    // Position pointer and highlight target element if available
    const pointer = document.getElementById('mobileTourPointer');
    pointer.classList.remove('active');
    
    if (step.targetElement) {
        const targetEl = document.querySelector(step.targetElement);
        if (targetEl) {
            // Highlight the element
            targetEl.classList.add('mobile-tour-highlight');
            
            // Scroll to the element
            setTimeout(() => {
                targetEl.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
                
                // Position and show pointer
                setTimeout(() => {
                    const rect = targetEl.getBoundingClientRect();
                    let pointerX, pointerY;
                    
                    // Position based on target positioning config
                    switch (step.targetPosition.x) {
                        case 'left':
                            pointerX = rect.left - 80;
                            break;
                        case 'right':
                            pointerX = rect.right + 20;
                            break;
                        default: // center
                            pointerX = rect.left + rect.width / 2 - 30;
                    }
                    
                    switch (step.targetPosition.y) {
                        case 'top':
                            pointerY = rect.top - 80;
                            break;
                        case 'bottom':
                            pointerY = rect.bottom + 20;
                            break;
                        default: // center
                            pointerY = rect.top + rect.height / 2 - 30;
                    }
                    
                    // Apply position
                    pointer.style.left = `${pointerX}px`;
                    pointer.style.top = `${pointerY}px`;
                    pointer.classList.add('active');
                }, 500);
            }, 300);
        }
    }
}

function nextTourStep() {
    const currentStep = window.mobileTour.currentStep;
    const totalSteps = window.mobileTour.steps.length;
    
    if (currentStep < totalSteps - 1) {
        showTourStep(currentStep + 1);
    } else {
        // End tour on last step
        endMobileTour();
    }
}

function prevTourStep() {
    const currentStep = window.mobileTour.currentStep;
    
    if (currentStep > 0) {
        showTourStep(currentStep - 1);
    }
}

// Functions to expose for external access
window.ZONAR = window.ZONAR || {};
window.ZONAR.startMobileTour = startMobileTour;
window.ZONAR.endMobileTour = endMobileTour;

// Helper functions to create CSS-based preview images
function createWelcomePreview() {
    const container = document.createElement('div');
    container.className = 'mobile-preview';
    container.innerHTML = `
        <div class="preview-product-card">
            <div class="preview-product-image"></div>
            <div class="preview-product-info">
                <div class="preview-product-title"></div>
                <div class="preview-product-price"></div>
                <div class="preview-product-buttons">
                    <div class="preview-button preview-button-primary"></div>
                    <div class="preview-button preview-button-secondary"></div>
                </div>
            </div>
        </div>
    `;
    return container;
}

function createAddProductPreview() {
    const container = document.createElement('div');
    container.className = 'mobile-preview';
    container.innerHTML = `
        <div class="preview-add-product">
            <div class="preview-form-label"></div>
            <div class="preview-form-field"></div>
            <div class="preview-form-label"></div>
            <div class="preview-form-field"></div>
            <div class="preview-submit-button"></div>
        </div>
    `;
    return container;
}

function createSearchPreview() {
    const container = document.createElement('div');
    container.className = 'mobile-preview';
    container.innerHTML = `
        <div class="preview-search">
            <div class="preview-search-icon"></div>
            <div class="preview-search-bar"></div>
        </div>
    `;
    return container;
}

function createProductCardPreview() {
    const container = document.createElement('div');
    container.className = 'mobile-preview';
    container.innerHTML = `
        <div class="preview-product-card">
            <div class="preview-product-image"></div>
            <div class="preview-product-info">
                <div class="preview-product-title"></div>
                <div class="preview-product-price"></div>
                <div class="preview-product-buttons">
                    <div class="preview-button preview-button-primary"></div>
                    <div class="preview-button preview-button-secondary"></div>
                </div>
            </div>
        </div>
    `;
    return container;
}

function createPriceTrackingPreview() {
    const container = document.createElement('div');
    container.className = 'mobile-preview';
    container.innerHTML = `
        <div class="preview-price-chart">
            <div class="preview-chart-line"></div>
            <div class="preview-chart-dots">
                <div class="preview-chart-dot"></div>
                <div class="preview-chart-dot"></div>
                <div class="preview-chart-dot"></div>
                <div class="preview-chart-dot"></div>
                <div class="preview-chart-dot"></div>
            </div>
            <div class="preview-chart-target"></div>
        </div>
    `;
    return container;
}

function createNotificationPreview() {
    const container = document.createElement('div');
    container.className = 'mobile-preview';
    container.innerHTML = `
        <div class="preview-notification">
            <div class="preview-notification-title"></div>
            <div class="preview-notification-content"></div>
        </div>
        <div class="preview-notification">
            <div class="preview-notification-title"></div>
            <div class="preview-notification-content"></div>
        </div>
    `;
    return container;
}

function createTargetPricePreview() {
    const container = document.createElement('div');
    container.className = 'mobile-preview';
    container.innerHTML = `
        <div class="preview-target-price">
            <div class="preview-target-icon"></div>
            <div class="preview-target-info">
                <div class="preview-target-label"></div>
                <div class="preview-target-value"></div>
            </div>
            <div class="preview-edit-icon"></div>
        </div>
    `;
    return container;
} 