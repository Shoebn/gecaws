from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tw_tccgroup_spn"
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
from selenium import webdriver
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tw_tccgroup_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'tw_tccgroup_spn'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TW'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'TWD'
    
    notice_data.notice_url = url
    
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass   
        
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
    
    notice_url_click = tender_html_element.click()
    time.sleep(5)

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#tenderDetail').get_attribute("outerHTML")                     
    except:
        pass

    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'投標起始時間')]//following::div[2]").text
        publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass  

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        notice_deadline = page_main.find_element(By.XPATH, "//*[contains(text(),'投標截止時間')]//following::div[1]").text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass   

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'TW'
        customer_details_data.org_language = 'ZH'
        customer_details_data.org_name = "Taiwan Cement Corporation (TCC Group)"
        customer_details_data.org_parent_id = 7788875

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, "//*[contains(text(),'招標單位')]//following::div[1]").text
        except:
            pass

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, "//*[contains(text(),'經辦人')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, "//*[contains(text(),'經辦人')]//following::div[2]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass   

    page_main.execute_script("window.history.go(-1)")
    time.sleep(5)
    WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#app > div.el-table.el-table--fit.el-table--enable-row-hover > div.el-table__body-wrapper.is-scrolling-none > table > tbody > tr')))
    time.sleep(5) 
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
    urls = ["https://ebidding.taiwancement.com/ebidding/tenderList.html?type=STATUS&status=T&comArea=tcc_cn"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)            

        try:
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div[3]/div[2]/div[3]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div[3]/div[2]/div[3]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
