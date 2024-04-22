from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_citcochandigarh_spn"
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
SCRIPT_NAME = "in_citcochandigarh_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'in_citcochandigarh_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    notice_data.document_type_description = "Tenders"

    notice_data.notice_url = url
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(2)').text
    except:
        pass
    try:
        if 'Starting date of submission' in publish_date:
            publish_date1 = re.findall(r'\bStarting date of submission of GeM -bid is \d{2}.\d{2}.\d{4}\b',publish_date)[0]
            publish_date1 = re.findall(r'\d{2}.\d{2}.\d{4}',publish_date1)[0]
            notice_data.publish_date = datetime.strptime(publish_date1,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    try:
        if 'Last date of submission' in publish_date:
            notice_deadline = re.findall(r'\bLast date of submission of GeM -bid is \d{2}.\d{2}.\d{4}\s+upto \d+:\d+ [PA]\.[M]\b',publish_date)[0]
            notice_deadline =notice_deadline.replace('P.M','PM')
            notice_deadline = re.findall(r'\d{2}.\d{2}.\d{4}\s+upto \d+:\d+ [PA][M]',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y upto %H:%S %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        else:
            try:
                notice_deadline = re.findall(r'\d+.\d+.\d+ \(\d+.\d+ [PA][M]\)',publish_date)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y (%H.%S %p)').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)   
            except:
                notice_deadline =publish_date.replace('P.M','PM')
                notice_deadline = re.findall(r'\d{2}.\d{2}.\d{4}\s+upto \d+:\d+ [PA][M]',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y upto %H:%S %p').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "CHANDIGARH INDUSTRIAL AND TOURISM DEVELOPMENT CORPORATION LIMITED (CITCO)"
        customer_details_data.org_parent_id = "7577516"
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,' td:nth-child(3) a'):
            attachments_data = attachments()
            attachments_data.file_name = "Tender Description"
            attachments_data.external_url = single_record.get_attribute('href')
            try:
                attachments_data.file_size = attachments_data.external_url.split('.')[-1]
            except:
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
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
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://citcochandigarh.com/tenders-notices/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            clk=page_main.find_element(By.XPATH,'/html/body/div[2]/div/div[2]/div[2]/svg/path').click()
        except:
            pass
        try:
            for page_no in range(2,5): 
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tablepress-1 > tbody tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tablepress-1 > tbody tr')))
                length = len(rows)                                                                              
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tablepress-1 > tbody tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
                        
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
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
