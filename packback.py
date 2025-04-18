
from apscheduler.schedulers.background import BackgroundScheduler
import time
from src.common.logger import get_logger

from packback_csv import process_csv_with_concurrency



logger = get_logger(__name__)



##################################################################
##############   function for packback lead course  ##############
##################################################################

def packback_lead_course():
    try:
        start_time = time.time()  # Start time
        logger.info("packback_lead_course is running")
        process_csv_with_concurrency()
        elapsed_time = time.time() - start_time  # Calculate elapsed time

        logger.info("packback_lead_course is completed in %.2f seconds", elapsed_time)

    except Exception as e:
        logger.exception("Exception occurred packback_lead_course %s", e)


if __name__ == "__main__":
    try:
        scheduler = BackgroundScheduler()
        logger.info("packback scheduler is running")
        # scheduler.add_job(packback_lead_course, 'interval', minutes=10)
        scheduler.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
 



# +16504603511
# +19726669892
# +14156926240
# +13372219750
# +14157415816