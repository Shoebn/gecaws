from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_tenders_pp"
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
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_tenders_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'au_tenders_pp'
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'AUD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 3
    notice_data.notice_url = url
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-4  p > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-8 > div > div:nth-child(3) div').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:        
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.last-updated").text
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'article  div.col-sm-8').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'article  div.col-sm-8'):
            customer_details_data = customer_details()

            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-8 > div > div:nth-child(2) div').text
        
            try:  
                contact_person = tender_html_element.find_element(By.XPATH, '(//*[contains(text(),"Contact:")]/..)['+str(num)+']').text
                if "As for APP" in contact_person:
                    pass
                else:
                    customer_details_data.contact_person = contact_person.split(':')[1].split(',')[0].strip()
                    customer_details_data.org_email = fn.get_email(contact_person)
                    customer_details_data.org_phone = contact_person.split(customer_details_data.contact_person)[1].split(customer_details_data.org_email)[0].strip().replace(',','')
            except Exception as e:
                logging.info("Exception in contact_name: {}".format(type(e).__name__))
                pass
                
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        cpv_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div').text.split('-')[0].strip()
        cpv_codes = fn.CPV_mapping("assets/au_tenders_pp_cpv.csv",cpv_no)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_codes: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    urls = ["https://www.tenders.gov.au/Search/PpAdvancedSearch?Page=1&ItemsPerPage=0&SearchFrom=PpSearch&Type=Pp&AgencyStatus=0&KeywordTypeSearch=AllWord&OrderBy=Last%20Updated"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        
        try:
            login_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#s2menu > li.menu-login')))
            page_main.execute_script("arguments[0].click();",login_click)
            time.sleep(2)

            page_main.find_element(By.CSS_SELECTOR,'#login-username').send_keys('akanksha@globalecontent.com')
            time.sleep(2)
            page_main.find_element(By.CSS_SELECTOR,'#login-password').send_keys('dg@1234567')

            submit_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#login-form > input.goLogIn')))
            page_main.execute_script("arguments[0].click();",submit_click)
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in login_error: {}".format(type(e).__name__)) 
            pass

        try:
            for page_no in range(2,30):#30
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainContent > div:nth-child(3) > div.boxEQH article div.row'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#mainContent > div:nth-child(3) > div.boxEQH article div.row')))
                length = len(rows)
                num = 1
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#mainContent > div:nth-child(3) > div.boxEQH article div.row')))[records]
                    extract_and_save_notice(tender_html_element)
                    num+=1
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
            
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainContent > div:nth-child(3) > div.boxEQH article div.row'),page_check))
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
