from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_kznhealth_ca"
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
SCRIPT_NAME = "za_kznhealth_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    
    
    if 'Health Facility' not in tender_html_element.text and len(tender_html_element.text)>10:    
    
        notice_data = tender()

        notice_data.script_name = 'za_kznhealth_ca'

        notice_data.main_language = 'EN'

        performance_country_data = performance_country()
        performance_country_data.performance_country = 'ZA'
        notice_data.performance_country.append(performance_country_data)

        notice_data.currency = 'ZAR'

        notice_data.procurement_method = 2

        notice_data.notice_type = 7
        notice_data.document_type_description = "Quotation Award"

        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        notice_data.notice_title  = notice_data.local_title  
        
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text 
            notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            lot_details_data = lot_details()

            lot_details_data.lot_number = 1
            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
                
            try:
                award_details_data = award_details()
                award_date = publish_date
                award_details_data.award_date = datetime.strptime(award_date,'%Y/%m/%d').strftime('%Y/%m/%d')

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data) 
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass


        notice_data.notice_url = "https://www.kznhealth.gov.za/SCM/Award/2024/February-2024.htm"
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text 
        notice_data.notice_no = notice_no.split('.pdf')[0]


        try:
            customer_details_data = customer_details()
            customer_details_data.org_country = 'ZA'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_parent_id = 6991344
            customer_details_data.org_name = "KWAZULU-NATAL DEPARTMENT HEALTH"
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text             
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass    
            
        try:              
            attachments_data = attachments()
            attachments_data.file_type = 'pdf'
            attachments_data.file_name = notice_data.notice_no
            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href") 
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass        

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://www.kznhealth.gov.za/SCM/quotation-award.htm"] 
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:   
            Quotation_Awards_2024_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//button[contains(@class,'btn btn-success dropdown-toggle')])[1]")))
            page_main.execute_script("arguments[0].click();",Quotation_Awards_2024_click)
            logging.info("Quotation_Awards_2024_click")
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in Quotation_Awards_2024_click: {}".format(type(e).__name__))
            logging.inf        

        try:   
            February_2024_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div:nth-child(4) > div > ul > li:nth-child(1) > a")))
            page_main.execute_script("arguments[0].click();",February_2024_click)
            logging.info("February_2024_click")
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in February_2024_click: {}".format(type(e).__name__))
            pass

        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.container-fluid > div > div.col-sm-12 > table > tbody > tr'))).text
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.container-fluid > div > div.col-sm-12 > table > tbody > tr')))
        length = len(rows)
        for records in range(1,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.container-fluid > div > div.col-sm-12 > table > tbody > tr')))[records] 
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()    
    output_json_file.copyFinalJSONToServer(output_json_folder)
