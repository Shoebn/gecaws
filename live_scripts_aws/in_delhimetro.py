from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_delhimetro"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_delhimetro"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_delhimetro'
    
    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) p:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(2) > p:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('to')[0]  
        if '.' in document_purchase_start_time:
            document_purchase_start_time = re.findall('\d+.\d+.\d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d.%m.%Y').strftime('%Y/%m/%d')
        elif '-' in document_purchase_start_time:
            document_purchase_start_time = re.findall('\d+-\d+-\d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
        else:
            document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')            
            
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass

    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('to')[1]    
        if '.' in document_purchase_end_time:
            document_purchase_end_time = re.findall('\d+.\d+.\d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d.%m.%Y').strftime('%Y/%m/%d')
        elif '-' in document_purchase_end_time:
            document_purchase_end_time = re.findall('\d+-\d+-\d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%m-%Y').strftime('%Y/%m/%d')
        else:
            document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')            
            
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass

    try:
        notice_data.publish_date = notice_data.document_purchase_start_time
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(3)").text.split('to')[1]    
        if '.' in notice_deadline:
            notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        elif '-' in notice_deadline:
            notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        else:
            notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')            
            
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text  
        if '.' in document_opening_time:
            document_opening_time = re.findall('\d+.\d+.\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d.%m.%Y').strftime('%Y-%m-%d')
        elif '-' in document_opening_time:
            document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
        else:
            document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')            
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:
        notice_data.additional_tender_url = tender_html_element.find_element(By.CSS_SELECTOR, 'span > p:nth-child(3) > a').get_attribute('href') 
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass

    notice_data.notice_url = "https://www.delhimetrorail.com/pages/en/tenders_by_category/6uww"
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'DELHI METRO RAIL CORPORATION LIMITED'

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text 
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_parent_id = '7247228'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_city = 'Delhi'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(1) > span:nth-child(2) > p > a')[1:]:  
            attachments_data = attachments()

            attachments_data.external_url = single_record.get_attribute('href')

            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_name = single_record.text.strip() 
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ['https://www.delhimetrorail.com/pages/en/tenders_by_category/6uww',  'https://www.delhimetrorail.com/pages/en/tenders_by_category/72mo',  'https://www.delhimetrorail.com/pages/en/tenders_by_category/7acg' ,  'https://www.delhimetrorail.com/pages/en/tenders_by_category/7i28',   'https://www.delhimetrorail.com/pages/en/tenders_by_category/7ps0',   'https://www.delhimetrorail.com/pages/en/tenders_by_category/7xhs',     'https://www.delhimetrorail.com/pages/en/tenders_by_category/8scw',     'https://www.delhimetrorail.com/pages/en/tenders_by_category/902o'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            Pop_up = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="buttonDismiss1"]')))  
            page_main.execute_script("arguments[0].click();",Pop_up)
        except:
            pass

        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="root"]/div/div[3]/div[2]/table/tbody/tr'))).text  
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="root"]/div/div[3]/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="root"]/div/div[3]/div[2]/table/tbody/tr')))[records]  
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="root"]/div/div[3]/div[2]/div/nav/ul/li[9]/button')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    time.sleep(3)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="root"]/div/div[3]/div[2]/table/tbody/tr'),page_check))
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
