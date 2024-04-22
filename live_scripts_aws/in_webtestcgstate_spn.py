from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_webtestcgstate_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_webtestcgstate_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_webtestcgstate_spn'
  
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'INR'
    
    # Onsite Field -None
    # Onsite Comment -"if the tender title start with ""CORRIGENDUM:"" or ""Clarification of  ""or ""Extension of"" 
    #notice type will be 16 "
    #"EXPRESSION OF INTEREST"", ""EOI""	Invitation for Expression of Interest ""  will be notice type 5" "
    #if not from this then pass - 4"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#block-system-main div.newitem').text
        notice_data.notice_title = notice_data.local_title
        if "CORRIGENDUM" in notice_data.local_title or 'Clarification of' in notice_data.local_title or 'Extension of' in notice_data.local_title or 'CANCELLATION OF' in notice_data.local_title:
            notice_data.notice_type = 16
        elif 'EXPRESSION OF INTEREST' in notice_data.local_title or 'EOI' in notice_data.local_title or 'Invitation for Expression of Interest' in notice_data.local_title:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -LIVE tenders are not present

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#block-system-main span.date-display-single").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
   
     # Onsite Field -Tender
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, '#maincontain-textsize > div.row > div.col-sm-9 > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#block-system-main a.local').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#maincontain-textsize > div.row > div.col-sm-9').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Department name
        # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Department name')]//following::div[1]").text

        customer_details_data.org_parent_id = '7268651'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'IN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#maincontain-textsize div.linkfilesize2'):
            attachments_data = attachments()
            attachments_data.file_type = 'pdf'
        # Onsite Field -None
        # Onsite Comment -ref url "https://webtest.cgstate.gov.in/request-proposal-rfp-selection-agency-s-%C2%A0%E2%80%98%E2%80%98conducting-tracer-study-technical-vocational-education"

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(3) > td > div > a').get_attribute('href')
        
        # Onsite Field -View / Download	
        # Onsite Comment -ref url "https://webtest.cgstate.gov.in/request-proposal-rfp-selection-agency-s-%C2%A0%E2%80%98%E2%80%98conducting-tracer-study-technical-vocational-education"

            attachments_data.file_name = single_record.text.split("-")[0].strip()
        
        # Onsite Field -View / Download	
        # Onsite Comment -ref url "https://webtest.cgstate.gov.in/request-proposal-rfp-selection-agency-s-%C2%A0%E2%80%98%E2%80%98conducting-tracer-study-technical-vocational-education"

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, '#maincontain-textsize span.filesize').text.split(":")[1].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
                
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
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://webtest.cgstate.gov.in/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 70)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-system-main"]/div/div/div[1]/div/ul/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-system-main"]/div/div/div[1]/div/ul/li')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
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
