from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_stella"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_stella"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_stella'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    # Onsite Field -DESCRIZIONE
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(5)').text
        if 'Rettificato' in notice_data.local_title:
            notice_data.notice_type = 16
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -DESCRIZIONE
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english  = notice_data.notice_title 
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -REGISTRO DI SISTEMA
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -IMPORTO
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(7)').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -SCADENZA
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tbody > tr > td:nth-child(8)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    # Onsite Field -DETTAGLIO
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.GR0_GridCol_Link > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#template_doc').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo Appalto:
    # Onsite Comment -In Tipo Appalto: if Lavori pubblici take it under works,Servizi under Service and Fornitura under Goods

    try:
        notice_contract_type = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(8)').text.split('Tipo Appalto: ')[1]  
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Lavori pubblici' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
# Onsite Field -ENTE APPALTANTE
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        # Onsite Field -ENTE APPALTANTE
        # Onsite Comment -None
        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(6)').text  
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'IT'
    # Onsite Field -Incaricato:
    # Onsite Comment -take contact person field from page detail

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Incaricato:')]//following::td").text   
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(12) > td > table > tbody > tr')[1:]:
            attachments_data = attachments()
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, '#Allegato_V_N').text 
                if '.pdf' in attachments_data.file_type:
                    attachments_data.file_type = 'pdf'
                elif '.doc' in attachments_data.file_type:
                    attachments_data.file_type = 'doc'   
                else:
                    attachments_data.file_type = 'zip'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, '#Allegato_V_N').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'table > tbody > tr > td:nth-child(1) > label').text  
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
            

            try:
                external_url = single_record.find_element(By.CSS_SELECTOR, '#Allegato_V_N').get_attribute('onclick')
                external_url = external_url.split("window.open('")[1].split(');')[0]
                attachments_data.external_url = external_url
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    


# Onsite Field -None
# Onsite Comment -None

    try:              
        tender_criteria_data = tender_criteria()
    # Onsite Field -Criterio Aggiudicazione:
    # Onsite Comment -None
        tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Criterio Aggiudicazione:')]//following::td").text
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
chrome_options = Options()
for argument in arguments:
    chrome_options.add_argument(argument)
page_main = webdriver.Chrome(chrome_options=chrome_options)
page_details = webdriver.Chrome(chrome_options=chrome_options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://stella.regione.lazio.it/portale/index.php/bandi?&filtro=1%3D1%20and%20Gestore%20=%200&sort=a_base_asta&sortorder=desc'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#table-lista-bandi > tbody > tr:nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#table-lista-bandi > tbody tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#table-lista-bandi > tbody tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#table-lista-bandi > tbody > tr:nth-child(1)'),page_check))
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
