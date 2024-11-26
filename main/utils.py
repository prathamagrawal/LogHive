from main.database import get_session
from main.models import LoggingDetails

def write_to_db(log_data):
    with get_session() as db:
        entry=LoggingDetails(
            service_name=log_data['service'],
            data=log_data['message'],
            timestamp=log_data['timestamp'],
            status=log_data['level'],
        )
        db.add(entry)

#TODO: TRY CATCHES
#TODO: put values back in queue in case of any errors.