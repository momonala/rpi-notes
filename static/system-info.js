(function() {
    'use strict';

    const { levelFor, formatValue, buildTiles, setTile, showGridError } = window.SMMetricGrid;

    const REFRESH_INTERVAL = 10000;

    // Usage thresholds (percent) at which a metric reads as elevated / critical.
    const WARN_PCT = 60;
    const CRIT_PCT = 85;
    // Raspberry Pi soft-throttles around 80°C; warn well before that.
    const WARN_TEMP_C = 60;
    const CRIT_TEMP_C = 75;
    // Temperature bar maps this Celsius window onto 0–100% fill.
    const TEMP_BAR_MIN_C = 40;
    const TEMP_BAR_MAX_C = 80;

    // Same order as the history chart series.
    const TILES = [
        { id: 'cpu', icon: 'cpu', label: 'CPU', bar: true },
        { id: 'disk', icon: 'disk', label: 'Disk', bar: true },
        { id: 'temperature', icon: 'thermometer', label: 'Temperature', dualBar: true },
        { id: 'memory', icon: 'memory', label: 'Memory', bar: true },
    ];

    let timer = null;

    function tempFill(celsius) {
        if (celsius == null) return null;
        const span = TEMP_BAR_MAX_C - TEMP_BAR_MIN_C;
        return Math.min(100, Math.max(0, ((celsius - TEMP_BAR_MIN_C) / span) * 100));
    }

    function render(container, info) {
        if (!container.querySelector('.metric')) buildTiles(container, TILES);
        container.removeAttribute('aria-busy');

        setTile(container, 'cpu', {
            value: formatValue(info.cpu_percent, '%'),
            sub: [
                info.load_avg != null ? `load ${info.load_avg}` : null,
                info.cpu_count ? `${info.cpu_count} cores` : null,
            ].filter(Boolean).join(' · '),
            level: levelFor(info.cpu_percent, WARN_PCT, CRIT_PCT),
            fill: info.cpu_percent,
        });

        setTile(container, 'disk', {
            value: formatValue(info.disk_used_pct, '%'),
            sub: (info.disk_used_gb != null && info.disk_total_gb != null)
                ? `${info.disk_used_gb} / ${info.disk_total_gb} GB`
                : '',
            level: levelFor(info.disk_used_pct, WARN_PCT, CRIT_PCT),
            fill: info.disk_used_pct,
        });

        setTile(container, 'temperature', {
            value: formatValue(info.temperature_c, '°C'),
            sub: info.temperature_avg_24h != null
                ? `avg ${formatValue(info.temperature_avg_24h, '°C')}`
                : '',
            level: levelFor(info.temperature_c, WARN_TEMP_C, CRIT_TEMP_C),
            fill: tempFill(info.temperature_c),
            avgFill: tempFill(info.temperature_avg_24h),
            maxFill: tempFill(info.temperature_max_24h),
        });

        setTile(container, 'memory', {
            value: formatValue(info.memory_used_pct, '%'),
            sub: (info.memory_used_mb != null && info.memory_total_mb != null)
                ? `${(info.memory_used_mb / 1024).toFixed(1)} / ${(info.memory_total_mb / 1024).toFixed(1)} GB`
                : '',
            level: levelFor(info.memory_used_pct, WARN_PCT, CRIT_PCT),
            fill: info.memory_used_pct,
        });
    }

    async function refresh(container) {
        try {
            const res = await fetch('/api/system-info');
            if (!res.ok) {
                showGridError(container, `Failed to load system info (HTTP ${res.status}).`);
                throw new Error(`system-info ${res.status}`);
            }
            render(container, await res.json());
        } catch (err) {
            console.error('System info refresh failed:', err);
            showGridError(container, `Could not load system info — ${err.message}.`);
        }
    }

    function init() {
        const container = document.getElementById('systemMetrics');
        if (!container) return;
        refresh(container);
        timer = setInterval(() => refresh(container), REFRESH_INTERVAL);
    }

    window.ServiceMonitorSystemInfo = { init };
})();
