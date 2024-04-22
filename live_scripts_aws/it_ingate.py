from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_ingate"
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
import gec_common.Doc_Download_ingate as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_ingate"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'IT'
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    notice_data.script_name = "it_ingate"
    notice_data.notice_url = url
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").get_attribute('outerHTML')
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('-')[1]
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass   

    try:
        type_of_procedure = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('-')[1]
        if 'Procedura Aperta' in type_of_procedure:
            notice_data.type_of_procedure = 'Open'
        elif 'Dialogo competitivo' in type_of_procedure:
            notice_data.type_of_procedure = 'Competitive dialogue'
        elif 'Manifestazione di Interesse' in type_of_procedure:
            notice_data.type_of_procedure = 'Competitive tendering'
        elif 'Affidamento diretto' in type_of_procedure:
            notice_data.type_of_procedure = 'Direct award'
        elif 'Procedura Negoziata/Procedura Negoziata Accelerata' in type_of_procedure:
            notice_data.type_of_procedure = 'Negotiated procedure'
        elif 'Procedura Ristretta Accelerata' in type_of_procedure:
            notice_data.type_of_procedure = 'Negotiated without prior call for competition'
        elif 'Altro' in type_of_procedure:
            notice_data.type_of_procedure = 'Other'
        elif 'Affidamenti Sottosoglia' in type_of_procedure:
            notice_data.type_of_procedure = 'Other multiple stage procedure'
        elif 'Procedura Ristretta/Fast-track restricted procedure/Procedura Ristretta (Parte B)' in type_of_procedure:
            notice_data.type_of_procedure = 'Restricted'
        else:
            notice_data.type_of_procedure = 'Other'
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR,"td:nth-child(5)").text
        if 'Servizi' in notice_contract_type or 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type='Service'
        if 'Fornitura' in notice_contract_type:
            notice_data.notice_contract_type='Supply'
    except:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute("onclick")
        notice_no1 = notice_no.split("('")[1].split("'")[0].strip()
    except:
        pass
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').click()
    except:
        pass
    
    try:
        notice_data.notice_text = WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.XPATH, '//*[@id="cntDetail"]/div'))).get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass  
    
    try:
        notice_data.notice_no = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > ul > li:nth-child(1) > div.form_answer').text
    except Exception as e:
        notice_data.notice_no = notice_no1
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Descrizione')]//following::div[9]").text
        notice_data.notice_summary_english = GoogleTranslator(source='it', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:              
        tender_criteria_data = tender_criteria()  
        tender_criteria_data.tender_criteria_title = page_main.find_element(By.XPATH,"//*[contains(text(),'Descrizione')]//following::div").text.split('\n')[0]       
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__))              
        pass
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div:nth-child(14)'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IT'
            customer_details_data.org_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div > ul > li:nth-child(1) > div.form_answer').text

            try:
                customer_details_data.org_email = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(14) > div > ul > li:nth-child(3) > div.form_answer').text
            except Exception as e:
                pass
            
            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, "//*[contains(text(),'Contatto')]//following::div[1]").text
            except Exception as e:
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: ", str(type(e))) 
        pass
    
    try:
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div:nth-child(12) > div > ul > li > table > tbody > tr')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            lot_details_data.contract_type = notice_data.notice_contract_type
             
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1 
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
        

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div:nth-child(16) > div > ul > li > table > tbody > tr')[1:]:
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('title').split("Scarica il file:")[1].strip()
            try:
                file_size = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(16)  td:nth-child(2)').text
                attachments_data.file_size = file_size.split('(')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.file_type = attachments_data.file_name.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
            
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass

    try:
        page_main.execute_script("window.history.go(-1)")
    except:
        pass
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://ingate.invitalia.it/web/login.shtml'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div:nth-child(1) > div > h2 > a'))).click()
        except:
            pass
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="OpportunityListManager"]/div/section/div[2]/table/tbody[2]/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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

    
