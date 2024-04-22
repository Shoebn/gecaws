from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_kzntransport_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_kzntransport_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'za_kzntransport_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'ZAR'
    
    notice_data.main_language = 'AR'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    try:
        notice_number = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > p > a').text
        notice_no = re.findall(r'[A-Za-z]{3}\d{5}/\d{5}/\d{2}/[A-Za-z]{3}/[A-Za-z]{3}/\d{2}/[A-Za-z]-?\d*', notice_number.strip())[0]
        notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > p > a').text
        notice_data.notice_title = GoogleTranslator(source='es', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > p').text.split('Date published:')[1].strip()
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2) > p').text.split('Closing Date:')[1].split('\n')[0].strip()
        notice_deadline = re.findall(r'\d{1,2} \w+ \d{4} at \d{1,2}h\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y at %Hh%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

        
    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "PROVINCE OF KWAZULU NATAL"
        customer_details_data.org_parent_id = 7732887
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'AR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        attachments_data = attachments()
        attachments_data.external_url =  tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > p > a').get_attribute('href')
        attachments_data.file_name = "Tender Document"
        attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
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
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://www.kzntransport.gov.za/tenders_bids/available_tenders_2024.htm"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr/td[1]/table/tbody/tr/td/blockquote/table/tbody/tr[3]'))).text
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr/td[1]/table/tbody/tr/td/blockquote/table/tbody/tr')))
            length = len(rows)
            for records in range(2,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr/td[1]/table/tbody/tr/td/blockquote/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
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