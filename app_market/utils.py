from loguru import logger

from app_sockets.controllers import SocketController


class QRHandler:
    def __init__(self, appeal):
        self.appeal = appeal

    def create_qr_data(self):
        return f'''userId={self.appeal.applier.id}&appealId={self.appeal.id}'''


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
