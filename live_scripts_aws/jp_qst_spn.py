from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "jp_qst_spn"
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
SCRIPT_NAME = "jp_qst_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'jp_qst_spn'
    notice_data.main_language = 'JA'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'JP'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'JPY'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "dl > dd").text
        publish_date = publish_date.split('掲載期間：')[1].split('～')[0].strip()
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        try:
            notice_data.publish_date  = datetime.strptime(publish_date ,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S') 
        except:
            notice_data.publish_date = datetime.strptime(publish_date ,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "dl > dd").text
        notice_deadline = notice_deadline.split('～')[1].split('】')[0].strip()
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline ,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S') 
        except:
            notice_data.notice_deadline = datetime.strptime(notice_deadline ,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'dl > dd').text        
        try:
            notice_no = re.findall('RE-\d+-\d+.', notice_no)[0]
        except:
            try:
                notice_no = re.findall('RE-\d+.', notice_no)[0]
            except:
                pass
            
        try:
            notice_data.notice_no = notice_no.split('）')[0]
        except:
            try:
                notice_data.notice_no = notice_no.split(')')[0]
            except:
                pass
            
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'dl > dd').text            
        try:
            local_title_re = re.findall('RE-\d+-\d+.', local_title)[0]
        except:
            local_title_re = re.findall('RE-\d+.', local_title)[0]
        notice_data.local_title = local_title.split(local_title_re)[1].split('【')[0].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'dl > dd > a').get_attribute("href")    
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.c-content-main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'National Institutes for Quantum and Radiological Science and Technology'
        customer_details_data.org_parent_id = '7781692'
        customer_details_data.org_country = 'JP'
        customer_details_data.org_language = 'JA'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.detail_free > p > a'):
            attachments_data = attachments()

            file_name = single_record.text
            attachments_data.file_name = file_name.split('[')[0]
            
            try:
                file_type = file_name
                attachments_data.file_type = file_type.split('[')[1].split('フ')[0]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                file_size = file_name
                file_size = file_size.split('ル／')[1].split(']')[0]
                attachments_data.file_size = file_size
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
            attachments_data.external_url = single_record.get_attribute('href')
        
        
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.qst.go.jp/soshiki/list10-1.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main_body"]/div[1]/div/dl'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main_body"]/div[1]/div/dl')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main_body"]/div[1]/div/dl')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="main_body"]/div[1]/div/dl'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
