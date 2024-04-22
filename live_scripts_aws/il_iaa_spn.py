
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "il_iaa_spn"
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
SCRIPT_NAME = "il_iaa_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'il_iaa_spn'
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
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text        
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass  
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        time.sleep
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#toTop > div > div').get_attribute("outerHTML")    
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"מספר מכרז:")]//following::td[1]').text  
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass  
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"תאריך אחרון להגשה:")]//following::td[1]').text  
        notice_deadline_1 = notice_deadline.split('שעה:')[0].strip()
        notice_deadline_2 = notice_deadline.split('שעה:')[-1].strip()   
        notice_deadline_3 = notice_deadline_1 +' '+ notice_deadline_2
        notice_data.notice_deadline = datetime.strptime(notice_deadline_3,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass    

    try:              
        attachment_text = page_details.find_element(By.CSS_SELECTOR,'#toTop > div > div.box-wrapper.shadow.text-21 > div:nth-child(2) > table > tbody > tr:nth-child(5) > td').text  
        try:
            notice_url_2 = page_details.find_element(By.CSS_SELECTOR, '#toTop > div > div.box-wrapper.shadow.text-21 > div:nth-child(2) > table > tbody > tr:nth-child(5) > td > div:nth-child(1) > a').get_attribute("href")                     
            fn.load_page(page_details2,notice_url_2,80)
            logging.info(notice_url_2)
            notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#toTop > div > section').get_attribute("outerHTML") 
        except Exception as e:
            logging.info("Exception in notice_url_2: {}".format(type(e).__name__))
            pass
        
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#toTop > div > div.box-wrapper.shadow.text-21 > div:nth-child(2) > table > tbody > tr:nth-child(5) > td > div'):   
            time.sleep(3)
            external_url = single_record.find_element(By.CSS_SELECTOR,'a').get_attribute('href') 
            if 'pdf' in external_url:
                attachments_data = attachments()
                attachments_data.external_url = external_url
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

                try:
                    attachments_data.file_type = external_url.split('.')[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass          
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except:
        try:          
            try:
                notice_url_2 = page_details.find_element(By.CSS_SELECTOR, '#toTop > div > div.box-wrapper.shadow.text-21 > div:nth-child(2) > table > tbody > tr:nth-child(4) > td > div:nth-child(1) > a').get_attribute("href")                     
                fn.load_page(page_details2,notice_url_2,80)
                logging.info(notice_url_2)
                notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#toTop > div > section').get_attribute("outerHTML") 
            except Exception as e:
                logging.info("Exception in notice_url_2: {}".format(type(e).__name__))
                pass
            
            for single_record in page_details.find_elements(By.CSS_SELECTOR,'#toTop > div > div.box-wrapper.shadow.text-21 > div:nth-child(2) > table > tbody > tr:nth-child(4) > td > div'):   
                external_url = single_record.find_element(By.CSS_SELECTOR,'a').get_attribute('href') 
                if 'pdf' in external_url:
                    attachments_data = attachments()
                    attachments_data.external_url = external_url
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

                    try:
                        attachments_data.file_type = external_url.split('.')[-1]
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
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
        customer_details_text = page_details2.find_element(By.CSS_SELECTOR,'#toTop > div > section > p:nth-child(5)').text  
        customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', customer_details_text)[0]
        try:
            customer_details_data.org_phone = re.findall(r'\d{2}-\d{7}/\d{3}', customer_details_text)[0]
        except:
            customer_details_data.org_phone = re.findall(r'\d{2}-\d{7}', customer_details_text)[0]   
        customer_details_data.org_country = 'IL'
        customer_details_data.org_language = 'HE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass       
   

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details2 = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.iaa.gov.il/tenders-and-contracts/active-tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(3)

        try:
            ckeck_box_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.modal-footer > div > div > div:nth-child(1) > div > label"))) 
            page_main.execute_script("arguments[0].click();",ckeck_box_click)
            logging.info("ckeck_box_click")
        except:
            pass
            
        try:
            approval_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#modal-tenders-terms_of_use > div > div > div.modal-footer > div > div > div:nth-child(2) > button")))  
            page_main.execute_script("arguments[0].click();",approval_click)
            logging.info("approval_click")
            time.sleep(3)
        except:
            pass

        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tab--tenders > section > div > table > tbody > tr'))).text  
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tab--tenders > section > div > table > tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tab--tenders > section > div > table > tbody > tr')))[records]  
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
    page_details2.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
