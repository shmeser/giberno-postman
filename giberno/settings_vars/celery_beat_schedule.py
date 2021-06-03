from celery.schedules import crontab

celery_beat_schedule = {
    # 'check_subscription': {
    #     'task': 'subscriptions.tasks.check_subscription',
    #     'schedule': crontab(hour='*', minute='0', day_of_week='*')
    # },
    'update_appeals': {
        'task': 'app_market.tasks.update_appeals',
        'schedule': crontab(minute='*')
    },
    'auto_switch_to_bot': {
        'task': 'app_chats.tasks.check_abandoned_chats',
        'schedule': crontab(minute='*')
    }
}
