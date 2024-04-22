from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_soresa_spn"
log_config.log(SCRIPT_NAME)
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_soresa_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_soresa_spn'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'

    notice_data.notice_type = 4
    notice_data.document_type_description = "Elenco Bandi"
    
    # Onsite Field -Scadenza
    # Onsite Comment -take publish_date as threshold

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline  < threshold:
        return

    if notice_data.notice_deadline == '' or notice_data.notice_deadline is None:
        return
    

    # Onsite Field -Tipologia Bando
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        if "Servizi" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Forniture" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Lavori pubblici" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Dettaglio
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute("href")                     
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
        
    # Onsite Field -take notice_no from notice url
    # Onsite Comment -None

    try:
        notice_data.notice_no = notice_data.notice_url.split("=")[-2].split('&')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'(//h3)[1]')))
        logging.info(notice_data.notice_url)  
    
        # Onsite Field -for following tabs use associated selectors "Esiti e Pubblicazioni" - #ui-id-4 > div > table, "Avvisi" - #ui-id-6 > div > table, "Chiarimenti" - #ui-id-8 > div > table
        # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ---- //*[@id="tabella"]/table/tbody/tr 
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-lg-9.col-md-9.col-sm-12.col-xs-12.pitch').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        
        
            # Onsite Field -Descrizione
        # Onsite Comment -None

        try:
            notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Descrizione breve")]//following::div[1]').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Importo
        # Onsite Comment -None

        try:
            est_amount = page_details.find_element(By.XPATH, '''//*[contains(text(),'Importo Appalto')]//following::p[1]''').text
            if '(Iva Esclusa)' in est_amount:
                est_amount = re.sub("[^\d\.\,]", "",est_amount)
                notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
                notice_data.netbudgeteuro  = notice_data.est_amount
                notice_data.netbudgetlc  = notice_data.est_amount
            else:
                est_amount = re.sub("[^\d\.\,]", "",est_amount)
                notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
                notice_data.grossbudgetlc  = notice_data.est_amount
                notice_data.grossbudgeteuro = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_language = 'IT'
            customer_details_data.org_country = 'IT'
        # Onsite Field -Direzione Proponente
        # Onsite Comment -None

            customer_details_data.org_name = page_details.find_element(By.XPATH, '''//*[contains(text(),'Direzione Proponente')]//following::p[1]''').text

        # Onsite Field -RUP
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '''//*[contains(text(),'RUP')]//following::p[1]''').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ui-id-2  > p ')[1:-1]:
                attachments_data = attachments()

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

            # Onsite Field -Allegati
            # Onsite Comment -None

                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass
                
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text.split(attachments_data.file_type)[0].strip()
            # Onsite Field -Allegati
            # Onsite Comment -None

                try:
                    attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'span').text.split('(')[1].split(')')[0].strip()
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
            pass
        
        
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//*[contains(text(),"Esiti e Pubblicazioni")]/following::div[1]//table').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        
        try:
            clk= WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//h3[contains(text(),"Avvisi")]'))).click()
            time.sleep(2)
        except:
            pass
        
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//*[contains(text(),"Avvisi")]/following::div[1]//table').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
            # Onsite Field -click on "Avvisi" for data 
            # Onsite Comment -ref url = "https://www.soresa.it/Pagine/BandoDettaglio.aspx?idDoc=2467968&tipoDoc=BANDO_SDA_PORTALE"

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ui-id-6'):
                external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').get_attribute('href')
                if "Determinazione" in external_url:
                    attachments_data = attachments()
                    attachments_data.external_url = external_url
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                    try:
                        attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').text.split('.')[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        
        try:
            clk2= WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//h3[contains(text(),"Chiarimenti")]'))).click()
            time.sleep(2)
        except:
            pass
        
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//*[contains(text(),"Chiarimenti")]/following::div[1]//table').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
    
    except Exception as e:
        logging.info("Exception in load_page: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title) 
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
    urls = ["https://www.soresa.it/Pagine/Bandi.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tabella"]/table/tbody/tr[3]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tabella"]/table/tbody/tr')))
                length = len(rows)
                for records in range(2,length,2):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tabella"]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'''//*[@id="ctl00_ctl45_g_87a647ad_435f_4624_bb38_90a9a7b9025e_ctl00_lstCercaBandi_btnNext"]''')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tabella"]/table/tbody/tr[3]'),page_check))
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
