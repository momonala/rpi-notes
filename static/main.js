(function() {
    'use strict';

    function initAll() {
        // First: installs the t-* hooks (tab pills, skeletons, tooltips,
        // checkboxes) that the feature modules below drive.
        window.SMTransitions?.init();
        window.ServiceMonitorUiShell?.init();
        window.ServiceMonitorServicesList?.init();
        window.ServiceMonitorLogStream?.init();
        window.ServiceMonitorSystemInfo?.init();
        window.ServiceMonitorServiceInfo?.init();
        window.ServiceMonitorSystemMetricsChart?.init();
        window.ServiceMonitorServiceMetricsChart?.init();
        window.ServiceMonitorR2Usage?.init();
        window.ServiceMonitorSidebarDetails?.load().catch((error) => {
            console.error('⚠️ Sidebar details load failed:', error);
        });
        window.ServiceMonitorSidebarDetails?.loadAlertSettings().catch((error) => {
            console.error('⚠️ Alert settings load failed:', error);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
        return;
    }
    initAll();
})();
