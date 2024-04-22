from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_trascultura_gpn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_trascultura_gpn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
# -------------------------------------------------------------------------------------------------------------------------------------------------------

#   Go to URL for GPN : "https://trasparenza.cultura.gov.it/pagina838_avvisi-di-preinformazione.html"

#                     : you can see GPN tbody below the "Ricerca" section



# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
   
    notice_data.script_name = 'it_trascultura_gpn'
   
    notice_data.main_language = 'IT'
  
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 2
    
    
    try:
        notice_data.document_type_description= tender_html_element.find_element(By.XPATH, ' /html/body/article/header/div[2]/nav').text.split("50/2016")[1].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass      
    
    # Onsite Field -OGGETTO
    # Onsite Comment -split the data from tender_html_page , url ref : "https://trasparenza.cultura.gov.it/pagina838_avvisi-di-preinformazione.html"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data di pubblicazione
    # Onsite Comment -split the data from tender_html_page , url ref : "https://trasparenza.cultura.gov.it/pagina838_avvisi-di-preinformazione.html"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return   
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("outerHTML").split("_0_")[1].split(".html")[0] 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -OGGETTO
    # Onsite Comment -inspect url for detail page, url ref : https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_146130_838_1.html

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        time.sleep(8)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > #regola_default').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass     
    
    # Onsite Field -Data di scadenza:
    # Onsite Comment -split the data from detail_page, url ref : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_146130_838_1.html"

    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Data di scadenza:")]//following::strong[1]').text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass        
    
# Onsite Field -None
# Onsite Comment -ref url : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_146130_838_1.html"

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        # Onsite Field -Ufficio:
        # Onsite Comment -ref url : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_146130_838_1.html"

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Ufficio:")]//following::a[1]').text
            
        # Onsite Field -RUP:
        # Onsite Comment -split the data between "Ufficio:" and "Data dell'atto:" field. url ref : "https://trasparenza.cultura.gov.it/archivio11_bandi-gare-e-contratti_0_146130_838_1.html"

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"RUP:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -lot details are not mentioned in the site

    try:
        lot_details_data = lot_details()       
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > h3').text
        lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Allegati
# Onsite Comment -split the data from detail_page

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#reviewOggetto > div > div > div.campoOggetto48'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text.split(":")[1].split(".")[0]
            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            
            try:
                attachments_data.file_type = single_record.text.split(".")[1].split("\n")[0]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
    
            try:
                attachments_data.file_description = attachments_data.file_name
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass    
     
            try:
                attachments_data.file_size =single_record.text.split("\n")[1].split("-")[-2]
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
    urls = ["https://trasparenza.cultura.gov.it/pagina838_avvisi-di-preinformazione.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]/table/tbody/tr')))[records]
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
