from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bd_nsdctg_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bd_nsdctg_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#  Go to URL : "https://nsdctg.navy.mil.bd/tenders" 

# click on  "Tender page" ( selector :  "div:nth-child(3) > main  div:nth-child(6)   th:nth-child(4)" )  
# for latest tender details , (note : this would be applicable for every page)
 
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'bd_nsdctg_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BD'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'BDT'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.document_type_description = 'GENERAL TENDERS'
    notice_data.notice_url = "https://nsdctg.navy.mil.bd/tenders"

    # Onsite Field -  Tender No          
    # Onsite Comment -
    
    if 'No Data Available.' in tender_html_element.text:
        return

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field - Tender Date
    # Onsite Comment -
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field - Category
    # Onsite Comment -

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tender Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Line Item
    # Onsite Comment -None

    try:
        notice_data.tender_quantity = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in tender_quantity: {}".format(type(e).__name__))
        pass

    # Onsite Field -Opening Date
    # Onsite Comment -None

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        document_opening_time = re.findall('\d+ \w+ \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %b %Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(6) table > tbody > tr').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = '"Naval Stores Depot Chattogram"'
        customer_details_data.org_country = 'BD'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_parent_id = '7769521'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Documents'

        # Onsite Field -Notice	
        # Onsite Comment -None
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Documents'

    # Onsite Field -Notice	
    # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10) a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
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
    urls = ["https://nsdctg.navy.mil.bd/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        date_data = th.strftime('%d-%m-%Y')
        yest_date = page_main.find_element(By.XPATH,'//*[@id="app"]/div/div[2]/div[2]/main/div/div/div/div[5]/form/div/div[1]/input').clear()
        yest_date = page_main.find_element(By.XPATH,'//*[@id="app"]/div/div[2]/div[2]/main/div/div/div/div[5]/form/div/div[1]/input').send_keys(date_data)
        time.sleep(5)
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="app"]/div/div[2]/div[2]/main/div/div/div/div[5]/form/div/div[5]/button'))).click()
        time.sleep(2)

        try:
         for page_no in range(1,5):
             page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#app > div > div:nth-child(2) > div:nth-child(3) > main > div > div > div > div > div > table > tbody > tr:nth-child(1) > td:nth-child(3)'))).text
             rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#app > div > div:nth-child(2) > div:nth-child(3) > main > div > div > div > div > div > table > tbody > tr')))
             length = len(rows)
             for records in range(0,length):
                 tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#app > div > div:nth-child(2) > div:nth-child(3) > main > div > div > div > div > div > table > tbody > tr')))[records]
                 
                 extract_and_save_notice(tender_html_element)
                 if notice_count >= MAX_NOTICES:
                     break
 
                 if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                     break
                     
                 if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                     logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                     break
 
             try:   
                 next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'''i.fa.fa-caret-right.fa-lg''')))
                 page_main.execute_script("arguments[0].click();",next_page)
                 logging.info("Next page")
                 page_check_2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#app > div > div:nth-child(2) > div:nth-child(3) > main > div > div > div > div > div > table > tbody > tr:nth-child(1) > td:nth-child(3)'))).text
                 WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#app > div > div:nth-child(2) > div:nth-child(3) > main > div > div > div > div > div > table > tbody > tr:nth-child(1) > td:nth-child(3)'),page_check))
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
