#Note:Open the site than click on "Search" button than grab the data
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gh_ghaneps_pp"
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
SCRIPT_NAME = "gh_ghaneps_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'gh_ghaneps_pp'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'GHS'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_url = url
        
    notice_data.notice_type = 3
    
    # Onsite Comment -Note:If tender_html_element page in keywod start with "National " than 
#     the  procurement_method will be "0" and start with "International" than 
# the  procurement_method will be "1" other wise it will be "2"
    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if 'National' in procurement_method:
            notice_data.procurement_method = 0
        elif 'International' in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Package
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Package Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
   # Onsite Field -Procurement Type
    # Onsite Comment -Note:Repleace following keywords with given keywords("Goods=Supply","Consulting Services=Consultancy","Disposals=Service","Technical Services=Service","Works=Works")

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Consulting Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Consultancy'
        elif 'Disposals' in notice_data.contract_type_actual or 'Technical Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass 
    
    # Onsite Field -Tender Invitation to Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
       
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass

    try:              
        attachments_data = attachments()
        # Onsite Field -Procuring Entity
        # Onsite Comment -None

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div > a').text

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div > a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Procuring Entity
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

        customer_details_data.org_country = 'GH'
        customer_details_data.org_language = 'EN'
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ghaneps.gov.gh/epps/app/searchPlan.do?searchType=advanced&selectedItem=app/searchPlan.do%3FsearchType%3Dadvanced"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#searchPlanForm > p > button:nth-child(1)')))
        page_main.execute_script("arguments[0].click();",search)
        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="T01"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#Content > div.Pagination > p:nth-child(2) > button:nth-child(5)")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="T01"]/tbody/tr'),page_check))
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
