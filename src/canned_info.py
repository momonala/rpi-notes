from src.services import ServiceStatus

# Website links with icons (icon mapping centralized here, not in template)
websites = [
    {
        "name": "task-manager",
        "url": "https://task-manager.mnalavadi.org",
        "description": "Task Manager",
        "icon": "📝",
    },
    {
        "name": "energyMonitor",
        "url": "https://energy-monitor.mnalavadi.org",
        "description": "Energy Monitor",
        "icon": "⚡️",
    },
    {
        "name": "USC-vis",
        "url": "https://usc-vis.mnalavadi.org",
        "description": "USC checkin visualizer",
        "icon": "💪🏾",
    },
    {
        "name": "trainspotter",
        "url": "https://trainspotter.mnalavadi.org",
        "description": "Spot when the next train comes!",
        "icon": "🚃",
    },
    {
        "name": "inspectordetector",
        "url": "https://inspectordetector.mnalavadi.org",
        "description": "Gute Schwarzfahrt!",
        "icon": "🚨",
    },
    {
        "name": "iOS Health Dump",
        "url": "https://ios-health.mnalavadi.org",
        "description": "Data from iOS Health app",
        "icon": "⚕️",
    },
    {
        "name": "pingpong",
        "url": "https://pingpong.mnalavadi.org",
        "description": "Shared Expense Tracker",
        "icon": "🏓",
    },
    {"name": "Trace", "url": "https://trace.mnalavadi.org", "description": "GPS Tracker", "icon": "📍"},
]
websites.sort(key=lambda x: x["name"].lower())

# fmt: off
canned_service_statuses = [
    ServiceStatus(name='projects_atc_tour_extension.service', is_active=True, is_failed=False, uptime='2 days', memory=None, cpu='29.406s', last_error=None, full_status='', project_group='atc'),
    ServiceStatus(name='projects_energy-monitor.service', is_active=True, is_failed=False, uptime='1h 58min', memory=None, cpu='7min 52.884s', last_error="Command '['git', 'add', 'data/energy.db.bk']' returned non-zero exit status 128.", full_status='', project_group='energy-monitor'),
    ServiceStatus(name='projects_flight-calendar-updater.service', is_active=True, is_failed=False, uptime='2h 15min', memory=None, cpu='5.597s', last_error=None, full_status='', project_group='flight-calendar-updater'),
    ServiceStatus(name='projects_incognita_dashboard.service', is_active=True, is_failed=False, uptime='1h 58min', memory=None, cpu='5min 15.362s', last_error=None, full_status='', project_group='incognita'),
    ServiceStatus(name='projects_incognita_data-api.service', is_active=True, is_failed=False, uptime='1h 58min', memory=None, cpu='5.185s', last_error=None, full_status='', project_group='incognita'),
    ServiceStatus(name='projects_incognita_data-backup-scheduler.service', is_active=True, is_failed=False, uptime='1h 58min', memory=None, cpu='17.103s', last_error=None, full_status='', project_group='incognita'),
    ServiceStatus(name='projects_inspector-detector.service', is_active=True, is_failed=False, uptime='1h 30min', memory=None, cpu='26min 58.062s', last_error=None, full_status='', project_group='inspector-detector'),
    ServiceStatus(name='projects_inspector-detector_site.service', is_active=True, is_failed=False, uptime='1h 30min', memory=None, cpu='2min 40.792s', last_error=None, full_status='', project_group='inspector-detector'),
    ServiceStatus(name='projects_ios-health.service', is_active=True, is_failed=False, uptime='1h 54min', memory=None, cpu='46.805s', last_error=None, full_status='', project_group='ios-health'),
    ServiceStatus(name='projects_ios-health_data-backup-scheduler.service', is_active=True, is_failed=False, uptime='1h 56min', memory=None, cpu='309ms', last_error=None, full_status='', project_group='ios-health'),
    ServiceStatus(name='projects_pingpong.service', is_active=True, is_failed=False, uptime='2 days', memory=None, cpu='40min 41.174s', last_error=None, full_status='', project_group='pingpong'),
    ServiceStatus(name='projects_service-monitor.service', is_active=True, is_failed=False, uptime='4h 23min', memory=None, cpu='2min 12.538s', last_error=None, full_status='', project_group='service-monitor'),
    ServiceStatus(name='projects_task-manager.service', is_active=True, is_failed=False, uptime='1h 49min', memory=None, cpu='1min 6.171s', last_error=None, full_status='', project_group='task-manager'),
    ServiceStatus(name='projects_task-manager_data-backup-scheduler.service', is_active=True, is_failed=False, uptime='1h 49min', memory=None, cpu='270ms', last_error=None, full_status='', project_group='task-manager'),
    ServiceStatus(name='projects_trainspotter.service', is_active=True, is_failed=False, uptime='2 days', memory=None, cpu='51min 48.859s', last_error=None, full_status='', project_group='trainspotter'),
    ServiceStatus(name='projects_usc-vis.service', is_active=True, is_failed=False, uptime='1h 20min', memory=None, cpu='1min 2.725s', last_error=None, full_status='', project_group='usc-vis'),
    ServiceStatus(name='projects_usc-vis_data-backup-scheduler.service', is_active=True, is_failed=False, uptime='1h 20min', memory=None, cpu='262ms', last_error=None, full_status='', project_group='usc-vis'),
    ServiceStatus(name='projects_wordle-alarm.service', is_active=True, is_failed=False, uptime='6min', memory=None, cpu='2.417s', last_error=None, full_status='', project_group='wordle-alarm')
]
# fmt: on
