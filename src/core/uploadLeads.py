
from src.configurations.instantly import InstantlyAPI
from src.common.logger import get_logger
import concurrent.futures
from src.database.supabase import SupabaseClient
from src.common.utils import get_campaign_details
from src.settings import settings
from src.configurations.justcall import JustCallService
from src.database.mongodb import MongoDBClient
import time

logger = get_logger("Upload Leads")
db = SupabaseClient()
jc = JustCallService()
mongodb_client = MongoDBClient()







class UploadLeads:

    def __init__(self, campaign_id, instantly_api_key):
        self.campaign_id = campaign_id
        self.instantly = InstantlyAPI(instantly_api_key)


    def restore_leads_from_mongodb(self, total_leads):
        limit = 50
        offset = 0
        total_count = 0
        try:
            
            
            while offset < total_leads:
                restored_leads = []
                restore_leads = []

                # Get all the leads from the mongodb and add to the restore_leads list
                leads = mongodb_client.get_all_from_recycled_leads(offset,limit)
                for lead in leads:
                    restore_leads.append({"email": lead.get('email'), "custom_variables": lead.get('custom_variables')})
                    restored_leads.append(lead.get('email'))

                

                    total_count += 1
                    if total_count >= total_leads:
                        break

                logger.info(f"restored_leads emails {restored_leads}")
                logger.info(f"restore_leads {len(restore_leads)}")
                logger.info(f"total_count for restoration {total_count}")


                # Modification for instantly api
                self.instantly.delete_lead_from_campaign(lead_list=restored_leads, campaign_id=self.campaign_id)
                self.instantly.add_lead_to_campaign(lead_list=restore_leads, campaign_id=self.campaign_id)

                # Modification for database
                self.update_or_delete_leads(restored_leads, "old_restore")

                    

                offset += limit

            logger.info(f"total lead count for restoration {total_count}")
            return total_count
        except Exception as e:
            logger.error(f"Error in restore_leads_from_mongodb: {e}")
            return total_count

    def new_enriched_leads(self, total_leads):
        try:

            limit = 50
            offset = 0
            total_count = 0
            
            while offset < total_leads:
                new_leads = []
                new_leads_email = []
                leads = db.get_new_enriched_leads(offset,limit).data
                for lead in leads:
                    new_leads.append({"email": lead.get('email'), "custom_variables": {"AE": lead.get('ae'), "firstName": lead.get('firstName'), 
                    "lastName": lead.get('lastName'), "Question 1": lead.get('question1'), "Question 2": lead.get('question2'),
                    "Question 3": lead.get('question3'), "Question 4": lead.get('question4'), "Course Name": lead.get('courseName'), 
                    "Course Description": lead.get('courseDescription'), "University Name": lead.get('universityName'), "FA24 Course Code": lead.get('courseCode')}})
                    new_leads_email.append(lead.get('email'))
                
             
    

                    total_count += 1
                    if total_count >= total_leads:
                        break
                
                logger.info(f"new_leads_email enriched {new_leads_email}")
                logger.info(f"new_leads enriched {len(new_leads)}")


                logger.info(f"total_count for new_enriched {total_count}")

                self.instantly.delete_lead_from_campaign(lead_list=new_leads_email, campaign_id=self.campaign_id)
                self.instantly.add_lead_to_campaign(lead_list=new_leads, campaign_id=self.campaign_id)

                # here we update the leads in the database
                self.update_or_delete_leads(new_leads_email, "new_enriched")

                offset += limit


            return total_count
        except Exception as e:
            logger.error(f"Error in new_enriched_leads: {e}")

    def update_or_delete_leads(self, email_list, flag):
        function_used = self.update_enriched_leads if flag == "new_enriched" else self.delete_restore_leads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_lead = {executor.submit(function_used, index, email): email for index, email in enumerate(email_list)}
            for index, future in enumerate(concurrent.futures.as_completed(future_to_lead)):
                try:
                    future.result() 
                    if (index + 1) % 50 == 0:  
                        time.sleep(1) 
                except Exception as e:
                    lead = future_to_lead[future]
                    logger.error(f"Error in processing lead {lead}: {e}")  

    def update_enriched_leads(self, index, email):
        db.update_new_enrich_leads({"downloaded": True}, email)
        logger.info(f"Updated lead {index + 1} {email}")  

    def delete_restore_leads(self, index, email):
        mongodb_client.delete_by_email(email)
        logger.info(f"Deleted lead {index + 1} {email}")  




def added_leads_to_campaign(campaign_id):
    try:
            _, _, instantly_api_key,_ = get_campaign_details(campaign_id)
            total = int(settings.TOTAL_LEADS)
            new = int(settings.NEW)
     
            if new == 0 or new > total:
                new = int(total/2)
                
            restore_total = total - new
            logger.info(f"total leads {total}  - new {new} -  restore {restore_total}")
            ul = UploadLeads(campaign_id, instantly_api_key)
            new_added_leads = ul.new_enriched_leads(new)
            restore_total += (new - new_added_leads)
            restore_added_leads = ul.restore_leads_from_mongodb(restore_total)
            logger.info(f"total leads {total}  - total added new {new_added_leads} -  total restore {restore_added_leads}")
            return total, new_added_leads, restore_added_leads
            
    except Exception as e:
            logger.error(f"Error in added_leads_to_campaign: {e}")