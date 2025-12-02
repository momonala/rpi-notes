/**
 * Service Monitor - Main JavaScript
 * 
 * Handles sidebar navigation, responsive behavior, and user interactions.
 */

(function() {
    'use strict';

    // ============================================
    // Configuration
    // ============================================
    const CONFIG = {
        // Breakpoints (must match CSS)
        BREAKPOINT_MOBILE: 640,   // Below this: mobile (iPhone)
        BREAKPOINT_TABLET: 1024,  // Below this: tablet (iPad), above: desktop
        
        // Animation timing (ms)
        TRANSITION_DURATION: 300,
        
        // Local storage keys
        STORAGE_SIDEBAR_COLLAPSED: 'servicemonitor:sidebar-collapsed',
    };

    const CSS_CLASSES = {
        SIDEBAR_OPEN: 'sidebar--open',
        SIDEBAR_CLOSED: 'sidebar--closed',
        SIDEBAR_COLLAPSED: 'sidebar--collapsed',
        OVERLAY_VISIBLE: 'sidebar-overlay--visible',
        HIDDEN: 'hidden',
    };

    // ============================================
    // DOM Elements
    // ============================================
    const elements = {
        sidebar: document.getElementById('sidebar'),
        sidebarToggle: document.getElementById('sidebarToggle'),
        sidebarClose: document.getElementById('sidebarClose'),
        mobileHamburger: document.getElementById('mobileHamburger'),
        sidebarOverlay: document.getElementById('sidebarOverlay'),
    };

    // ============================================
    // State
    // ============================================
    const state = {
        isSidebarCollapsed: loadSidebarState(),
        isMobileSidebarOpen: false,
    };

    // ============================================
    // Utility Functions
    // ============================================
    
    /**
     * Get current device type based on viewport width
     * @returns {'mobile'|'tablet'|'desktop'}
     */
    function getDeviceType() {
        const width = window.innerWidth;
        if (width < CONFIG.BREAKPOINT_MOBILE) return 'mobile';
        if (width < CONFIG.BREAKPOINT_TABLET) return 'tablet';
        return 'desktop';
    }

    /**
     * Check if current view is mobile
     * @returns {boolean}
     */
    function isMobile() {
        return getDeviceType() === 'mobile';
    }

    /**
     * Load sidebar collapsed state from localStorage
     * @returns {boolean}
     */
    function loadSidebarState() {
        try {
            return localStorage.getItem(CONFIG.STORAGE_SIDEBAR_COLLAPSED) === 'true';
        } catch {
            return false;
        }
    }

    /**
     * Save sidebar collapsed state to localStorage
     * @param {boolean} collapsed
     */
    function saveSidebarState(collapsed) {
        try {
            localStorage.setItem(CONFIG.STORAGE_SIDEBAR_COLLAPSED, String(collapsed));
        } catch {
            // localStorage not available
        }
    }

    // ============================================
    // Sidebar Functions
    // ============================================

    /**
     * Open mobile sidebar (slide in)
     */
    function openMobileSidebar() {
        if (!elements.sidebar) return;
        
        state.isMobileSidebarOpen = true;
        elements.sidebar.classList.remove(CSS_CLASSES.SIDEBAR_CLOSED);
        elements.sidebar.classList.add(CSS_CLASSES.SIDEBAR_OPEN);
        
        // Show overlay
        if (elements.sidebarOverlay) {
            elements.sidebarOverlay.classList.add(CSS_CLASSES.OVERLAY_VISIBLE);
        }
        
        // Hide hamburger
        if (elements.mobileHamburger) {
            elements.mobileHamburger.classList.add(CSS_CLASSES.HIDDEN);
        }
        
        // Prevent body scroll on mobile
        document.body.style.overflow = 'hidden';
    }

    /**
     * Close mobile sidebar (slide out)
     */
    function closeMobileSidebar() {
        if (!elements.sidebar) return;
        
        state.isMobileSidebarOpen = false;
        elements.sidebar.classList.remove(CSS_CLASSES.SIDEBAR_OPEN);
        elements.sidebar.classList.add(CSS_CLASSES.SIDEBAR_CLOSED);
        
        // Hide overlay
        if (elements.sidebarOverlay) {
            elements.sidebarOverlay.classList.remove(CSS_CLASSES.OVERLAY_VISIBLE);
        }
        
        // Show hamburger
        if (elements.mobileHamburger) {
            elements.mobileHamburger.classList.remove(CSS_CLASSES.HIDDEN);
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
    }

    /**
     * Toggle desktop sidebar collapse
     */
    function toggleDesktopSidebarCollapse() {
        if (!elements.sidebar) return;
        
        state.isSidebarCollapsed = !state.isSidebarCollapsed;
        elements.sidebar.classList.toggle(CSS_CLASSES.SIDEBAR_COLLAPSED, state.isSidebarCollapsed);
        saveSidebarState(state.isSidebarCollapsed);
    }

    /**
     * Apply initial sidebar state based on device type
     */
    function initializeSidebarState() {
        if (!elements.sidebar) return;
        
        const device = getDeviceType();
        
        if (device === 'mobile') {
            // Mobile: sidebar starts closed
            elements.sidebar.classList.add(CSS_CLASSES.SIDEBAR_CLOSED);
            elements.sidebar.classList.remove(CSS_CLASSES.SIDEBAR_OPEN, CSS_CLASSES.SIDEBAR_COLLAPSED);
            if (elements.mobileHamburger) {
                elements.mobileHamburger.classList.remove(CSS_CLASSES.HIDDEN);
            }
        } else {
            // Tablet/Desktop: sidebar always visible
            elements.sidebar.classList.remove(CSS_CLASSES.SIDEBAR_CLOSED, CSS_CLASSES.SIDEBAR_OPEN);
            if (elements.mobileHamburger) {
                elements.mobileHamburger.classList.add(CSS_CLASSES.HIDDEN);
            }
            
            // Desktop: restore collapsed state
            if (device === 'desktop' && state.isSidebarCollapsed) {
                elements.sidebar.classList.add(CSS_CLASSES.SIDEBAR_COLLAPSED);
            }
        }
        
        // Ensure overlay is hidden
        if (elements.sidebarOverlay) {
            elements.sidebarOverlay.classList.remove(CSS_CLASSES.OVERLAY_VISIBLE);
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
    }

    // ============================================
    // Event Handlers
    // ============================================

    /**
     * Handle sidebar toggle button click
     * @param {Event} event
     */
    function handleSidebarToggleClick(event) {
        event.stopPropagation();
        
        const device = getDeviceType();
        
        if (device === 'mobile') {
            openMobileSidebar();
        } else if (device === 'desktop') {
            toggleDesktopSidebarCollapse();
        }
        // Tablet: no toggle action (sidebar always visible and expanded)
    }

    /**
     * Handle click outside sidebar (mobile only)
     * @param {Event} event
     */
    function handleOutsideClick(event) {
        if (!isMobile() || !state.isMobileSidebarOpen) return;
        
        const clickedInsideSidebar = elements.sidebar?.contains(event.target);
        const clickedToggle = elements.sidebarToggle?.contains(event.target);
        const clickedHamburger = elements.mobileHamburger?.contains(event.target);
        
        if (!clickedInsideSidebar && !clickedToggle && !clickedHamburger) {
            closeMobileSidebar();
        }
    }

    /**
     * Handle window resize
     */
    function handleResize() {
        // Re-initialize sidebar state when crossing breakpoints
        initializeSidebarState();
    }

    /**
     * Handle overlay click
     */
    function handleOverlayClick() {
        closeMobileSidebar();
    }

    // ============================================
    // Event Listener Setup
    // ============================================

    function setupEventListeners() {
        // Sidebar toggle button (hamburger inside sidebar on desktop)
        if (elements.sidebarToggle) {
            elements.sidebarToggle.addEventListener('click', handleSidebarToggleClick);
        }
        
        // Close button (mobile only, inside sidebar)
        if (elements.sidebarClose) {
            elements.sidebarClose.addEventListener('click', closeMobileSidebar);
        }
        
        // Mobile hamburger button (fixed position)
        if (elements.mobileHamburger) {
            elements.mobileHamburger.addEventListener('click', openMobileSidebar);
        }
        
        // Overlay click
        if (elements.sidebarOverlay) {
            elements.sidebarOverlay.addEventListener('click', handleOverlayClick);
        }
        
        // Click outside sidebar
        document.addEventListener('click', handleOutsideClick);
        
        // Window resize (debounced)
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(handleResize, 150);
        });
        
        // Handle escape key to close mobile sidebar
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && state.isMobileSidebarOpen) {
                closeMobileSidebar();
            }
        });
    }

    // ============================================
    // Initialization
    // ============================================

    function init() {
        initializeSidebarState();
        setupEventListeners();
        
        // Log device type for debugging (remove in production)
        console.log('[ServiceMonitor] Initialized for device:', getDeviceType());
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
