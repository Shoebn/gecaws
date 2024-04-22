
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "il_iaa_ca"
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
SCRIPT_NAME = "il_iaa_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'il_iaa_ca'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IL'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'ILS'
    notice_data.main_language = 'HE'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    

    notice_data.local_title  = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    
    try:     
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').get_attribute("innerHTML")   
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass  
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div > a').get_attribute("href") 
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
        time.sleep(5)
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#toTop > div > div').get_attribute("outerHTML")   
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
       
    try:
        lot_details_data = lot_details()

        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        try:
            contract_date = page_details.find_element(By.XPATH, '//*[contains(text(),"תקופת ההתקשרות:")]//following::td[1]').text  

            contract_start_date = contract_date.split('-')[1].strip()
            contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(lot_details_data.contract_start_date)
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass        

        try:
            contract_end_date = contract_date.split('-')[0].strip()
            contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(lot_details_data.contract_end_date)
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass     

        try:
            award_details_data = award_details()

            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"שם ספק/לקוח:")]//following::td[1]').text  
            
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
    
    try: 
        attachments_data = attachments()

        attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"פרטי ההודעה:")]//following::a[1]').text

        attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"פרטי ההודעה:")]//following::a[1]').get_attribute('href')
        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
        except:
            pass
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "ISRAEL AIRPORTS AUTHORITY"
        customer_details_data.org_parent_id = 7636991

        customer_details_data.org_country = 'IL'
        customer_details_data.org_language = 'HE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass       

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_type) +  str(notice_data.notice_url)
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
    urls = ["https://www.iaa.gov.il/tenders-and-contracts/active-tenders#notifications"] 
    for url in urls:
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(3)

        try:
            ckeck_box_click = WebDriverWait(page_main, 150).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.modal-footer > div > div > div:nth-child(1) > div > label"))) 
            page_main.execute_script("arguments[0].click();",ckeck_box_click)
            time.sleep(3)
            logging.info("ckeck_box_click")
        except:
            pass

        try:
            approval_click = WebDriverWait(page_main, 150).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#modal-tenders-terms_of_use > div > div > div.modal-footer > div > div > div:nth-child(2) > button")))  
            page_main.execute_script("arguments[0].click();",approval_click)
            time.sleep(3)
            logging.info("approval_click")
        except:
            pass

        try:
            rows = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tab--notifications > div > div > table > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tab--notifications > div > div > table > tbody > tr')))[records]  
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
