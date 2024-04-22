from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_empulia_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_empulia_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()

    notice_data.script_name = 'it_empulia_spn'
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_title: ", str(type(e)))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline= re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: ", str(type(e)))
        pass

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
    except:
        pass

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute("href")   
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
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
    urls = ['http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Bandi%20di%20gara%20new.aspx',
            'http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Bandi%20di%20gara%20new.aspx?expired=1&type=All'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10): 
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div/div[1]/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/div[4]/div[1]/table/tbody/tr[3]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div/div[1]/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/div[4]/div[1]/table/tbody/tr')))
            length = len(rows)
            logging.info(length)
            for records in range(2,length-1):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div/div[1]/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/div[4]/div[1]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody > tr:nth-child(23) > td > a:nth-child('+str(page_no)+')')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/form/div[7]/div[4]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div/div/table/tbody/tr/td/div/div/div/div[1]/table/tbody/tr/td/table/tbody/tr[2]/td/div/div/div[4]/div[1]/table/tbody/tr[3]'),page_check))
            except :
                logging.info("No next page")
                break
    logging.info("Done cross checked total notice which has to be downloaded {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)