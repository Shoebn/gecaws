from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_marcsecuris_ca"
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
SCRIPT_NAME = "fr_marcsecuris_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
  
    notice_data.script_name = 'fr_marcsecuris_ca'
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'FR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    notice_data.notice_url = url
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.tr_objet > td').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(7) > td').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(7) > td').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de marché / Type de prestation  ---- Travaux = Works, Services = Services, Fournitures = Supplies
    # Onsite Comment -split "Type de prestation"

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.tr_type > td').text
        if 'Travaux' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Fournitures' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass               
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procédure
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR,'tr.tr_proc > td').text.split('\n')[0].strip()
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcsecuris_ca_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    # Onsite Field -Date de mise en ligne
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr:nth-child(9) > td").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Référence
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.tr_identifiant > th:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, '#details_avis').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:              
        customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.tr_pa.tr_icone > td').text


        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None


    
# Onsite Field -None
# Onsite Comment -None

    try:              
        attachments_data = attachments()
        # Onsite Field -Fichier
        # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(8) > td > a').get_attribute('href')
            
        
        # Onsite Field -Fichier
        # Onsite Comment -None

        try:
            attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(8) > td > a').text.split('.')[0].strip()
        except Exception as e:
            logging.info("Exception in file_name: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Fichier
        # Onsite Comment -None

        try:
            attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(8) > td > a').text.split('.')[1].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
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
    urls = ['https://www.marches-securises.fr/entreprise/?module=liste_avis_attribution'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,50):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div[4]/div[2]/div/table/tbody'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[4]/div[2]/div/table/tbody')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[4]/div[2]/div/table/tbody')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/div[4]/div[2]/div/table/tbody'),page_check))
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
    
