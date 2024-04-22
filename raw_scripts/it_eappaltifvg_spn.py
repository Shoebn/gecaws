#NOTE-  after clicking on login page click on >>>>> " Bandi e avvisi " 
#NOTE- "if page get expire overright the url again" ....
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
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_eappaltifvg_spn"
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
    notice_data.script_name = 'it_eappaltifvg_spn'
    
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
    # Onsite Comment -if following word is encountered "Expression of interest" then take as "5" use following selector to check EOI "td:nth-child(2)"
    notice_data.notice_type = 4
    
    # Onsite Field -Scadenza Manifestazione d'Interesse
    # Onsite Comment -just take data for published date from Data ultima modifica


    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, " td:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Descrizione Bando di Gara
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descrizione Bando di Gara
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia Prestazione
    # Onsite Comment - Forniture - Supply, Vendita/Locazione -Service, Servizi - Service, Lavori - Service,

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Tipologia Prestazione
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Codice Cartella di Gara
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),'Codice Cartella di Gara')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Descrizione')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descrizione
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Descrizione')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Scadenza Manifestazione d'Interesse
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)>a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#opportunityDetailFEBean > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(6) > div > ul'):
            customer_details_data = customer_details()
        # Onsite Field -Descrizione Bando di Gara
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Email
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),'Email')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contatto
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),'Contatto')]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#opportunityDetailFEBean > div > div:nth-child(9)'):
            lot_details_data = lot_details()
        # Onsite Field -Codice
        # Onsite Comment -take data from "Lotti Pubblicati" only

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Titolo
        # Onsite Comment -take data from "Lotti Pubblicati" only

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Descrizione
        # Onsite Comment -click on Colonna Azione" for details use following selector "#opportunityDetailFEBean  button > span '

            try:
                lot_details_data.lot_description = page_details1.find_element(By.XPATH, '//*[contains(text(),'Descrizione')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url "https://eappalti.regione.fvg.it/esop/toolkit/opportunity/current/19243/detail.si"
# Onsite Comment -click on "Colonna Azione" for details use following selector "#opportunityDetailFEBean button > span "

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#cntDetail'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'input[type=button]:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'input[type=button]:nth-child(4)').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details1.find_element(By.CSS_SELECTOR, 'input[type=button]:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -CIG/Smart CIG
    # Onsite Comment -click on "Colonna Azione" for details use following selector "#opportunityDetailFEBean button > span "

    try:
        notice_data.related_tender_id = page_details1.find_element(By.XPATH, '//*[contains(text(),'CIG/Smart CIG')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass




# Onsite Field -ref url -"https://eappalti.regione.fvg.it/esop/toolkit/opportunity/current/19142/detail.si"
# Onsite Comment -Allegati dell'Avviso

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div:nth-child(13) > div > ul > li > table > tbody'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > a').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CLASS_NAME, 'SvgSize16 SVG-file-pdf ICON-PDF_FILE js_svg PDF_FILE').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        

        # Onsite Field -Nome
        # Onsite Comment -take data from "Allegati dell'Avviso" only ---- if description is present grab description...

            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
            
        # Onsite Field -Nome
        # Onsite Comment -from the data just select file size

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
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
page_details1 = fn.init_chrome_driver(arguments)
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://eappalti.regione.fvg.it/web/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr'),page_check))
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    