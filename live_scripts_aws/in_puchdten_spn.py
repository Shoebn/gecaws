from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_puchdten_spn"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_puchdten_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global even_rows
    global odd_rows
    global first_row
    notice_data = tender()

    notice_data.script_name = 'in_puchdten_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note:Note:If the tender title start with "Corrigendum" or "Extension" notice type will be 16
    notice_data.notice_type = 4
    notice_data.notice_url = 'https://tenders.puchd.ac.in/' 
    
    # Onsite Field -Tender
    # Onsite Comment -Note:Take a text

    try:
        notice_data.local_title = page_main.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div[2]/table/tbody/tr['+str(even_rows)+']/td[1]/a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div[2]/table/tbody/tr['+str(odd_rows)+']/td').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Issue
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div[2]/table/tbody/tr['+str(even_rows)+']/td[2]').text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -Due Date & Time
#     # Onsite Comment -None

    try:
        deadline_date = page_main.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div[2]/table/tbody/tr['+str(even_rows)+']/td[3]').text
        deadline = re.findall('\d+-\d+-\d{4}',deadline_date)[0]
        deadline_time = re.findall('\d+:\d+',deadline_date)[0]
        notice_deadline = str(deadline) + ' ' + str(deadline_time)
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Date of Opening & Time
#     # Onsite Comment -None

    try:
        document_opening_time = page_main.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div[2]/table/tbody/tr['+str(even_rows)+']/td[3]').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    notice_data.notice_text = notice_data.notice_title + ' ' + notice_data.local_description  

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Document'
    # Onsite Field -Tender
    # Onsite Comment -None

        attachments_data.external_url = page_main.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div[2]/table/tbody/tr['+str(even_rows)+']/td[1]/a').get_attribute('href')


        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'PANJAB UNIVERSITY'
        customer_details_data.org_parent_id = '7522390'
    # Onsite Field -Tender
    # Onsite Comment -None
        customer_details_data.org_address = page_main.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div[2]/table/tbody/tr['+str(first_row)+']/td/b').text
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass        
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return

    even_rows += 3
    odd_rows += 3
    first_row += 3
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tenders.puchd.ac.in/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="tdfaculty"]/ancestor::tr')))
        first_row = 2
        even_rows = 3
        odd_rows =  4
        try:
            for records in range(0,40):
                extract_and_save_notice(records)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
