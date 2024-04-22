from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_ndlambe_ca"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_ndlambe_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'za_ndlambe_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'ZAR'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    
    notice_data.notice_text = tender_html_element.get_attribute('outerHTML')
    
    notice_data.document_type_description = 'Bid Awards'
    

    notice_data.notice_url = 'https://ndlambe.gov.za/web/bid_awards/'


    try:
        notice_data.local_title =  tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except:
        pass
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        try:
            notice_data.publish_date = datetime.strptime(publish_date, '%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_data.publish_date = datetime.strptime(publish_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_data.publish_date = datetime.strptime(publish_date, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
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
        award_details_data = award_details()
        award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        award_date = publish_date
        try:
            award_details_data.award_date = datetime.strptime(award_date, '%d %b %Y').strftime('%Y/%m/%d')
        except:
            try:
                award_details_data.award_date = datetime.strptime(award_date, '%d/%m/%Y').strftime('%Y/%m/%d')
            except:
                award_details_data.award_date = datetime.strptime(award_date, '%d %B %Y').strftime('%Y/%m/%d')

        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = ' Ndlambe Municipality'
        customer_details_data.org_parent_id=7559363
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_phone = '+27 (46) 604 5500'
        customer_details_data.org_email = "info@ndlambe.gov.za"
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
page_main = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://ndlambe.gov.za/web/bid_awards/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tablepress-1 > tbody tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tablepress-1 > tbody tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tablepress-1 > tbody tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#tablepress-1 > tbody tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
