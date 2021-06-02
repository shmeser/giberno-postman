from celery.schedules import crontab

celery_beat_schedule = {
    # 'check_subscription': {
    #     'task': 'subscriptions.tasks.check_subscription',
    #     'schedule': crontab(hour='*', minute='0', day_of_week='*')
    # },
    'notify_self_employed_users_about_soon_job': {
        'task': 'app_market.tasks.notify_user_about_job_status',
        'schedule': crontab(minute='*')
    },
    'cancel_overdue_appeals': {
        'task': 'app_market.tasks.cancel_overdue_appeals',
        'schedule': crontab(minute='*')
    },
    'complete_appeals_by_end_time': {
        'task': 'app_market.tasks.complete_appeals_by_end_time',
        'schedule': crontab(minute='*')
    },
    'auto_switch_to_bot': {
        'task': 'app_chats.tasks.check_abandoned_chats',
        'schedule': crontab(minute='*')
    }
}
