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
SCRIPT_NAME = "fr_marchespublics"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
# after opening the url fields in front of "Date limite de remise des plis" such as "Entre le" and "et le" shuold be blank. and in the fields in front of "Date de mise en ligne" such as "Entre le" and "et le" select date.
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'fr_marchespublics'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'FR'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
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

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-2 > div > div:nth-child(2) > div.date").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-1 > div > div.cloture-line > div.date").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works','Fournitures = Supply')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.actions > ul.list-unstyled > li:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.m-b-10').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Référence :
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Référence :")]//following::span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet :
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet :")]//following::div[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet :
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet :")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet :")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procédure :
    # Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Procédure :")]//following::div").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marchespublics_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type d'annonce :
    # Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details.

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Type d'annonce :")]//following::div').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -to take cpvs click on "+" sign after the "div.panel-heading > h1" in page_details

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#recap-consultation'):
            cpvs_data = cpvs()
        # Onsite Field -Code CPV :
        # Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details.     2.here "37535200 (Code principal)" take only "37535200" in cpv_code.

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV :")]//following::div').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#recap-consultation'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -Organisme :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organisme :")]//following::span').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lieu d'exécution :
        # Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details.    2.here "(62) Pas-de-Calais" take only "Pas-de-Calais" in org_city.

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieu d'exécution :")]//following::div').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details.  	2.click on "div > span > a" to get lot_details from page_details.

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.modal-body.clearfix'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details1.find_element(By.CSS_SELECTOR, '#headingOne > span').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details1.find_element(By.CSS_SELECTOR, '#headingOne > span').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details1.find_element(By.CSS_SELECTOR, '#headingOne > strong').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works','Fournitures = Supply')

            try:
                lot_details_data.contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#pub > div > div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -1.don't grab file_size in file_name. eg.,in "Règlement de consultation - 74,96 Ko" take only "Règlement de consultation" .	2.take this as file_name from "div.actions > ul > li:nth-child(2) > a" in tender_html_element. 	3.take this also in file_name "div.section-body > div:nth-child(1) > div > ul > li" from page_details.

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#panelPieces > ul > li').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.don't grab file_name in file_size. eg.,"Règlement de consultation - 74,96 Ko" take only "74,96 Ko".

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, '#panelPieces > ul > li').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.take this also in external_url "div.section-body > div:nth-child(1) > div > ul > li > a" from page_details. 		2.take this also in external_url "div.actions > ul > li:nth-child(3) > a" in tender_html_element.

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#panelPieces > ul  a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://marchespublics596280.fr/?page=Entreprise.EntrepriseAdvancedSearch&searchAnnCons"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,7):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))[records]
                extract_and_save_notice(tender_html_element)
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div'),page_check))
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