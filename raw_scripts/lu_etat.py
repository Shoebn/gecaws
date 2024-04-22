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
SCRIPT_NAME = "lu_etat"
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
    notice_data.script_name = 'lu_etat'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'FR'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'LU'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
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
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Services=Service','Travaux=Works','Fournitures=Supply')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.objet-line > div >div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.actions > ul.list-unstyled > li:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.m-b-10').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Date et heure limite de remise des plis :
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.XPATH, "//*[contains(text(),"Date et heure limite de remise des plis :")]//following::span[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
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
    # Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get type_of_procedure_actual.	 	2.split type_of_procedure_actual eg., here "10 européenne ouverte" take only "européenne ouverte".
    try:
        notice_data.type_of_procedure_actual = single_record.find_element(By.XPATH, "//*[contains(text(),"Procédure :")]//following::div[1]").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/lu_etat_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type d'avis :
    # Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get document_type_description.

    try:
        notice_data.document_type_description = single_record.find_element(By.XPATH, '//*[contains(text(),"Type d'avis :")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get cpvs.

    try:              
        for single_record in page_details.find_elements(By.XPATH, '#recap-consultation'):
            cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get cpvs_code.     2.here "37535200 (Code principal)" take only "37535200" in cpv_code.

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV :")]//following::div[1]/span').text
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
        # Onsite Field -Organisme :
        # Onsite Comment -1.split org_name. eg., here "Portail des marchés publics ( - )" take only "Portail des marchés publics" in org_name.

            try:
                customer_details_data.org_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Organisme :")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'LU'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get lot_details.  	2.click on "div > span > a" to get lot_details from page_details. 		3.reference_url "https://pmp.b2g.etat.lu/entreprise/consultation/528290?orgAcronyme=t5y"

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.modal-body.clearfix'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -1.if not availabel then take local_title in lot_title.

            try:
                lot_details_data.lot_title = page_details1.find_element(By.CSS_SELECTOR, '#headingOne > span').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description :
        # Onsite Comment -1.click on '+' to get lot_description.      2.if not availabel then take local_title in lot_title.

            try:
                lot_details_data.lot_description = page_details1.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
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
                
        # Onsite Field -Catégorie :
        # Onsite Comment -1.click on '+' to get contract_type       .2.Replace following keywords with given respective keywords ('Travaux = works','Fournitures = supply','Services = Services')

            try:
                lot_details_data.contract_type = page_details1.find_element(By.XPATH, '//*[contains(text(),"Catégorie")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -None
        # Onsite Comment -1.click on '+' to get lot_cpvs.

            try:
                for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#collapse_1 > div'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -CPV:
                    # Onsite Comment -here "37535200 (Code principal)" take only "37535200" in cpv_code.

                    lot_cpvs_data.lot_cpv_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::div[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
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
        # Onsite Comment -1.don't grab file_size in file_name. eg.,in "Règlement de consultation - 74,96 Ko" take only "Règlement de consultation"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'ul > li.picto-link').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.don't grab file_name in file_size. eg.,"Règlement de consultation - 74,96 Ko" take only "74,96 Ko".

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'ul > li.picto-link').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.take this also in external_url "#panelPieces > ul >li > span > a" from page_details.

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'ul > li.picto-link > a').get_attribute('href')
            
        
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
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://pmp.b2g.etat.lu/?page=Entreprise.EntrepriseAdvancedSearch&searchAnnCons"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,9):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))[records]
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