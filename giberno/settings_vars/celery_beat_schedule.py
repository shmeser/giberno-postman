from celery.schedules import crontab

celery_beat_schedule = {
    'auto_control_timed_shifts': {
        'task': 'app_market.tasks.auto_control_timed_shifts',
        'schedule': crontab(minute='*')
    },
    'update_appeals': {
        'task': 'app_market.tasks.update_appeals',
        'schedule': crontab(minute='*')
    },
    'auto_switch_to_bot': {
        'task': 'app_chats.tasks.check_abandoned_chats',
        'schedule': crontab(minute='*')
    }
}
