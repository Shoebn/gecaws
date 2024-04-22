from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_vrprovincia"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_vrprovincia"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_vrprovincia'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
 

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'article > h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr:nth-child(1) > td").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr:nth-child(2) > td").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:  
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td').text
        if 'Beni e servizi' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Lavori pubblici' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.type_of_procedure = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(5) > td').text
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass
 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'article > h3 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="main"]/div/div[3]/div/div/article').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    try:
        notice_no = notice_data.notice_url
        notice_data.notice_no = re.findall('\d{3}',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    try:
        notice_summary_english = page_details.find_element(By.CSS_SELECTOR,'article > p').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR,'article > p').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
 
    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="main"]/div/div[3]/div/div/article/section[2]'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'PROVINCIA DI VERONA'
            customer_details_data.org_parent_id = '1325880'
            customer_details_data.org_country = 'IT'
   
            try:
                customer_details_data.org_description = single_record.find_element(By.XPATH, '//*[@id="main"]/div/div[3]/div/div/article/section[2]/table/tbody/tr[1]/td').text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[@id="main"]/div/div[3]/div/div/article/section[2]/table/tbody/tr[2]/td').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
  
            try:
                customer_details_data.org_address = single_record.find_element(By.XPATH, '//*[@id="main"]/div/div[3]/div/div/article/section[2]/table/tbody/tr[3]/td').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
      
            try:
                org_phone = single_record.find_element(By.XPATH, '//*[@id="main"]/div/div[3]/div/div/article/section[2]/table/tbody/tr[4]/td').text
                customer_details_data.org_phone = re.findall('\d+',org_phone )[0]
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
 
            try:
                customer_details_data.org_email = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass



    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tbody > tr:nth-child(n)'):
            attachments_data = attachments() 
            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > span > a').get_attribute('href')
            
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) ').text
           
  
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
  
            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
      
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span img').get_attribute('alt').split('Formato ')[1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://portale.provincia.vr.it/index.php/ente/bandi"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div[3]/div/div/article/section/article')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div[3]/div/div/article/section/article')))[records]
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
