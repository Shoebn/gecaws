from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_difesa"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_difesa"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_difesa'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
   

    try:
        notice_data.document_type_description = "Bandi di Gara"
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'li > a >h4').text
        if "Acquisition of" in notice_data.local_title or "Acquisizione di" in notice_data.local_title:
            notice_data.notice_type = 13
        elif "PROROGA" in notice_data.local_title:
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4   
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
 
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span.data-generico").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.elenco-generico> li > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
 
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.span10.contenuto > div:nth-child(2)').get_attribute("outerHTML")                     
    except Exception as e:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.area_note').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
 
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[@id='ctl00_PlaceHolderMain_MdDCodiceGaraContainer']/strong").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Ministero della Difesa'
        customer_details_data.org_parent_id = '1347768'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
 
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_PlaceHolderMain_MdDImageGalleryApprofondimenti1_boxApprofondimenti > div > a'):
            attachments_data = attachments()
   
            try:
                attachments_data.file_type = single_record.text.split(".")[1].split(" ")[0]  
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_name = single_record.text.split("(")[0]
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

            try:
                file_size = single_record.text.split("(")[1].split(".pdf")[1].split(")")[0]
                attachments_data.file_size = fn.bytes_converter(file_size)
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.external_url = single_record.get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.difesa.it/SGD-DNA/Staff/DT/TELEDIFE/Bandi/Pagine/elenco.aspx'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_PlaceHolderMain_ctl00_PannelloDinamico"]/ul/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_PlaceHolderMain_ctl00_PannelloDinamico"]/ul/li')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
    
