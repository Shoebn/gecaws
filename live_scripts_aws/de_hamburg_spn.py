from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_hamburg_spn"
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
SCRIPT_NAME = "de_hamburg_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'de_hamburg_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'DE'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Öffentliche Verfahren'
    
    # Onsite Field -None
    # Onsite Comment -None
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.color-primary.card-title-style').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Projektnummer:
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(1) > label').text 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
     # Onsite Field -Leistungsart:
     # Onsite Comment -Replace follwing keywords with given respective kywords ('Sicherungsleistung/bauaffine Dienstleistung =Service','Bauleistung = Works ','Lieferleistung = Supply', 'Dienstleistung = services ','Architekten- und Ingenieurleistungen = consultancy')

    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(2) > label').text
        if 'Sicherungsleistung/bauaffine Dienstleistung' in notice_contract_type or 'Dienstleistung' in notice_contract_type:
            notice_data.notice_contract_type='Service'
        elif 'Bauleistung' in notice_contract_type:
            notice_data.notice_contract_type='Works'
        elif 'Lieferleistung' in notice_contract_type:
            notice_data.notice_contract_type='Supply'
        elif 'Architekten- und Ingenieurleistungen' in notice_contract_type:
            notice_data.notice_contract_type='Consultancy'
        else:
            pass
        
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Einreichungsfrist:
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,"div:nth-child(2) > div:nth-child(1) > label").text     
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%y, %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
     # Onsite Field -DETAILS
    # Onsite Comment -click on DETAILS for detail page
    try:
        WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.button-area-style > button > span.mat-button-wrapper > span"))).click()
        time.sleep(5)
        notice_data.notice_url = page_main.current_url  
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'project-details > div > div:nth-child(2)'))).get_attribute("outerHTML")        
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Vergabeart:
     # Onsite Comment -take only "Vergabeart:" data as type_of_procedure_actual from the given selector

    try: 
        notice_data.type_of_procedure_actual = page_main.find_element(By.XPATH,"//*[contains(text(),'Vergabeart')]//following::div[1]").text 
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_hamburg_spn_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::div[1]').text 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Beschreibung
     # Onsite Comment -None

    try:
        notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::div[1]').text  
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english) 
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Bekanntmachung
     # Onsite Comment -take only date as publication_date

    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Bekanntmachung")]//following::div[1]').text
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y, %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

 # Onsite Field -Auftraggeber
 # Onsite Comment -None

    try:              
        
        customer_details_data = customer_details()
         # Onsite Field -Auftraggeber
         # Onsite Comment -take only first data as org_name
        try:
            customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, 'mat-card-content > div > div:nth-child(4) > div:nth-child(2)').text 
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
#         # Onsite Field -Adresse
#         # Onsite Comment -None
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresse")]//following::div[1]').text 
        except Exception as e: 
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
#         # Onsite Field -Ausführungsort:
#         # Onsite Comment -None
        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Ausführungsort")]//following::div[1]').text  
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

     # Onsite Field -Klassifizierung
     # Onsite Comment -None


    try:
        cpvs_code = page_main.find_element(By.XPATH,'//*[contains(text(),"Klassifizierung")]//following::div[1]').text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass


    try:              
        attachments_data = attachments()
        external_url = page_main.find_element(By.CSS_SELECTOR, 'button.mat-focus-indicator.mat-tooltip-trigger.download-button-style').click()
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        attachments_data.file_name = 'Tender Documents'
        attachments_data.file_type = 'zip'
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://fbhh-evergabe.web.hamburg.de/evergabe.bieter/eva/supplierportal/fhh/tabs/home'] 
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.cc-btn.cc-dismiss'))).click()
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' div.mat-form-field-flex.ng-tns-c50-18'))).click()
            time.sleep(5)
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mat-option-9 > span'))).click()
            time.sleep(5)
        except:
            pass
            
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))[records]
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
