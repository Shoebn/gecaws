from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_bput_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_bput_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)

output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'INR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.script_name = "in_bput_spn"
    
    
    
    notice_data.document_type_description = "Tenders"
          
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
        if "Corrigendum" in notice_data.local_title:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
   
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        notice_data.publish_date = threshold
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
   
            
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "Biju Patnaik University Of Technology"
        customer_details_data.org_parent_id ="6539737"        
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.notice_url = url
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:  
        attachments_data = attachments()

        attachments_data.file_name = "tender document"


        external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').click()
        time.sleep(3)
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)
        atach_url = page_main.current_url
        attachments_data.external_url = atach_url
        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])
        time.sleep(5)
        
        if attachments_data.external_url !='':
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)      
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.bput.ac.in/tenders.php'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):#5
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_chec2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[2]'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/table/tbody/tr[2]'),page_check2))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
