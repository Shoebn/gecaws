from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_welthungerhilfe_spn"
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
SCRIPT_NAME = "de_welthungerhilfe_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_welthungerhilfe_spn'

    notice_data.main_language = 'EN'

    notice_data.currency = 'EUR'

    notice_data.notice_type = 4
   
    notice_data.procurement_method = 2

    notice_data.document_type_description = 'Current calls for tender'
    
    try:
        performance_country_data = performance_country()
        performance1 = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tender__list__item__client').text
        performance = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tender__list__item__client').text.split(' ')[-1]
        if 'Central African Republic' in performance1:
            customer_details_data.org_country = 'CF'
        else:
            performance_country_data.performance_country= fn.procedure_mapping("assets/de_welthungerhilfe_spn.csv", performance)
        notice_data.performance_country.append(performance_country_data)
    except:
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'DE'
        notice_data.performance_country.append(performance_country_data)     
    
    # Onsite Field - Date of Publication: 
    # Onsite Comment -
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.tender__list__item__date").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    # Onsite Field -Tender Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tender__list__item__title ').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

     
    # Onsite Field -Response Deadline (CET)
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.tender__list__item__deadline ").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass


    # Onsite Field - Read more
    # Onsite Comment -

    try:
        notice_data.additional_tender_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.tender__list__item__cta > a').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass

    notice_data.notice_url = "https://www.welthungerhilfe.org/tenders/"

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

 # Onsite Field -Department Name
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_language = 'EN'
        customer_details_data.org_parent_id = 7571321

        # Onsite Field - Contracting Authority:
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tender__list__item__client ').text.split(':')[1].split()[0]

        # Onsite Field -Contracting Authority:
        # Onsite Comment -split only org_country for ex."Welthungerhilfe Mali" , here take only "Mali"

        try:
            org_country1 = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tender__list__item__client').text
            org_country = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tender__list__item__client').text.split(' ')[-1]
            if 'Central African Republic' in org_country1:
                customer_details_data.org_country = 'CF'
            else:
                customer_details_data.org_country = fn.procedure_mapping("assets/de_welthungerhilfe_spn.csv", org_country )
            
        except Exception as e:
            logging.info("Exception in org_country: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.publish_date) +  str(notice_data.local_title) + str(notice_data.notice_deadline)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
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
    urls = ["https://www.welthungerhilfe.org/tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        time.sleep(10)
        logging.info('----------------------------------')
        logging.info(url)
    
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="c28671"]/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="c28671"]/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="c28671"]/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="c28671"]/div/div'),page_check))
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
