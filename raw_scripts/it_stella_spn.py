from gec_common.gecclass import *
import logging
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_centraleacquisti"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Note : you have to open "Drop down" in page_detail to view indivisual section, in that section details are contained





#Steps to explore Tender Details ->

#   1) first go to URL "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza?t=Bandi&ente=regione"

#   2)  click on "Azzera Filtri" button for reset filter 

#   3) select "Bandi di gara" option in drop down , after that you will see details




#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_stella_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
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
    
    # Onsite Field -TIPO
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'app-tabella-td:nth-child(1) > td').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CIG/N.Gara
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'app-tabella-td:nth-child(2) > td').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -IMPORTO
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'app-tabella-td:nth-child(5) > td').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -IMPORTO
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.grossbudgetlc = single_record.find_element(By.CSS_SELECTOR, 'app-tabella-td:nth-child(5) > td').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -SCADENZA
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "app-tabella-td:nth-child(6) > td").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -TITOLO
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'app-tabella-td:nth-child(3) > td').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -click on (magnifying glass symbol) , inspect url for detail page , url ref = "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'app-tabella-td:nth-child(7) > td > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -for view individual details you have to open drop down section
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'app-dettaglio-bando > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = single_record.find_element(By.XPATH, '//*[contains(text(),"Descrizione breve:")]//following::div').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descrizione breve:
    # Onsite Comment -split the notice_summary_english from detail_page

    try:
        notice_data.notice_summary_english = single_record.find_element(By.XPATH, '//*[contains(text(),"Descrizione breve:")]//following::div').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo Appalto:
    # Onsite Comment -split the data from   "DETTAGLIO" this drop down  , reference_url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1655057&tipo_doc=BANDO_GARA_PORTALE",   Replace following keywords with given respective keywords ('Forniture = Supply' , 'Servizi = Services' , 'Lavori = Services')

    try:
        notice_data.notice_contract_type = single_record.find_element(By.XPATH, '//*[contains(text(),"Tipo Appalto:")]//following::div').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-dettaglio-bando > div'):
            customer_details_data = customer_details()
        # Onsite Field -Ente Appaltante:
        # Onsite Comment -split the data from  "DETTAGLIO" this section,

            try:
                customer_details_data.org_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Ente Appaltante:")]//following::div').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
        # Onsite Field -Incaricato:
        # Onsite Comment -split the data from "DETTAGLIO " this section

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),"Incaricato")]//following::div').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Comune Sede di Gara:
        # Onsite Comment -click on "TABELLA INFORMATIVA DI INDICIZZAZIONE" this drop down for split the details > selector = "#heading3 > button",

            try:
                customer_details_data.org_city = single_record.find_element(By.XPATH, '//*[contains(text(),"Comune Sede di Gara:")]//following::div').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Indirizzo Sede di Gara:
        # Onsite Comment -click on "TABELLA INFORMATIVA DI INDICIZZAZIONE" this drop down for split the details > selector = "#heading3 > button",           ref url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1655057&tipo_doc=BANDO_GARA_PORTALE"

            try:
                customer_details_data.org_address = single_record.find_element(By.XPATH, '//*[contains(text(),"Indirizzo Sede di Gara:")]//following::div').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            # Onsite Field -TABELLA INFORMATIVA DI INDICIZZAZIONE > Tipo di Amministrazione:
    # Onsite Comment -reference url "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1654050&tipo_doc=BANDO_GARA_PORTALE"
              try:
                customer_details_data.customer_main_activity = single_record.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione:")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
                
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -TABELLA INFORMATIVA DI INDICIZZAZIONE
# Onsite Comment -click on " TABELLA INFORMATIVA DI INDICIZZAZIONE" this drop down for split the cpv code

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#heading3 > button'):
            cpvs_data = cpvs()
        # Onsite Field -Codice CPV:
        # Onsite Comment -split the following data from this xpath

            try:
                cpvs_data.cpv_code = single_record.find_element(By.XPATH, '//*[contains(text(),"Codice CPV:")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

# Onsite Field -DETTAGLIO
# Onsite Comment -click on " DETTAGLIO" drop down for split "tender_criteira",

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#heading1 > button'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Criterio Aggiudicazione:
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Criterio Aggiudicazione:")]//following::div').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass    
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-dettaglio-bando > div'):
            lot_details_data = lot_details()
        # Onsite Field -TITOLO
        # Onsite Comment -split the data from tender_html_page

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'app-tabella-td:nth-child(3) > td').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Descrizione breve:
        # Onsite Comment -split the description from detail_page

            try:
                lot_details_data.lot_description = single_record.find_element(By.XPATH, '//*[contains(text(),"Descrizione breve:")]//following::div').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Data Pubblicazione:
    # Onsite Comment -click on " TABELLA INFORMATIVA DI INDICIZZAZIONE" this drop down for split the publish_date ,  when you click on "#heading3 > button" this button the section will be open

    try:
        publish_date = single_record.find_element(By.XPATH, "//*[contains(text(),"Data Pubblicazione:")]//following::div").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
# Onsite Field -Documentazione
# Onsite Comment -split the data from "Documentazione" section,   which is into  "DETTAGLIO" section,   ref url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#heading1n > button'):
            attachments_data = attachments()
        # Onsite Field -Documentazione
        # Onsite Comment -split the file type , for ex . " DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO.docx" here split only "docx", ref url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#collapse1n > div  div > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione
        # Onsite Comment -split only file_name for ex."Disciplinare di gara:  DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO.docx", here split only "Disciplinare di gara",     split the data before " :(colon) "    url ref : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#collapse1n  div  strong').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione
        # Onsite Comment -split the file description , for ex."DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO.docx" here split only "DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO", ref url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, '#collapse1n > div  div > a').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#collapse1n > div  div > a').get_attribute('href')
            
  

        # Onsite Field -Avvisi di Sospensione > Allegato
        # Onsite Comment -Avvisi di Sospensione > Allegato, take file_type from title attribute.        reference url"https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1654050&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#collapse3n > div > div > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Avvisi di Sospensione > Allegato
        # Onsite Comment -reference url "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1654050&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#collapse3n > div > div > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -Avvisi di Sospensione > Allegato
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#collapse2n > div > div').get_attribute('href')




        # Onsite Field -Avvisi di Rettifica > Allegato
        # Onsite Comment -Avvisi di Rettifica > Allegato, take file_type from title attribute.        reference url"https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1654050&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#collapse2n > div > div').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Avvisi di Rettifica > Allegato
        # Onsite Comment -reference url "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1654050&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#collapse2n > div > div').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -Avvisi di Rettifica > Allegato
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#collapse2n > div > div > a').get_attribute('href')




        # Onsite Field -AVVISI
        # Onsite Comment -take file_type from title attribute.        reference url "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1619758&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),'AVVISI')]//following::div/a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -AVVISI
        # Onsite Comment -reference url "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1619758&tipo_doc=BANDO_GARA_PORTALE"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#collapse23 > div > div > div > div > div > div').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -AVVISI
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),'AVVISI')]//following::div/a').get_attribute('href')
            
      
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -if field 'URL di pubblicazione su' in detail page have value then pass additional_source_name as static or else it will be blank 
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'

    
    # Onsite Field -URL di pubblicazione su
    # Onsite Comment -if field 'URL di pubblicazione su' in detail page have value then pass additional_tender_url and then take url from this field or else it will be blank 
    try:
        notice_data.additional_tender_url = page_details.find_element(By.By.XPATH, '//*[contains(text(),"URL di pubblicazione su")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza?t=Bandi&ente=regione","https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza?t=Bandi&ente=altri"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="elenco"]/div/app-tabella/div/table/app-tabella-tbody/tbody/app-tabella-tr/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="elenco"]/div/app-tabella/div/table/app-tabella-tbody/tbody/app-tabella-tr/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="elenco"]/div/app-tabella/div/table/app-tabella-tbody/tbody/app-tabella-tr/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="elenco"]/div/app-tabella/div/table/app-tabella-tbody/tbody/app-tabella-tr/tr'),page_check))
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
