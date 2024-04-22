from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_hamburg_ca"
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
SCRIPT_NAME = "de_hamburg_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_hamburg_ca'
    
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    notice_data.document_type_description = 'Award Announcements'
    
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
    
    # Onsite Field -Veröffentlichungsdatum:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(1) > div:nth-child(2) > label").text
        publish_date = re.findall('\d+.\d+.\d{4}, \d{2}:\d{2}:\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y, %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    # Onsite Field -Leistungsart:
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Sicherungsleistung/bauaffine Dienstleistung =Service','Bauleistung = Works ','Lieferleistung = Supply', 'Dienstleistung = services ','Architekten- und Ingenieurleistungen = consultancy')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(2) > label').text
        if "Sicherungsleistung" in notice_contract_type or "Bauaffine Dienstleistung" in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Bauleistung" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        elif "Lieferleistung" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Dienstleistung" in notice_contract_type:
            notice_data.notice_contract_type = "services"
        elif "Architekten- und Ingenieurleistungen" in notice_contract_type:
            notice_data.notice_contract_type = "consultancy"          
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DETAILS
    # Onsite Comment -click on DETAILS for detail page
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.button-area-style > button').click()    
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div:nth-child(1) > div > h4')))
        notice_data.notice_url = page_main.current_url
        logging.info('notice_url:-' , notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'project-award-details > div > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Vergabeart
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_main.find_element(By.XPATH, '//*[contains(text(),"Vergabeart")]//following::div[1]').text
        type_of_procedure_actual = GoogleTranslator(source='de', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_hamburg_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass       
    

    customer_details_data = customer_details()
    customer_details_data.org_country = 'DE'
    customer_details_data.org_language = 'DE'

     # Onsite Field -Ausführungsort:
    # Onsite Comment -None

    try:
        customer_details_data.org_city = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(15) > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in org_city: {}".format(type(e).__name__))
        pass

     # Onsite Field -Auftraggeber
    # Onsite Comment -take only first data as org_name

    try:
        customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, ' div > div:nth-child(3) > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass

    # Onsite Field -Adresse
    # Onsite Comment -None

    try:
        customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresse")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_address: {}".format(type(e).__name__))
        pass

    # Onsite Field -Telefon
    # Onsite Comment -None

    try:
        customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_phone: {}".format(type(e).__name__))
        pass

    # Onsite Field -Fax
    # Onsite Comment -None

    try:
        customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_fax: {}".format(type(e).__name__))
        pass

    # Onsite Field -E-Mail
    # Onsite Comment -None

    try:
        customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in org_email: {}".format(type(e).__name__))
        pass

    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number =1
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        lot_details_data.lot_description = notice_data.notice_title
        lot_details_data.contract_type = notice_data.notice_contract_type
        # Onsite Field -Leistungsart:
        # Onsite Comment -take only "Leistungsart:" data as contract_type from the given selector and Replace follwing keywords with given respective kywords ('Sicherungsleistung/bauaffine Dienstleistung =Service','Bauleistung = Works ','Lieferleistung = Supply', 'Dienstleistung = services ','Architekten- und Ingenieurleistungen = consultancy'
      
        try:
            award_details_data = award_details()
            award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Firma")]//following::div[1]').text
            award_details_data.address = page_main.find_element(By.CSS_SELECTOR, ' mat-card-content > div > div:nth-child(22)').text.split("Adresse")[1]
            # Onsite Field -Firma
            # Onsite Comment -None
            
            # Onsite Field -Adresse
            # Onsite Comment -take address from "Bezuschlagte(r) Bieter" field only
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    page_main.execute_script("window.history.go(-1)")
    
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
    urls = ['https://fbhh-evergabe.web.hamburg.de/evergabe.bieter/eva/supplierportal/fhh/tabs/zuschlagsbekanntmachungen'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.cc-window.cc-floating.cc-type-info.cc-theme-classic.cc-bottom.cc-right.cc-color-override--897518285 > div > a")))
            page_main.execute_script("arguments[0].click();",click)
            time.sleep(2)
        except:
            pass
        
        try:
            WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' mat-card-title > label')))
        except:
            pass
        try:
            for page_no in range(1,8):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="project-vertical-container"]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," button.mat-focus-indicator.mat-tooltip-trigger.mat-paginator-navigation-next.mat-icon-button.mat-button-base")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="project-vertical-container"]/div'),page_check))
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
    
