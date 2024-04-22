from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_aoupu"
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
SCRIPT_NAME = "it_aoupu"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_aoupu'
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -Pubblicato il
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Scade il
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > th').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
       
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > th').text
        if "MANIFESTAZIONE DI INTERESSE" in notice_type:
            notice_data.notice_type = 5
    except:
        pass 
    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'th > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/div[1]/main/section[3]/div/div/div[2]').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Descrizione
#     # Onsite Comment -split notice_summary_english from "Descrizione"

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '/html/body/div[1]/main/section[3]/div/div/div[2]').text
        if 'Descrizione' in notice_summary_english:
            notice_data.notice_summary_english = notice_summary_english.split('Descrizione')[1].split('Data pubblicazione')[0].strip()
            notice_data.notice_summary_english = GoogleTranslator(source='it', target='en').translate(notice_data.notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = page_details.find_element(By.XPATH, '/html/body/div[1]/main/section[3]/div/div/div[2]').text
        if 'Descrizione' in local_description:
            notice_data.local_description = local_description.split('Descrizione')[1].split('Data pubblicazione')[0].strip()
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia avviso
    # Onsite Comment -split type_of_procedure_actual from "Tipologia avviso"

    try:
        type_of_procedure_actual = page_details.find_element(By.XPATH, '/html/body/div[1]/main/section[3]/div/div/div[2]').text
        if 'Tipologia avviso' in type_of_procedure_actual:
            notice_data.type_of_procedure_actual = type_of_procedure_actual.split('Tipologia avviso')[1].split('\n')[1].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Azienda Ospedaliera Universitaria Policlinico Umberto I'
        customer_details_data.org_parent_id = '7266414'
        customer_details_data.org_country = 'IT'
    # Onsite Field -Email di riferimento
    # Onsite Comment -split org_email from "Email di riferimento"

        try:
            org_email = page_details.find_element(By.XPATH, '/html/body/div[1]/main/section[3]/div/div/div[2]').text
            if 'Email di riferimento' in org_email:
                customer_details_data.org_email = org_email.split('Email di riferimento')[1].split('\n')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Telefono
    # Onsite Comment -split org_phone from "Telefono"

        try:
            org_phone = page_details.find_element(By.XPATH, '/html/body/div[1]/main/section[3]/div/div/div[2]').text
            if 'Telefono' in org_phone:
                customer_details_data.org_phone = org_phone.split('Telefono')[1].split('\n')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None 
    try:         
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-12.col-lg-8.it-page-sections-container > div > div > table > tbody > tr '):
            lot_details_data = lot_details()
        # Onsite Field -Descrizione
        # Onsite Comment -split lot_title from "Lotto"                   if lot_title is not availabel then take local_title as lot_title

            lot_title = single_record.find_element(By.CSS_SELECTOR, 'td').text
            if 'lotto ' in lot_title or 'Lotto ' in lot_title:
                lot_details_data.lot_title = lot_title.split(': ')[1].split('\n')[0].strip()
                lot_details_data.lot_title_english = GoogleTranslator(source='it', target='en').translate(lot_details_data.lot_title)
        # Onsite Field -Descrizione
        # Onsite Comment -None
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.card-body.pb-0'):
            attachments_data = attachments()
        # Onsite Field -Allegati
        # Onsite Comment -None

            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -None

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'a').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -None
        
            try:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                attachments_data.external_url = external_url
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.policlinicoumberto1.it/bandi-di-gara-avvisi/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,3):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main_container"]/section[3]/div/form/div/div[3]/div/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main_container"]/section[3]/div/form/div/div[3]/div/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main_container"]/section[3]/div/form/div/div[3]/div/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="main_container"]/section[3]/div/form/div/div[3]/div/div/table/tbody/tr'),page_check))
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
