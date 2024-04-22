from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_start_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_start_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    
    notice_data.procurement_method = 2
    notice_data.script_name = 'it_start_spn'
    notice_data.main_language = 'IT'
    notice_data.class_at_source = 'CPV'
        
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
        
    notice_data.currency = 'EUR'
    notice_data.notice_type = 4
    notice_data.document_type_description = 'Bandi e avvisi'


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td.amount').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(notice_data.est_amount)
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'span.protocolId').text
        notice_data.tender_id = notice_data.notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
  
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href") 
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

    try: #02/04/2024
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text.split('-')[0]
        try:
            customer_main_activity = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text.replace(customer_details_data.org_name,'').replace('-','').strip()
            customer_details_data.customer_main_activity = customer_main_activity
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.contractType').text
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td.contractType').text
        if 'Servizi' in notice_contract_type or 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Lavori pubblici' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
                          
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
    urls = ['https://start.toscana.it/index/index/hideAnnouncements/true'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,30):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Contenuto"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li:nth-child(12) > a')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
