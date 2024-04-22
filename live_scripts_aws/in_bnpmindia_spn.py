from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_bnpmindia_spn"
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
SCRIPT_NAME = "in_bnpmindia_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_bnpmindia_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    
    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        if 'NATIONAL COMPETITIVE BIDDING' in procurement_method:
            notice_data.procurement_method = 0
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
                   
        
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('\n')[0].strip()
        if 'dated' in notice_no:
            notice_data.notice_no = notice_no.split('dated')[0].strip()
        elif ', Date' in notice_no:
            notice_data.notice_no = notice_no.split(', Date')[0].strip()
        else:
            notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
        title_selection = re.findall("[\d\.+]\w+",title)[0]
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text.split(title_selection)[0]
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        document_fee = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        document_fee = re.sub("[^\d\,]","",document_fee)
        notice_data.document_fee = document_fee
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    try:
        earnest_money_deposit = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        earnest_money_deposit = re.sub("[^\d\,]","",earnest_money_deposit)
        notice_data.earnest_money_deposit = earnest_money_deposit
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
        publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+ \w+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_deadline = re.findall('\d+ \w+ \d{4} \d+:\d+ \w+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
        
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "BANK NOTE PAPER MILL INDIA PRIVATE LIMITED"
        customer_details_data.org_parent_id = 7522346
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:  
        
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,'td:nth-child(2) > a'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text
            attachments_data.external_url = single_record.get_attribute('href')
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
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
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bnpmindia.com/ViewActiveTender.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
           
        try:
            page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[3]/div[6]/div/div[1]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div[6]/div/div[1]/div/table/tbody/tr')))
            length = len(rows)
            tender_no = 0
            for records in range(tender_no,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div[6]/div/div[1]/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
    
                if notice_count == 10 or notice_count == 20:
                    try:   
                        next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ContentPlaceHolder1_TenderDetails > div > a:nth-child(5)')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[3]/div[6]/div/div[1]/div/table/tbody/tr'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
                elif notice_count > 20:
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
