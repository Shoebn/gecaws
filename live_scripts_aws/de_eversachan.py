from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_eversachan"
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
SCRIPT_NAME = "de_eversachan"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = "de_eversachan"
    
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
  
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    
    # Onsite Field -Ausschreibungsgegenstand
    # Onsite Comment -None
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tsaid_TOPIC > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > #tsaid_AnsichtAusschreibung_01').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Veröffentlichungsdatum
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.tsaid_RELEASEDATE").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Recherche aktueller Vergaben
    # Onsite Comment -None
    try:
        document_type_description = page_details.find_element(By.CSS_SELECTOR, '#c8 > h1').text
        notice_data.document_type_description  = GoogleTranslator(source='de', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ausschreibungsgegenstand
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tsaid_TOPIC').text
        notice_data.notice_title = GoogleTranslator(source='de', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Verfahrensart
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, "div.tsaid_PROCESSTYPE").text.split('Ver­fah­rens­art: ')[1]
        type_of_procedure_actual = GoogleTranslator(source='de', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_eversachan_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Verfallsdatum**
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td.tsaid_DEADLINE").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Ort
        # Onsite Comment -None
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//div[@class="tsaid_MANDANT "]//div[2]').text



        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//div[@class="tsaid_AREA "]//div[2]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        customer_details_data.org_language = 'DE'
        customer_details_data.org_country = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try: 
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//div[@class="tsaid_URL tsaid_TenderSourceXVergabe"]//div[2]//a').get_attribute('href')
    except:
        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//div[@class="tsaid_URL tsaid_TenderSourceEVergabeOnline"]//div[2]//a').get_attribute('href')
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__)) 
            pass
    # Onsite Field -None
    # Onsite Comment -None
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://evergabe.sachsen-anhalt.de/recherche-aktueller-vergaben"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'.tsaid_searchButton'))).click()
        except:
            pass

        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tsaid_ListeAusschreibungen_01"]/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tsaid_ListeAusschreibungen_01"]/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tsaid_ListeAusschreibungen_01"]/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tsaid_ListeAusschreibungen_01"]/div[2]/table/tbody/tr'),page_check))
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
