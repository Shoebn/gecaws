from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_trasparenza"
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
SCRIPT_NAME = "it_trasparenza"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element,n_type):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'IT'    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = n_type
    notice_data.procurement_method = 2
    notice_data.script_name = 'it_trasparenza'
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.blksotto > span').get_attribute("href")
    except:
        pass
    try:
        notice_data.notice_no = notice_url.split('/')[4].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.titolo').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__))
        pass
    
    try:
        estimated_amount = tender_html_element.find_element(By.CSS_SELECTOR, " div.datibando > div:nth-child(2)").text.split('Importo:')[1].split('\n')[0]
        est_amount = re.sub("[^\d\.\,]", "", estimated_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in estimated_amount: {}".format(type(e).__name__))
        pass
    
    try:  
        n_url = 'https://trasparenza.aulss3.veneto.it'
        notice_data.notice_url = n_url + notice_url
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.blk1.blk1_8.attivo').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Categoria:")]//following::td[1]').text
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Fornitura' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#container > div.rightside > div > div > div.pagina'))).get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Stato:')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass
    
    customer_details_data = customer_details()
    customer_details_data.org_name = 'UOC Servizi Tecnici e Patrimoniali'
    customer_details_data.org_country = 'IT'
    
    try:
        customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Riferimenti:")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in contact_person: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Riferimenti:")]//following::td').text.split('Telefono: ')[1].split('\n')[0]
    except Exception as e:
        logging.info("Exception in org_phone: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Riferimenti:")]//following::td').text.split('Email:')[1].split(';')[0].strip()
    except Exception as e:
        logging.info("Exception in org_email: {}".format(type(e).__name__))
        pass
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.ballegat'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a.spostatut').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' a.spostatut').get_attribute('href')
            attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'a.spostatut').text
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
       
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr:nth-child(2)'):
            tender_criteria_data = tender_criteria()
            tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, ' div.pagina > table > tbody > tr:nth-child(2) > td:nth-child(2)').text
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Data inizio:')]//following::td[1]").text
        publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
        try:
            publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)     
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Data scadenza:')]//following::td[1]").text
        notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)
        try:    
            notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    try:
        if notice_data.notice_type == 7:
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english = notice_data.notice_title

            
            award_details_data = award_details()
            # Onsite Field -Data aggiudicazione:
            # Onsite Comment -None

            award_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Data aggiudicazione:')]//following::td[1]").text
            award_date = GoogleTranslator(source='it', target='en').translate(award_date)
            award_date = re.findall('\w+ \d+, \d{4}',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)

    except Exception as e:
        logging.info("Exception in award_details: {}".format(type(e).__name__))
        pass  
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ['https://trasparenza.aulss3.veneto.it/index.cfm?action=trasparenza.bandi'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk1 = page_main.find_element(By.CSS_SELECTOR, "a.btn.rosso.c_100").click()
        time.sleep(2)
        n_type = 4

        try:
            for page_no in range(2,10):
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#lista_elenco_bandi_elenco > div.elenco_bandi > a')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#lista_elenco_bandi_elenco > div.elenco_bandi > a')))[records]
                    extract_and_save_notice(tender_html_element,n_type)
                    if notice_count >= MAX_NOTICES:
                        break
           
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
                                
        time.sleep(2)        
        clk2 = page_main.find_element(By.CSS_SELECTOR, "a.btn.azzurro.c_4").click()
        time.sleep(2)
        n_type = 7

        try:
            for page_no in range(2,10):
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#lista_elenco_bandi_elenco > div.elenco_bandi > a')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#lista_elenco_bandi_elenco > div.elenco_bandi > a')))[records]
                    extract_and_save_notice(tender_html_element,n_type)
                    if notice_count >= MAX_NOTICES:
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
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
        
        time.sleep(2)  
        clk3 = page_main.find_element(By.CSS_SELECTOR, "#container > div.rightside > div > div > div.tab_cerca.stati_bandi.righta > a.btn.giallo.c_2").click()
        time.sleep(2)
        n_type = 16
        
        try:
            for page_no in range(2,10):
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#lista_elenco_bandi_elenco > div.elenco_bandi > a')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#lista_elenco_bandi_elenco > div.elenco_bandi > a')))[records]
                    extract_and_save_notice(tender_html_element,n_type)
                    if notice_count >= MAX_NOTICES:
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
