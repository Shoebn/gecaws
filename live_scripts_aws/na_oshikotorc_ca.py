from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "na_oshikotorc_ca"
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
SCRIPT_NAME = "na_oshikotorc_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -click on "Bids Awarded" to get contract award data 
    notice_data.script_name = 'na_oshikotorc_ca'

    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NA'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'NAD'

    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    
    notice_data.notice_url = url

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, '#tab3 > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DESCRIPTION
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Standstill start
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "th:nth-child(2)").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if '-' in publish_date:
        return

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None
    
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.text                    
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Oshikoto Regional Council - Namibia'
        customer_details_data.org_parent_id = '7295471'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'NA'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -DOWNLOADS
# Onsite Comment -None

    try:              
        attachments_data = attachments()
        # Onsite Field -DOWNLOADS
        # Onsite Comment -take in textform

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(6)').text
        # Onsite Field -DOWNLOADS
        # Onsite Comment -take url from selector

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(6) > a').get_attribute('href')
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://oshikotorc.gov.na/procurement'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:   
            bids_awarded_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#tab3')))
            page_main.execute_script("arguments[0].click();",bids_awarded_click)
        except:
            pass

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tabPanel3"]/div/div/div/div/div[1]/table/thead/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tabPanel3"]/div/div/div/div/div[1]/table/thead/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tabPanel3"]/div/div/div/div/div[1]/table/thead/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tabPanel3"]/div/div/div/div/div[1]/table/thead/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
