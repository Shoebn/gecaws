from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_had"
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
SCRIPT_NAME = "de_had"
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
    notice_data.script_name = 'de_had'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'DE'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -"Öffentliche Ausschreibung/Auftragsbekanntmachung" , "Korrekturbekanntmachung / Berichtigung" , "Vorinformation"
    # Onsite Comment -for  "Öffentliche Ausschreibung" and  "Auftragsbekanntmachung" keyword take notice type(4)  , for  "Korrekturbekanntmachung"  and "Berichtigung" this keyword take notice type (16),  for " Vorinformation" this keyword take notice type(2)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    notice_type  = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > div').text
    logging.info(notice_type)
    if 'Öffentliche Ausschreibung' in notice_type or 'Auftragsbekanntmachung' in notice_type:
        notice_data.notice_type = 4
    elif 'Korrekturbekanntmachung' in notice_type or 'Berichtigung' in notice_type:
        notice_data.notice_type = 16
    elif 'Vorinformation' in notice_type:
        notice_data.notice_type = 2
    else:
        notice_data.notice_type = 4
 
    try:
        notice_data.local_title=tender_html_element.find_element(By.CSS_SELECTOR, "#innerframe > table:nth-child(1) > tbody > tr> td:nth-child(2)").text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except:
        pass
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text.split('\n')[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2) > div").text
        logging.info(notice_data.type_of_procedure_actual)
        type_of_procedure=GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets\\de_had_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

 
    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'form > table > tbody > tr'))).click()   
        notice_data.notice_url = page_main.current_url
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
 
    try:
        text=WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="innerframe"]/table[2]'))).text
    except:
        pass


    try:
        notice_data.notice_no = text.split('HAD-Referenz-Nr.: ')[1].split('\n')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, 'td > h3').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_contract_type =text.split('Art des Auftrags:')[1].split('\n')[0]
        if 'Lieferleistung' in notice_contract_type:
            notice_data.notice_contract_type='Supply'
        elif 'Bauauftrag' in notice_contract_type:
             notice_data.notice_contract_type='Works'
        elif 'Dienstleistung' in notice_contract_type or 'Dienstleistungen' in notice_contract_type:
            notice_data.notice_contract_type='Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.additional_tender_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Kommunikation")]//following::a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
 
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
 
    try:
        notice_summary_english = text.split('Kurze Beschreibung')[1].split('\n')[1]
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except:
        try:
            notice_summary_english = text.split('Art des Auftrags')[1].split('\n')[1]
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
        except Exception as e: 
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass   
    try:
        notice_data.local_description = text.split('Kurze Beschreibung')[1].split('\n')[1]
    except:
        try:
            notice_data.local_description = text.split('Art des Auftrags')[1].split('\n')[1]
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table:nth-child(2)'):
            customer_details_data = customer_details()
            
            try:
                customer_details_data.org_name = single_record.text.split('Offizielle Bezeichnung:')[1].split('\n')[0]
            except:
                try:
                    customer_details_data.org_name = single_record.text.split('I.1)Name und Adressen')[1].split('\n')[0]
                except:
                    customer_details_data.org_name ='HAD - Hessische Ausschreibungsdatenbank'
                    pass

            try:
                customer_details_data.org_email = single_record.text.split('E-Mail:')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_address = customer_details_data.org_name 
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'DE'
            customer_details_data.org_language = 'DE'

            try:
                customer_details_data.org_fax = text.split('Fax')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_phone = text.split('Telefon')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.customer_nuts = text.split('NUTS code: ')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try: 
        if 'cpv' in text.lower():
            cpvs_data = cpvs()
            cpvs_data.cpv_code = re.findall('\d{8}', text)[0]
            
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)        
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        try:
            lot_details_data.lot_title = text.split('Bezeichnung des Auftrags')[1].split('\n')[1]
        except:
            lot_details_data.lot_title=notice_data.notice_title
            notice_data.is_lot_default = True

        try:
            lot_details_data.lot_description = lot_details_data.lot_title
        except Exception as e: 
            lot_details_data.lot_description = notice_data.notice_summary_english 
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass

        try:
            contract_start_date = text.split('Beginn ')[1].split('\n')[0]
            contract_start_date  = re.findall('\d+.\d+.\d{4}',contract_start_date )[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

        try:
            lot_details_data.contract_type = notice_data.notice_contract_type
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass

        try: 
            lot_cpvs_data = lot_cpvs()
            lot_cpvs_data.lot_cpv_code = cpvs_data.cpv_code

            lot_cpvs_data.lot_cpvs_cleanup()
            lot_details_data.lot_cpvs.append(lot_cpvs_data)        
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="innerframe"]/table[1]/tbody'))).text
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://www.had.de/onlinesuche_erweitert.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Erweiterte Suche'))).click()

        clk=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="innerframe"]/form/table[1]/tbody/tr[4]/td[1]/select/optgroup[1]/option[2]'))).click()

        clk=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="innerframe"]/form/table[1]/tbody/tr[4]/td[2]/input'))).click()

        try:
            for page_no in range(1,9):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="innerframe"]/table[1]/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="innerframe"]/table[1]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="innerframe"]/table[1]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#innerframe > table:nth-child(3) > tbody > tr > td:nth-child(3) > form > input[type=submit]:nth-child(26)')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 5).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="innerframe"]/table[1]/tbody/tr[2]'),page_check))
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
