from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_trascultura_spn"
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
SCRIPT_NAME = "it_trascultura_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_trascultura_spn'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -OGGETTO
    # Onsite Comment -local_title for both format

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        notice_data.local_description = notice_data.local_title
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CIG
    # Onsite Comment -split the date from tender_html page, take for both format

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DATA DI PUBBLICAZIONE
    # Onsite Comment -take publication date for both format

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    if url==urls[0]:
        notice_data.document_type_description = 'Avvisi e Bandi'
    else:
        notice_data.document_type_description = 'Delibera a contrarre'
    
    # Onsite Field -OGGETTO
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.row > div.col-lg-9').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Data di scadenza:
    # Onsite Comment -split the data from detail_page, ref url : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_156988_957_1.html"

    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Data di scadenza")]//following::strong[1]').text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass        

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'  

    # Onsite Field -Ufficio:
    # Onsite Comment -split the data from "Ufficio:" this field, (take xpath for  both format)

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Ufficio:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

    # Onsite Field -RUP:
    # Onsite Comment -split the data from "RUP:" this field,

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"RUP: ")]//following::a').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_number = 1
        lot_details_data = lot_details()
        lot_details_data.lot_number = lot_number

        lot_title = page_details.find_element(By.XPATH, '//*[@id="reviewOggetto"]/div/div/div[2]/h3').text
        lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
        lot_details_data.lot_description = lot_details_data.lot_title

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.campoOggetto48'):
            attachments_data = attachments()
        # Onsite Field -Allegati
        # Onsite Comment -split only file_type , for ex : "Decreto n 50 del 18 maggio 2023 conclusione lavori commissione convegno cel vanv.pdf"  , here take only "pdf"

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -split only file_name , for ex : "46713887doc00094320230803160654_integrazione_tistampo.pdf" , here take only "46713887doc00094320230803160654_integrazione_tistampo"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('.')[0].strip()
        
        # Onsite Field -Allegati
        # Onsite Comment -take all the data as a "file_description" from selector

            attachments_data.file_description = single_record.text
        
        # Onsite Field -Allegati
        # Onsite Comment -split only file size from this field , for ex . "(Pubblicato il 04/08/2023 - Aggiornato il 04/08/2023 - 3092 kb - pdf) ", here take only "3092 kb"

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'span').text.split('-')[2].split('-')[0].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://trasparenza.cultura.gov.it/pagina957_avvisi-e-bandi.html" , "https://trasparenza.cultura.gov.it/pagina956_delibera-a-contrarre.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 70).until(EC.presence_of_element_located((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 70).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,'>successiva')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr[2]'),page_check))
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
