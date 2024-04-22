from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_lombardia_ca"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_lombardia_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)

output_json_folder = "cross_check_output"

def extract_and_save_notice(tender_html_element):

    global notice_count
    global notice_data
    notice_data = cross_check_output()

    notice_data.script_name = 'it_lombardia_ca'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()

    performance_country_data.performance_country = 'IT'

    notice_data.currency = 'EUR'

    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    
    notice_data.additional_source_name="ARIA"

    # Onsite Field -None
    # Onsite Comment -In Search  Field  below are the keywords for Contract Award(CA) :- in  "STATO :" select the following keywords for ca (notice_type 7) ' Aggiudicata',' Aggiudicazione','Conclusa'

    # Onsite Field -STATO
    # Onsite Comment -None
 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -NOME PROCEDURA
    # Onsite Comment -None
    try:
        CODICE_GARA = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except:
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.replace(CODICE_GARA,'').strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -ID SINTEL
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except:
        try:
            notice_data.notice_no=notice_data.notice_url.split("id=")[1].strip()
        except Exception as e:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass    
    
    # Onsite Field -DATA INIZIO
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    # Onsite Field -TIPO
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_lombardia_ca_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    # Onsite Field -VALORE ECONOMICO
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        est_amount =est_amount.replace('.','')
        notice_data.est_amount = float(est_amount.replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    # Onsite Field -VALORE ECONOMICO
    # Onsite Comment -None

    try:
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -VALORE ECONOMICO
    # Onsite Comment -None

 
    try:
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
        
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
    urls = ['https://www.sintel.regione.lombardia.it/eprocdata/sintelSearch.xhtml'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            stato= page_main.find_element(By.CSS_SELECTOR, '#state').click()
        except Exception as e:
            logging.info("Exception in stato: {}".format(type(e).__name__))
            pass
        time.sleep(2)

        try:
            Aggiudicazione= page_main.find_element(By.CSS_SELECTOR, '#j_idt28\:j_idt31\:auctionStatus\:15').click()
        except Exception as e:
            logging.info("Exception in Aggiudicazione: {}".format(type(e).__name__))
            pass
        time.sleep(2)

        try:
            Aggiudicata= page_main.find_element(By.CSS_SELECTOR, '#j_idt28\:j_idt31\:auctionStatus\:17').click()
        except Exception as e:
            logging.info("Exception in Aggiudicata: {}".format(type(e).__name__))
            pass
        time.sleep(2)

        try:
            Conclusa= page_main.find_element(By.CSS_SELECTOR, '#j_idt28\:j_idt31\:auctionStatus\:19').click()
        except Exception as e:
            logging.info("Exception in Conclusa: {}".format(type(e).__name__))
            pass

        try:
            applica= page_main.find_element(By.CSS_SELECTOR, '#j_idt28\:j_idt31\:template-contactform-submit').click()
        except Exception as e:
            logging.info("Exception in applica: {}".format(type(e).__name__))
            pass
        time.sleep(5)

        for page_no in range(2,50):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="result"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

 
            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="result"]/tbody/tr'),page_check))
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

    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
