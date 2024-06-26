from gec_common.gecclass import *
import logging
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
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_rvskvv_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_rvskvv_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'INR'
    
    notice_data.notice_url = url
    
    notice_data.notice_type = 4
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(1)").text  
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(3)").text.strip()
        try:
            publish = re.findall('\d+/\d+/\d{4} [\d:]+ [PMAMpmam]+',publish_date)[0]
            try:
                notice_data.publish_date = datetime.strptime(publish,'%d/%m/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_data.publish_date = datetime.strptime(publish,'%d/%m/%Y %I %p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                publish = re.findall('\d+/\d+/\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
        try:
            deadline = re.findall('\d+/\d+/\d{4} [\d:]+ [PMAMpmam]+',notice_deadline)[0]
            try:
                notice_data.notice_deadline = datetime.strptime(deadline,'%d/%m/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_data.notice_deadline = datetime.strptime(deadline,'%d/%m/%Y %I %p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
        logging.info(notice_data.notice_deadline) 
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name =  "RAJMATA VIJAYARAJE SCINDIA KRISHI VISHWAVIDYALAYA (RVSKVV)"
        customer_details_data.org_parent_id = 7123266
        customer_details_data.org_phone = '0751-2970509'
        customer_details_data.org_email = 'drs@rvskvv.net'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    
    try:               
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td > p > a'):
            attachments_data = attachments()
                
            attachments_data.file_name = single_record.get_attribute("outerHTML")
            
            if 'Corrigendum' in attachments_data.file_name:
                notice_data.notice_type = 16

            attachments_data.external_url = single_record.get_attribute("href")
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except:
                pass
            
            if attachments_data.external_url != '':
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
        pass
   
    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td > a'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text
            
            if 'Corrigendum' in attachments_data.file_name:
                notice_data.notice_type = 16

            attachments_data.external_url = single_record.get_attribute("href")
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except:
                pass

            if attachments_data.external_url != '':
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
        pass   

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://www.rvskvv.net/index.php/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)  
        try:   
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#sp-component > div > div.article-details > div:nth-child(3) > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#sp-component > div > div.article-details > div:nth-child(3) > table > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#sp-component > div > div.article-details > div:nth-child(3) > table > tbody > tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#sp-component > div > div.article-details > div:nth-child(3) > table > tbody > tr'),page_check))
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
