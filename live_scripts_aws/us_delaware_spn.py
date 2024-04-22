from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_delaware_spn"
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
SCRIPT_NAME = "us_delaware_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_delaware_spn'
    
    notice_data.main_language = 'EN'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'USD'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.document_type_description = 'Bids'
    
    notice_data.notice_url = url
    
    # Onsite Field -Contract Number
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Title
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Open Date
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline Date
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    org_name1 = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text

    # Onsite Field -UNSPSC
    # Onsite Comment -if UNSPSC code is matched with CPV then take , otherwise take auto CPV
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        cpv_regex = re.compile(r'\d{8}')
        cpv_code_list = cpv_regex.findall(notice_data.category)
        for cpv in cpv_code_list:
            cpv_codes = fn.CPV_mapping("assets/us_delaware_spn (1).csv",cpv)
            for cpv_code in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    # Onsite Field -Contract Title    
    try:
        next_page = WebDriverWait(tender_html_element, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(3) a')))
        page_main.execute_script("arguments[0].click();",next_page)
        time.sleep(3)

        try:
            notice_data.notice_text += page_main.find_element(By.ID, '#dynamicDialogInnerHtml').get_attribute("outerHTML")                     
        except:
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = fn.procedure_mapping("assets/us_delaware_spn_org.csv",org_name1)
            customer_details_data.org_language = 'EN'
            customer_details_data.org_country = 'US'
            customer_details_data.org_parent_id = '7689218'
            # Onsite Field -Contact Information
            # Onsite Comment -for Page_main click on "tr.jqgrow > td:nth-child(3) a"

            try:
                customer_details_data.org_email = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > a').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

            # Onsite Field -Supporting Bid Documents
        try:              
            for single_record in page_main.find_elements(By.CSS_SELECTOR, '#bidDocuments  tbody > tr> td > a'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.text

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        try:
            back = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#dynamicDialogInnerHtml > form > div.modal-footer > input')))
            page_main.execute_script("arguments[0].click();",back)
            time.sleep(3)
        except Exception as e:
            logging.info("Exception in back: {}".format(type(e).__name__))

    except Exception as e:
        logging.info("Exception in click: {}".format(type(e).__name__)) 
        pass
        
    WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.jqgrow.ui-row-ltr')))
    
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
    urls = ["https://mmp.delaware.gov/Bids/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.jqgrow.ui-row-ltr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.jqgrow.ui-row-ltr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.jqgrow.ui-row-ltr')))[records]
                extract_and_save_notice(tender_html_element)
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="next_jqg1"]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tr.jqgrow.ui-row-ltr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)