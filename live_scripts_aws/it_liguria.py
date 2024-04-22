from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_liguria"
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
SCRIPT_NAME = "it_liguria"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'it_liguria'
    notice_data.main_language = 'IT'
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    notice_data.procurement_method = 2
    
    notice_data.document_type_description = "AVVISI"
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bando_link').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bando_link ').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    logging.info(notice_data.notice_url)
    
    try:
        notice_no = notice_data.notice_url
        notice_data.notice_no = re.findall('\d{4}',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text = page_details.find_element(By.XPATH, '//*[@id="content"]/div[4]/div/div[2]').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, ' div.pc_latest_item_apertura.minisize').text
        publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
        try:
            publish_date_en= re.findall('\w+ \d+, \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date_en,'%B %d, %Y').strftime('%Y/%m/%d')
        except:
            publish_date_en= re.findall('\d+ \w+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date_en,'%d %B %Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, 'div.pc_latest_item_chiusura.minisize').text
        notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)
        try:
            notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    customer_details_data = customer_details()
    customer_details_data.org_name = "REGIONE LIGURIA"
    customer_details_data.org_country = 'IT'
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.pc_latest_item_alberatura_fondo.borderBox'):
            customer_details_data.org_city = single_record.find_element(By.CSS_SELECTOR, 'div.pc_latest_item_enti.minisize').text.split(':')[1]
    except Exception as e:
        logging.info("Exception in org_city: {}".format(type(e).__name__))
        pass
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'ul.docs-list'):
            attachments_data = attachments()
            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'p.card-title').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'ul li a').get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'ul li a span.filesize').text.split("(")[1].split(")")[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' ul > li > a > div > span:nth-child(2)').text.strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
    urls = ['https://www.regione.liguria.it/homepage-bandi-e-avvisi.html'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' li:nth-child(1) > div.pc_latest_item_bando'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' div.pc_latest_item_bando')))
                length =len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.pc_latest_item_bando')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,' li:nth-child(1) > div.pc_latest_item_bando'),page_check))
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
