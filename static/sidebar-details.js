(function() {
    'use strict';

    // Value-text thresholds for the sidebar's compact per-service mem readout
    // (this is one service's share of the whole machine, so much lower than the
    // 60/85 warn/crit used by the host-wide and per-service detail-view tiles).
    const METRIC_WARN_PCT = 5;
    const METRIC_CRIT_PCT = 10;

    function buildIcon(name, className = 'service-details__icon') {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('aria-hidden', 'true');
        svg.setAttribute('class', className);
        const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttribute('href', `#icon-${name}`);
        svg.appendChild(use);
        return svg;
    }

    /**
     * Build a "[icon] NNN MB (N.N%)" cell for the sidebar row. Text color reflects usage
     * level (ok/warn/crit) instead of a fixed per-metric identity color.
     * @param {string} className - 'service-mem'
     * @param {string} icon - icon symbol name
     * @param {number | null} pct
     * @param {number | null} mb
     */
    function buildMetricCell(className, icon, pct, mb) {
        const cell = document.createElement('span');
        cell.className = `${className} ${
            pct == null
                ? 'service-metric--empty'
                : pct >= METRIC_CRIT_PCT
                    ? 'service-metric--crit'
                    : pct >= METRIC_WARN_PCT
                        ? 'service-metric--warn'
                        : 'service-metric--ok'
        }`;
        cell.title = 'Click to sort by this column';
        const text = document.createElement('span');
        text.className = 'service-metric__value';
        text.textContent = pct != null && mb != null
            ? `${mb} MB (${pct.toFixed(1)}%)`
            : pct != null
                ? `${pct.toFixed(1)}%`
                : '—';
        cell.appendChild(text);
        return cell;
    }

    /**
     * Update sidebar card status indicator and detail rows.
     * @param {Element} serviceItem
     * @param {object} status
     */
    function updateServiceItem(serviceItem, status) {
        const icon = serviceItem.querySelector('.status-icon');
        if (icon) {
            icon.classList.remove('status-icon--active', 'status-icon--failed', 'status-icon--inactive');
            const use = icon.querySelector('use');
            if (status.is_active) {
                icon.classList.add('status-icon--active');
                icon.setAttribute('aria-label', 'Active');
                if (use) use.setAttribute('href', '#icon-activity');
            } else if (status.is_failed) {
                icon.classList.add('status-icon--failed');
                icon.setAttribute('aria-label', 'Failed');
                if (use) use.setAttribute('href', '#icon-alert-circle');
            } else {
                icon.classList.add('status-icon--inactive');
                icon.setAttribute('aria-label', 'Inactive');
                if (use) use.setAttribute('href', '#icon-pause-circle');
            }
        }

        const grid = serviceItem.querySelector('.service-item-grid');
        if (!grid) return;

        // Remove previous dynamic bottom-row cells
        grid.querySelector('.service-details__item--ci')?.remove();
        grid.querySelector('.service-mem')?.remove();
        grid.querySelector('.service-uptime')?.remove();

        if (status.ci_status) {
            const ciIcon = status.ci_status === 'success' ? 'check-circle' : status.ci_status === 'failure' ? 'x-circle' : 'alert-triangle';
            const ciClass = `service-details__item service-details__item--ci service-details__item--ci-${status.ci_status}`;
            const ciLink = document.createElement('a');
            ciLink.className = ciClass;
            ciLink.href = `https://github.com/momonala/${status.project_group}/actions/workflows/ci.yml`;
            ciLink.target = '_blank';
            ciLink.rel = 'noopener';
            ciLink.title = 'View CI on GitHub';
            const ciSvg = buildIcon(ciIcon);
            ciSvg.setAttribute('aria-label', `CI ${status.ci_status}`);
            ciSvg.removeAttribute('aria-hidden');
            ciLink.appendChild(ciSvg);
            grid.appendChild(ciLink);
        }
        grid.appendChild(buildMetricCell('service-mem', 'memory', status.memory_used_pct, status.memory_used_mb));

        const item = document.createElement('span');
        item.className = 'service-uptime';
        item.textContent = status.uptime || '—';
        grid.appendChild(item);
    }

    /**
     * Render or update the alert badge in the sidebar service item.
     * @param {Element} serviceItem
     * @param {string} frequency - 'hourly' | 'daily' | 'muted'
     */
    function updateAlertBadge(serviceItem, frequency) {
        const grid = serviceItem.querySelector('.service-item-grid');
        if (!grid) return;

        let badge = grid.querySelector('.service-alert-badge');
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'service-alert-badge';

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'service-alert-badge__icon');
            svg.setAttribute('aria-hidden', 'true');
            const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
            svg.appendChild(use);
            badge.appendChild(svg);

            grid.appendChild(badge);
        }

        const use = badge.querySelector('use');
        badge.classList.toggle('service-alert-badge--muted', frequency === 'muted');
        badge.setAttribute('aria-label', `Alert: ${frequency}`);
        if (use) use.setAttribute('href', frequency === 'muted' ? '#icon-bell-off' : '#icon-bell');
    }

    /**
     * Fetch alert settings and render the frequency select in the main content header.
     */
    async function loadAlertSettings() {
        const control = document.getElementById('alertSettingsControl');
        if (!control) return;

        const serviceName = control.dataset.service;
        if (!serviceName) return;

        const response = await fetch('/api/alert-settings');
        if (!response.ok) return;
        const settings = await response.json();

        const frequency = settings[serviceName] ?? 'hourly';

        if (control.querySelector('.alert-frequency-select')) {
            control.querySelector('.alert-frequency-select').value = frequency;
            return;
        }

        const select = document.createElement('select');
        select.className = 'alert-frequency-select';
        select.setAttribute('aria-label', 'Alert frequency');

        for (const { value, label } of [
            { value: 'daily', label: 'Alert: daily' },
            { value: 'hourly', label: 'Alert: hourly' },
            { value: 'muted', label: 'Alert: muted' },
        ]) {
            const opt = document.createElement('option');
            opt.value = value;
            opt.textContent = label;
            select.appendChild(opt);
        }
        select.value = frequency;
        select.dataset.committed = frequency;

        select.addEventListener('change', async (e) => {
            const newFrequency = e.target.value;
            const prevFrequency = select.dataset.committed ?? 'hourly';
            try {
                const res = await fetch('/api/alert-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ service: serviceName, frequency: newFrequency }),
                });
                if (!res.ok) {
                    console.error('Failed to save alert setting, reverting');
                    select.value = prevFrequency;
                    return;
                }
                select.dataset.committed = newFrequency;
                const sidebarItem = document.querySelector(`.service-item[data-service-name="${CSS.escape(serviceName)}"]`);
                if (sidebarItem) updateAlertBadge(sidebarItem, newFrequency);
            } catch (err) {
                console.error('Failed to update alert setting:', err);
                select.value = prevFrequency;
            }
        });

        control.appendChild(select);
    }

    // --- Click-to-sort: click the mem cell to sort the whole list by memory
    // usage (descending, missing readings last); click it again to return to
    // the default alphabetical/grouped order.

    let sortMode = null; // null | 'mem'
    let latestMetricsByName = new Map(); // service name -> { memory_used_pct }
    let originalOrder = null; // [{ group, item }], captured once from the server-rendered order
    let sortHandlersBound = false;

    function captureOriginalOrder(nav) {
        if (originalOrder) return;
        originalOrder = [];
        nav.querySelectorAll('.project-group').forEach((group) => {
            group.querySelectorAll(':scope > .service-item').forEach((item) => {
                originalOrder.push({ group, item });
            });
        });
    }

    function metricValueFor(serviceName) {
        const metrics = latestMetricsByName.get(serviceName);
        return metrics ? metrics.memory_used_pct : null;
    }

    function applySort(nav) {
        captureOriginalOrder(nav);
        if (!originalOrder.length) return;

        if (!sortMode) {
            let lastGroup = null;
            for (const { group, item } of originalOrder) {
                if (group !== lastGroup) {
                    nav.appendChild(group);
                    lastGroup = group;
                }
                group.appendChild(item);
            }
            nav.querySelectorAll('.project-group').forEach((group) => {
                group.hidden = false;
            });
        } else {
            const sorted = [...originalOrder].sort((a, b) => {
                const va = metricValueFor(a.item.getAttribute('data-service-name'));
                const vb = metricValueFor(b.item.getAttribute('data-service-name'));
                if (va == null && vb == null) return 0;
                if (va == null) return 1;
                if (vb == null) return -1;
                return vb - va;
            });
            for (const { item } of sorted) {
                nav.appendChild(item);
            }
            nav.querySelectorAll('.project-group').forEach((group) => {
                group.hidden = !group.querySelector(':scope > .service-item');
            });
        }

        nav.dataset.sortMode = sortMode ?? '';
    }

    function setupSortHandlers(nav) {
        if (sortHandlersBound) return;
        sortHandlersBound = true;
        nav.addEventListener('click', (event) => {
            const cell = event.target.closest('.service-mem');
            if (!cell || !nav.contains(cell)) return;
            sortMode = sortMode === 'mem' ? null : 'mem';
            applySort(nav);
        });
    }

    /**
     * Refresh sidebar details from backend.
     */
    async function load() {
        const nav = document.querySelector('.sidebar__nav');
        if (!nav) return;

        setupSortHandlers(nav);

        const [detailsResponse, alertsResponse] = await Promise.all([
            fetch('/api/services/sidebar-details'),
            fetch('/api/alert-settings'),
        ]);

        if (!detailsResponse.ok) {
            throw new Error(`Failed to load sidebar details: ${detailsResponse.status}`);
        }
        const payload = await detailsResponse.json();
        const alertSettings = alertsResponse.ok ? await alertsResponse.json() : {};
        const services = Array.isArray(payload.services) ? payload.services : [];

        const byName = new Map();
        for (const item of nav.querySelectorAll('.service-item[data-service-name]')) {
            byName.set(item.getAttribute('data-service-name'), item);
        }

        latestMetricsByName = new Map(
            services.map((status) => [status.name, { memory_used_pct: status.memory_used_pct, memory_used_mb: status.memory_used_mb }]),
        );

        for (const status of services) {
            const serviceItem = byName.get(status.name);
            if (!serviceItem) continue;
            updateServiceItem(serviceItem, status);
            updateAlertBadge(serviceItem, alertSettings[status.name] ?? 'hourly');
        }

        applySort(nav);
    }

    window.ServiceMonitorSidebarDetails = {
        load,
        loadAlertSettings,
    };
})();
