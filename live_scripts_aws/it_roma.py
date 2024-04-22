from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_roma"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_roma"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
               
    notice_data.main_language = 'IT'
    notice_data.script_name = 'it_roma'
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#main div > p.List-title > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#main  div > p.List-title').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -None
#     # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > p.List-date").text
        notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)
        notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    logging.info(notice_data.notice_deadline)
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
#     # Onsite Field -Lotto
#     # Onsite Comment -Just select "Tender no" from "lotto"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > p:nth-child(4)').text.split('Gara')[1].split('-')[0].strip()
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('=')[-1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Tipologia
    # Onsite Comment -for "Servizi = service Forniture = supply Lavori pubblici=Works" as there are various types

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(1) > a').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
        
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div:nth-child(2) > div > div').get_attribute("outerHTML")      
        notice_text=page_details.find_element(By.CSS_SELECTOR, '#main > div:nth-child(2) > div > div').text
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    
# # Onsite Field -None
# # Onsite Comment -None
    customer_details_data = customer_details()
    customer_details_data.org_country = 'IT'
    customer_details_data.org_language = 'IT'
    # Onsite Field -Municipio, Da
    # Onsite Comment -just select "Da" and "Muncipio" from the body
    try:
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.List-category').text.split('Municipio:')[1]
    except:
        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.List-category').text.split('Da:')[1] 
        except:
            customer_details_data.org_name = 'ROMA'
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'p > a'))):
            external_url = single_record.get_attribute('href')
            if 'documents/' in external_url:
                attachments_data = attachments()
                attachments_data.file_name = single_record.text
                attachments_data.external_url = single_record.get_attribute('href')
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
                
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome( options=options)
page_details = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.comune.roma.it/web/it/bandi-e-concorsi.page#"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,50):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main"]/div[2]/div/div/div[3]/div[1]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/div/div/div[3]/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/div/div/div[3]/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="main"]/div[2]/div/div/div[3]/div[1]'),page_check))
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
