from celery.schedules import crontab

celery_beat_schedule = {
    'auto_control_timed_shifts': {
        'task': 'app_market.tasks.auto_control_timed_shifts',
        'schedule': crontab(minute='*')
    },
    'auto_control_shifts': {
        'task': 'app_market.tasks.auto_control_shifts',
        'schedule': crontab(minute='*/2')  # каждые 2 минуты
    },
    'update_appeals': {
        'task': 'app_market.tasks.update_appeals',
        'schedule': crontab(minute='*')
    },
    'auto_switch_to_bot': {
        'task': 'app_chats.tasks.check_abandoned_chats',
        'schedule': crontab(minute='*')
    },
    'check_users_daily_tasks_on_completed_shifts': {
        'task': 'app_games.tasks.check_users_daily_tasks_on_completed_shifts',
        'schedule': crontab(minute='*/3')
    }
}
