
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
import time
from src.common.logger import get_logger

from packback_csv import process_csv_concurrent



logger = get_logger('Packback-lead-course')



##################################################################
##############   function for packback lead course  ##############
##################################################################

def packback_lead_course():
    try:
        start_time = time.time()  # Start time
        logger.info("packback_lead_course is running")
        process_csv_concurrent()
        elapsed_time = time.time() - start_time  # Calculate elapsed time

        logger.info("packback_lead_course is completed in %.2f seconds", elapsed_time)

    except Exception as e:
        logger.exception("Exception occurred packback_lead_course %s", e)


if __name__ == "__main__":
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(process_csv_concurrent, 'interval', minutes=15)
        scheduler.start()
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
