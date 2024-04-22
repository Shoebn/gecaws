from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "rw_reg_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "rw_reg_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'rw_reg_spn'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RW'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'RWF'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = 'https://www.reg.rw/public-information/tenders/new-tenders/'
    
    # Onsite Field -None
    # Onsite Comment -Note:if the tender title start with "Corrigendum" or "Addendum" or "amendments"or "Extension of" notice type will be 16 or 
     #"EXPRESSION OF INTEREST", "EOI", "Invitation for Expression of Interest" will be notice type 5"    
    
    # Onsite Field -Title startswith
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
        if 'Corrigendum' in notice_data.local_title or 'Addendum' in notice_data.local_title or 'amendments' in notice_data.local_title or 'Extension of' in notice_data.local_title:
            notice_data.notice_type = 16
        elif 'EXPRESSION OF INTEREST' in notice_data.local_title or 'EOI' in notice_data.local_title or 'Invitation for Expression of Interest' in notice_data.local_title:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
#     notice_data.publish_date = 'Take it as Threshold'
    
    # Onsite Field -Due Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(4)").text
        notice_deadline_day = re.findall('\d+',notice_deadline)[0]
        notice_deadline_year = re.findall('\w+ \d{4}',notice_deadline)[0]
        notice_deadline_date = notice_deadline_day+' '+notice_deadline_year
        notice_data.notice_deadline = datetime.strptime(notice_deadline_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
   
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
# Onsite Field -Download
# Onsite Comment -None

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Document'

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(5) > a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'RW'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Category
        # Onsite Comment -Note:if org_name have keyword "EDCL" in given selector then take  org_name as "Energy Development Corporation Limited " or if "EUCL" in given selector then take  org_name as "Energy Utility Corporation Limited"

        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3)').text
        if "EDCL" in org_name:
            customer_details_data.org_name = 'Energy Development Corporation Limited'
        elif "EUCL" in org_name:
            customer_details_data.org_name = 'Energy Utility Corporation Limited'
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)  
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.reg.rw/public-information/tenders/new-tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(3)
        
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="new_tendetable"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="new_tendetable"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
        except:
            logging.info("No new record")
            break


    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
