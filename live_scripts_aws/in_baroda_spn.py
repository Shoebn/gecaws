from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_baroda_spn"
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


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_baroda_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_baroda_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.notice_type = 4
    notice_data.procurement_method = 2
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(1) > p > span').text
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "li:nth-child(2) > p > span").text
        notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'


        customer_details_data.org_name = "Bank Of Baroda"
        
        try:
            org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(3) > p').text
            if "Department" in org_address:
                customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(3) > p > span').text
        except:
            pass
        
        try: 
            org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(3) > p').text
            if "Zone" in org_city:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(3) > p > span').text
                customer_details_data.org_state = fn.procedure_mapping("assets/in_baroda_spn_india_states.csv",customer_details_data.org_city)

        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__)) 
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'h6 > span > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        fn.load_page(page_details,notice_data.notice_url,80)  

        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="content"]/section').get_attribute("outerHTML")                     
        except:
            pass
    
        try:
            notice_data.local_title = page_details.find_element(By.XPATH, '//h2/span').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.eauction-main-data-div > ul > li > a'):
                attachments_data = attachments()
                
                attachments_data.external_url = single_record.get_attribute('href') 
                
                attachments_data.file_type = single_record.text.split('.')[-1].strip()
                attachments_data.file_name = single_record.text.split(attachments_data.file_type)[0].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    except Exception as e:
        logging.info("Exception in load_page: {}".format(type(e).__name__)) 
        pass
    
    
    
    notice_data.identifier = str(notice_data.script_name)  +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bankofbaroda.in/tenders/corporate-office","https://www.bankofbaroda.in/tenders/zonal-regional-offices"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        scheight = .1
        while scheight < 9.9: 
            page_main.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
            try:
                button = page_main.find_element(By.XPATH,'//*[@id="tender_loadmore"]/div/button').click() 
            except:
                pass
            scheight += 1 
            time.sleep(2)
            
        for click in range(10):
            load_more = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.loadmore-btn')))
            page_main.execute_script("arguments[0].click();",load_more)
            time.sleep(2)

        try:
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.bob-auction-card')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.bob-auction-card')))[records]
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
