
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
SCRIPT_NAME = "ca_seao_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    
    
 #-----------click on "Recherche avancée" then click "Rechercher" and then In "Statuts" select "Publié" and "Annulé" to get tender data and rest should be "all"----------------#  
    
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'ca_seao_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'FR'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'CAD'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Fermeture
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Titre
    # Onsite Comment -None

    try:
        notice_data.local_title = single_record.find_element(By.XPATH, '//*[contains(text(),'Titre')]//following::span[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = single_record.find_element(By.XPATH, '//*[contains(text(),'Description')]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = single_record.find_element(By.XPATH, '//*[contains(text(),'Description')]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de l'avis :
    # Onsite Comment -None

    try:
        notice_data.document_type_description = single_record.find_element(By.XPATH, '//*[contains(text(),'Type de ')]//following::span [1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de l'avis :  --- Travaux de construction - Works Approvisionnement (biens) - Goods Services de nature technique - Services Services professionnels - Services
    # Onsite Comment -refer number "1751687"

    try:
        notice_data.notice_no = single_record.find_element(By.XPATH, '//*[contains(text(),'référence')]//following::span [1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de l'avis :
    # Onsite Comment -None

    try:
        notice_data.notice_contract_type = single_record.find_element(By.XPATH, '//*[contains(text(),'Nature du contrat :')]//following::span [1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, '#dvOpportunityDetail').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#dvOpportunityDetail'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = single_record.find_element(By.XPATH, '//*[contains(text(),'Organisme')]//following::span [1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_address = single_record.find_element(By.XPATH, '//*[contains(text(),'Adresse')]//following::span [1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split "Telephone" and "number" from the selector--just take number
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),'Téléphone')]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split contact person from "Contact" to "Telephone"
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),'Contact')]//following::td [1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split contact person from "Contact" to "Telephone"
        # Onsite Comment -None

            try:
                customer_details_data.org_email = single_record.find_element(By.XPATH, '//*[contains(text(),'Courriel')]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'CA'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#dvOpportunityDetail'):
            lot_details_data = lot_details()
        # Onsite Field -just take following data ----take data which is after "lot"
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),'Lot ')]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -just take following data ----take data which is after "lot"
        # Onsite Comment -"https://seao.ca/OpportunityPublication/ConsulterAvis/Recherche?callingPage=3&ItemId=f7cb8b65-551f-481f-9a77-ab31cb7cf806&COpp=Search&p=3&searchId=6bad23dd-db01-4601-a4e0-b0c100412438"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),'LOT1 ')]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass  
                
        # Onsite Field -just take following data ----take data which is after "lot"
        # Onsite Comment -"https://seao.ca/OpportunityPublication/ConsulterAvis/Recherche?callingPage=3&ItemId=f7cb8b65-551f-481f-9a77-ab31cb7cf806&COpp=Search&p=3&searchId=6bad23dd-db01-4601-a4e0-b0c100412438"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),'LOT1 ')]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),'Lot ')]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -just take following data ----take data which is after "lot"
        # Onsite Comment -None

            try:
                lot_details_data.file_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Lot ')]').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -just take following data ----take data which is after "lot"
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Lot ')]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Nature du contrat :')]//following::span [1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
                
                        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),'Nature du contrat :')]//following::span [1]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'dvOpportunityDetail'):
            cpvs_data = cpvs()
        # Onsite Field -ref no - 1751552 for cpv data pg
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, 'cpv -//*[contains(text(),'Classifications')]//following::div[1]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#pnlDocDistrib > table > tbody'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#pnlDocDistrib  td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_description = page_details.find_element(By.CSS_SELECTOR, '#pnlDocDistrib  td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#pnlDocDistrib td:nth-child(6) > a').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, '#pnlDocDistrib td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#pnlDocDistrib > table > tbody').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass



# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '#trSummaryCriterias'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Critères de sélection
        # Onsite Comment -split title from selector
            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, '#lbSummaryCriterias > p > span > span').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères de sélection
        # Onsite Comment -split weight from selector 

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, '#lbSummaryCriterias > p > span > span').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass



    # Onsite Field -Durée prévue du contrat sans les options (en mois)
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée prévue du contrat sans les options (en mois) :")]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass


   # Onsite Field -Catégorie
    # Onsite Comment -None

    try:
        notice_data.category = page_details.find_element(By.CSS_SELECTOR, '#pnlUNSPSC > div:nth-child(3) > div.data > ul > li').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass


    # Onsite Field -Type de l'avis :
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = single_record.find_element(By.XPATH, '//*[contains(text(),'Nature du contrat :')]//following::span [1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))


        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ['https://seao.ca/Recherche/avis_trouves.aspx?callingPage=3&Results=1&searchId=d854e9d4-6cf6-4f34-9689-b0c10014468d#p=1'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tblResults"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblResults"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblResults"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tblResults"]/tbody/tr'),page_check))
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
    