from datetime import datetime, timedelta

import pytz
from loguru import logger

from app_sockets.controllers import SocketController


class QRHandler:
    def __init__(self, appeal):
        self.appeal = appeal

    def create_qr_data(self):
        return f'''userId={self.appeal.applier.id}&appealId={self.appeal.id}'''


def handle_date_for_appeals(shift, shift_active_date, by_end: bool = None):
    utc_offset = pytz.timezone(shift.vacancy.timezone).utcoffset(datetime.utcnow()).total_seconds() / 3600
    if by_end:
        time_object = shift.time_end
    else:
        time_object = shift.time_start

    if by_end and shift.time_start > shift.time_end:
        shift_active_date += timedelta(days=1)

    year = shift_active_date.year
    month = str(shift_active_date.month)
    if len(month) == 1:
        month = '0' + month
    day = str(shift_active_date.day)
    if len(day) == 1:
        day = '0' + day

    date = datetime.fromisoformat(f'{year}-{month}-{day} {time_object}')
    date -= timedelta(hours=utc_offset)
    return date


def send_socket_event_on_appeal_statuses(appeal, applier_sockets, managers_sockets):
    # Только самозанятому
    logger.info({
        'type': 'appeal_job_status_updated',
        'prepared_data': {
            'id': appeal.id,
            'jobStatus': appeal.job_status,
        }
    })

    SocketController.send_message_to_many_connections(applier_sockets, {
        'type': 'appeal_job_status_updated',
        'prepared_data': {
            'id': appeal.id,
            'jobStatus': appeal.job_status,
        }
    })

    # И самозанятому и менеджерам релевантным
    sockets = applier_sockets + managers_sockets
    logger.info({
        'type': 'appeal_status_updated',
        'prepared_data': {
            'id': appeal.id,
            'status': appeal.status,
        }
    })
    SocketController.send_message_to_many_connections(sockets, {
        'type': 'appeal_status_updated',
        'prepared_data': {
            'id': appeal.id,
            'status': appeal.status,
        }
    })
