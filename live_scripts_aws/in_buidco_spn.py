from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_buidco_spn"
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
SCRIPT_NAME = "in_buidco_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'in_buidco_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4
    
    try:
        notice_data.document_type_description = 'Active Tenders'
    except:
        pass
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        deadline_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        deadline_date = deadline_date.split()
        deadline_date = " ".join(deadline_date[:3]) + " " + deadline_date[3] + " " +deadline_date[4]
        deadline_date = re.findall(r'\d+ \w+ \d{4} \d+:\d+ [apAP][Mm]',deadline_date)[0]
        notice_data.notice_deadline = datetime.strptime(deadline_date, '%d %b %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
        
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        document_opening_time = re.findall(r'\d+ \w+ \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d %b %Y').strftime('%Y-%m-%d')
    except:
        pass
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(3) > a").get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        pass
    logging.info(notice_data.notice_url)
    try:
        notice_text1 = tender_html_element.get_attribute('outerHTML')
        notice_text = page_details.find_element(By.CSS_SELECTOR,' div.inContan > div.inRight > div.containerRight').get_attribute('outerHTML')
        notice_data.notice_text = notice_text +  notice_text1
    except:
        pass
    
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Headline")]//following::span[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Details")]//following::span[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Bihar Urban Infrastructure Development Corporation Limited'
        customer_details_data.org_parent_id = '6992393'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_state = 'Bihar'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#dtl_list tbody tr div div'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,' td:nth-child(2) a' ).text

            if 'Corrigendum' in attachments_data.file_name:
                notice_data.notice_type = 16

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2) a' ).get_attribute('href') 

            attachments_data.file_type = attachments_data.external_url.split('.')[-1]

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
  
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://www.buidco.in/ActiveTenders.aspx?GL=5&PL=1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,3):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#grdView > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#grdView > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#grdView > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#grdView > tbody > tr'),page_check))
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
