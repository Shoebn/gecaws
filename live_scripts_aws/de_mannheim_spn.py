from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_mannheim_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_mannheim_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_mannheim_spn'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.main_language = 'DE'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'article > div > h4').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Note:Grab time also

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "article > div > div.teaser__meta.teaser__meta--head").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        if "am" in publish_date or "pm " in publish_date:
            publish_date = re.findall('\d+ \w+ \d{4} - \d+:\d{2} [apAP][mM]',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y - %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        elif "." in publish_date:
            publish_date = re.findall('\d+. \w+ \d{4} - \d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d. %B %Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        else:
            publish_date = re.findall('\w+ \d+, \d{4} - \d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -Note:Splite after "Ende der Angebotsfrist" this keyword....    Note:Grab time also          ...Note:If notice_deadline is not present then take threshold

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "article > div > div:nth-child(3) > div").text
        if "Ende der Angebotsfrist:" in notice_deadline:
            notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
            notice_deadline = re.findall('\w+ \d+, \d{4} - \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    notice_data.notice_url = 'https://www.mannheim.de/de/wirtschaft-entwickeln/oeffentliche-bekanntmachungen-aktuelle-planverfahren-vergaben/oeffentliche-bekanntmachungen'
    
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) article > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'article > div > div:nth-child(3) > span'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -Note:Don't take file extention

            attachments_data.file_name = single_record.text.split(".")[0].strip()
        
        # Onsite Field -None
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = single_record.text.split(".")[1].split("(")[0].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'span').text.split("(")[1].split(")")[0].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        

            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, ' a').get_attribute('href')            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Stadt Mannheim'
        customer_details_data.org_parent_id = '1391662'
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://www.mannheim.de/de/wirtschaft-entwickeln/oeffentliche-bekanntmachungen-aktuelle-planverfahren-vergaben/oeffentliche-bekanntmachungen"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[1]/div/div/main/div/div[2]/div/div/article/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[1]/div/div/main/div/div[2]/div/div/article/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[1]/div/div/main/div/div[2]/div/div/article/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.dialog-off-canvas-main-canvas > div.off-canvas-wrapper > div > div > main > div > div:nth-child(4) > div > nav:nth-child(2) > ul > li.pager__item.pager__item--next > a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[1]/div/div/main/div/div[2]/div/div/article/div'),page_check))
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
