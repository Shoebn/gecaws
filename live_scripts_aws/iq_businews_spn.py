from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "iq_businews_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "iq_businews_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'iq_businews_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IQ'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'IQD'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -Date Added
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = publish_date.replace("th", "").replace("st", "").replace("nd", "").replace("rd", "")
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Deadline
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = notice_deadline.replace("th", "").replace("st", "").replace("nd", "").replace("rd", "")
        notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        page_details.find_element(By.CSS_SELECTOR,'div.ctct-popup-inner > div > button').click()
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' header > h1')))
    except:
        pass
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > article').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'section.entry > p:nth-child(1)').text
        notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'section.entry > p:nth-child(1)').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_no. eg., here "Tender for the Furnishing of the Wellness and Safety Office. Tender reference number: CUE-RFQ-0012." take only "CUE-RFQ-0012" in notice_no.         2.there is no alternative for notice_no.

    try:
        notice_no = page_details.find_element(By.CSS_SELECTOR, 'section.entry > p:nth-child(1)').text
        if "Tender reference number:" in notice_no:
            notice_data.notice_no = notice_no.split("Tender reference number:")[1].strip()
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IQ'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Company/Ministry
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        
        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'section.entry').text.split("please contact:")[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section.entry a')[:-1]:
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -1.file_name take in text format.	2.reference url "https://www.iraq-businessnews.com/Tenders/electrical-materials-18/".
        
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.iraq-businessnews.com/Tenders/fruit-drying-kits/".
            attachments_data.file_name =  " Tender Document"
            
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.iraq-businessnews.com/Tenders/electrical-materials-18/".            
        
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.iraq-businessnews.com/Tenders/fruit-drying-kits/".

            attachments_data.external_url = single_record.get_attribute('href')            
        
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
    urls = ["https://www.iraq-businessnews.com/tenders/#google_vignette"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_main.find_element(By.CSS_SELECTOR,' div.ctct-popup-inner > div > button').click()
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' header > h1')))
        except:
            pass
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
