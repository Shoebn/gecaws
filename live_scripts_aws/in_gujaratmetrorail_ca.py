from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_gujaratmetrorail_ca"
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
tender_no = 0
SCRIPT_NAME = "in_gujaratmetrorail_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_gujaratmetrorail_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 7
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    notice_data.document_type_description = "Awarded Tenders"
       
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass    

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "Gujarat Metro Rail Corporation (GMRC) Limited"
        customer_details_data.org_parent_id = 7784503
        customer_details_data.org_state = "Gujarat"
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        try:
            award_details_data = award_details()
            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
            
            try:
                award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                notice_data.publish_date = award_details_data.award_date
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass
                
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

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = [" https://www.gujaratmetrorail.com/awarded-tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.has-border-color.has-contrast-3-border-color > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.has-border-color.has-contrast-3-border-color > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
