
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
import common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_empulia_spn"
Doc_Download = common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_empulia_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -if "MANIFESTAZIONE DI INTERESSE " such key words are encountered in title take notice type "5", if "AMENDMENT " such key words are encountered in title take notice type "16"  for selecting title use following selector "td:nth-child(2)" 
    notice_data.notice_type = 4
    
    
    # Onsite Field -None
    # Onsite Comment -Descrizione

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: ", str(type(e)))
        pass
    
    # Onsite Field -also take notice_no from notice url
    # Onsite Comment -split the data from "open bracket"(" till "close bracket")"

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#template_doc > thead > tr > th > h1').text.split('(')[1].split(')')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -Scadenza

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline= re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: ", str(type(e)))
        pass
    

    # Onsite Field - Data Pubblicazione	
    # Onsite Comment -click on "Tabella informativa di indicizzazione"


    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, " #table_dpcm s td:nth-child(11)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -None
    # Onsite Comment -split till open bracket "(" take data which is before open bracket 
    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'th > h1').text.split('(')[0]
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
       

    # Onsite Field -Importo Appalto:	
    # Onsite Comment -ref url "http://www.empulia.it/tno-a/empulia/Empulia/SitePages/New_Dettaglio%20Bando%20di%20Gara.aspx?getdettaglio=yes&bando=349887&tipobando=Bando&RicQ=NO&VisQ=NO&tipoDoc=BANDO_GARA_PORTALE&xslt=XSLT_BANDO_GARA_PORTALE&scadenzaBando=2024-01-19T12:00:00"

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),'Importo')]//following::td[1] ').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    # Onsite Field -Importo Appalto:	
    # Onsite Comment -ref url "http://www.empulia.it/tno-a/empulia/Empulia/SitePages/New_Dettaglio%20Bando%20di%20Gara.aspx?getdettaglio=yes&bando=349887&tipobando=Bando&RicQ=NO&VisQ=NO&tipoDoc=BANDO_GARA_PORTALE&xslt=XSLT_BANDO_GARA_PORTALE&scadenzaBando=2024-01-19T12:00:00"
    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),'Importo')]//following::td[1] ').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -Altro indirizzo web
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),'Altro indirizzo web')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass


    # Onsite Field -Tipul Appalto
    # Onsite Comment -"for "Servizi = service , Forniture = supply, Lavori pubblici=Works" 

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Tipo Appalto:')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipul Appalto
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),'Tipo Appalto:')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    # Onsite Field -Categoria Prevalente
    # Onsite Comment -ref url - "http://www.empulia.it/tno-a/empulia/Empulia/SitePages/New_Dettaglio%20Bando%20di%20Gara.aspx?getdettaglio=yes&bando=349887&tipobando=Bando&RicQ=NO&VisQ=NO&tipoDoc=BANDO_GARA_PORTALE&xslt=XSLT_BANDO_GARA_PORTALE&scadenzaBando=2024-01-19T12:00:00"

    try:
        notice_data.category = page_details.find_element(By.CSS_SELECTOR, ' tr:nth-child(14) > td > table > tbody').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass


    # Onsite Field -None
    # Onsite Comment -Dettaglio

    try:
        notice_data.notice_url = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(7) >a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"#ctl00_m_g_e1473ed7_3e49_4d7a_8380_ca0aaa3c0eda_dgList > tbody > tr"

    try:
        notice_data.notice_text = page_details.find_element(By.CSS_SELECTOR, '#template_doc > tbody ').text
    except Exception as e:
        logging.info("Exception in notice_text: ", str(type(e)))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#template_doc > tbody '):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -Ente Appaltante

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_name: ", str(type(e)))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Incaricato

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),'Incaricato:')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: ", str(type(e)))
                pass
        
            customer_details_data.org_country = 'IT'

            customer_details_data.org_language = 'IT'


            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: ", str(type(e))) 
        pass
        

        
# Onsite Field -None
# Onsite Comment - 

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#template_doc > tbody'):
            attachments_data = attachments()
        # Onsite Field -
        # Onsite Comment -

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#DownloadAllegati').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#DownloadAllegati').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass


        # Onsite Field -
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, '#DownloadAllegati').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#DownloadAllegati').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ['http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Bandi%20di%20gara%20new.aspx , http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Bandi%20di%20gara%20new.aspx?expired=1&type=All'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'#ctl00_m_g_e1473ed7_3e49_4d7a_8380_ca0aaa3c0eda_dgList > tbody > tr'))).text
            for tender_html_element in WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '#ctl00_m_g_e1473ed7_3e49_4d7a_8380_ca0aaa3c0eda_dgList > tbody > tr'))):
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.LINK_TEXT,str(page_no)))).click()
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'#ctl00_m_g_e1473ed7_3e49_4d7a_8380_ca0aaa3c0eda_dgList > tbody > tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: ", str(type(e)))
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
    