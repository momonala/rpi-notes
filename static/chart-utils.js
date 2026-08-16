// Shared, stateless helpers for the system and per-service metric charts.
// Kept dependency-free so both chart modules can build on the same primitives.
(function() {
    'use strict';

    function cssToken(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    function withOpacity(color, alpha) {
        const hex = color.replace('#', '');
        if (hex.length !== 6) return color;
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    function readLocal(key) {
        try {
            return localStorage.getItem(key);
        } catch {
            return null;
        }
    }

    function writeLocal(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch {
            // Ignore quota / private-mode failures.
        }
    }

    function setPressed(btn, active) {
        btn.classList.toggle('is-active', active);
        btn.setAttribute('aria-pressed', String(active));
    }

    function syncChoiceGroup(root, selector, dataKey, activeValue) {
        root.querySelectorAll(selector).forEach((btn) => {
            setPressed(btn, btn.dataset[dataKey] === activeValue);
        });
    }

    function padCell(value, width, align = 'left') {
        const text = String(value);
        if (text.length >= width) return text.slice(0, width);
        const padding = ' '.repeat(width - text.length);
        return align === 'right' ? padding + text : text + padding;
    }

    function formatTooltipValue(value) {
        return value == null ? '—' : String(value);
    }

    // Compact x-axis label; wider windows show the date, narrow ones just the time.
    function formatXTick(value, window) {
        const date = new Date(value);
        if (window === '7d' || window === '24h') {
            return date.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit' });
        }
        return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    }

    window.SMChartUtils = {
        cssToken,
        withOpacity,
        readLocal,
        writeLocal,
        setPressed,
        syncChoiceGroup,
        padCell,
        formatTooltipValue,
        formatXTick,
    };

    // Shared tile-grid rendering used by the system-info and service-info panels
    // (metric-grid / .metric markup in app.css). Both panels poll an endpoint on
    // an interval and render CPU/memory-style tiles; this factors out the parts
    // that don't vary: tile scaffolding, warn/crit thresholds, and error display.

    function levelFor(value, warn, crit) {
        if (value == null) return '';
        if (value >= crit) return 'metric--crit';
        if (value >= warn) return 'metric--warn';
        return '';
    }

    function formatValue(value, suffix = '') {
        return value == null ? '—' : `${value}${suffix}`;
    }

    function barHtmlFor(tile) {
        if (tile.dualBar) {
            return `
                <div class="metric__bar metric__bar--dual">
                    <span class="metric__bar-current" data-role="bar"></span>
                    <span class="metric__bar-avg" data-role="bar-avg" hidden></span>
                    <span class="metric__bar-max" data-role="bar-max" hidden></span>
                </div>`;
        }
        if (tile.bar) {
            return '<div class="metric__bar"><span data-role="bar"></span></div>';
        }
        return '';
    }

    /**
     * Build the metric tiles once. Subsequent updates mutate these in place so
     * values change without tearing down the DOM (no flicker, preserved focus).
     */
    function buildTiles(container, tiles) {
        container.textContent = '';
        for (const tile of tiles) {
            const el = document.createElement('div');
            el.className = 'metric';
            el.dataset.metric = tile.id;
            el.innerHTML = `
                <div class="metric__head">
                    <svg class="metric__icon" aria-hidden="true"><use href="#icon-${tile.icon}"></use></svg>
                    <span class="metric__label">${tile.label}</span>
                </div>
                <div class="metric__value" data-role="value">—</div>
                ${tile.sub !== false ? '<div class="metric__sub" data-role="sub"></div>' : ''}
                ${barHtmlFor(tile)}
            `;
            container.appendChild(el);
        }
    }

    function setBarWidth(el, fill) {
        if (!el) return;
        el.style.width = fill == null ? '0%' : `${Math.min(100, fill)}%`;
    }

    function setBarMarker(el, fill) {
        if (!el) return;
        if (fill == null) {
            el.hidden = true;
            return;
        }
        el.hidden = false;
        el.style.left = `${Math.min(100, fill)}%`;
    }

    function setTile(container, id, { value, sub, level, fill, avgFill, maxFill }) {
        const tile = container.querySelector(`.metric[data-metric="${id}"]`);
        if (!tile) return;
        tile.classList.remove('metric--warn', 'metric--crit');
        if (level) tile.classList.add(level);
        tile.querySelector('[data-role="value"]').textContent = value;
        const subEl = tile.querySelector('[data-role="sub"]');
        if (subEl) subEl.textContent = sub ?? '';
        setBarWidth(tile.querySelector('[data-role="bar"]'), fill);
        setBarMarker(tile.querySelector('[data-role="bar-avg"]'), avgFill);
        setBarMarker(tile.querySelector('[data-role="bar-max"]'), maxFill);
    }

    // Only replace the placeholder while no tiles exist; once tiles are built we
    // keep the last-known values on a transient failure rather than wiping them.
    function showGridError(container, message) {
        if (container.querySelector('.metric')) return;
        container.removeAttribute('aria-busy');
        const p = container.querySelector('.metric-grid__placeholder') || document.createElement('p');
        p.className = 'metric-grid__placeholder';
        p.textContent = message;
        if (!p.isConnected) container.appendChild(p);
    }

    window.SMMetricGrid = {
        levelFor,
        formatValue,
        buildTiles,
        setTile,
        showGridError,
    };
})();
