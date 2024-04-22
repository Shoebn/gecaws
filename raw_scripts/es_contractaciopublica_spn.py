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


#after opening the url select only "Preliminary market consultation" and "Tender announcements within deadline date" and "Execution" this three in "Valid phase" section and then click on "Apply Filters" for tender_details.



NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "es_contractaciopublica_spn"
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
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 0
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -Note:take only text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'app-resultats-cerca-avancada > div > div > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.flex-column.gap-1 > div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.d-flex.gap-1.fases-vigents > div.d-flex.flex-column.text-center > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Basic budget for tender (excluding VAT)
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.flex-column.gap-1 > div > span:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Basic budget for tender (excluding VAT)
    # Onsite Comment -None

    try:
        notice_data.grossbudgeteuro = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.flex-column.gap-1 > div > span:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in grossbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.flex-column.gap-1 > div:nth-child(3) > a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.gap-1.fases-vigents > div.d-flex.flex-column.text-center > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Expedient code
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Expedient code")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of contract
    # Onsite Comment -Note:Repleace following keywords with given keywords("Work projects=Works","Supplies=Supply","Services=Service")

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of contract
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedure >> Contract award procedure
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract award procedure")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject>> Estimated value of contract
    # Onsite Comment -None

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated value of contract")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject >> Basic estimate for tender
    # Onsite Comment -None

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Basic estimate for tender")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject >> Basic estimate for tender
    # Onsite Comment -None

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Basic estimate for tender")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject >> VAT
    # Onsite Comment -None

    try:
        notice_data.vat = page_details.find_element(By.XPATH, '//*[contains(text(),"VAT")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject  >> Duration of the contract
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duration of the contract")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject >> CPV
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-detall-publicacio > div:nth-child(7) > app-anunci-licitacio'):
            cpvs_data = cpvs()
        # Onsite Field -Subject >> CPV
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Contract award criteria: > Criterion:
#Note:Click on "Further information" and grab the data
# Onsite Comment -Note:if the "Criterion: is " Price" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  of the if the "Criterion: is " technical" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  if above both keyword avaiable" Price", "technical" than only pass this in criteria title .. do not pass the hole line
#reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157846
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-detall-publicacio > div:nth-child(7) > app-anunci-licitacio'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Subject >> Criterion
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Criterion")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Subject >> Weighting out of 100%
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Weighting out of 100%")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Deadline for the presentation of offers
    # Onsite Comment -None

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),"Deadline for the presentation of offers")]//following::div[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.None, 'body > app-root > main'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None
        #reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157276
        # Onsite Comment -Note:Click on "Further information" and grab the data

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.flex-column.gap-1 > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'ES'
            customer_details_data.org_language = 'ES'
        # Onsite Field -Procurement entity >> Postal address
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal address")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement entity >> Locality
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Locality")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement entity >> Post code
        # Onsite Comment -None

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Post code")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement entity >> NUTS (Nomenclature of Territorial Units for Statistics)
        # Onsite Comment -None

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS (Nomenclature of Territorial Units for Statistics)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement entity >> Telephone
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement entity >> Email address
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email address")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement entity >> Web address
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Web address")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement entity >> Contact persons >> Name
        # Onsite Comment -Note:"//*[contains(text(),"Contact persons")]//following::div[17]"Take this also data in contact_person. seperate each contact_person using comma(,).

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact persons")]//following::div[6]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procurement entity >> Main activity
        # Onsite Comment -None

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Main activity")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None
#reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157208

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > app-root > main'):
            attachments_data = attachments()
        # Onsite Field -Documantation
        # Onsite Comment -Note:split file_name.eg.,"Plec de Condicions Particulars.pdf" don't take ".pdf" in file_name.

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'app-documents-publicacio > div > div.col-md-8 > div > button').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documantation
        # Onsite Comment -Note:split the extenstion (like ".pdf")

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'app-documents-publicacio > div > div.col-md-8 > div > button').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documantation
        # Onsite Comment -Note:for the all attachment <a> tag is not avaibale .. so add the click botton code for the external url

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'app-documents-publicacio > div > div.col-md-8 > div > button').get_attribute('href')
            
        


#reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157276       
        # Onsite Field -Description of the batch
        # Onsite Comment -Note:split file_name.eg.,"33 Acta sobre A 2023_14 signat.pdf" don't take ".pdf" in file_name.

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'app-documents-publicacio > div > div > div > button').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description of the batch
        # Onsite Comment -Note:split the extenstion (like ".pdf")

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'app-documents-publicacio > div > div > div > button').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description of the batch
        # Onsite Comment -Note:for the all attachment <a> tag is not avaibale .. so add the click botton code for the external url

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'app-documents-publicacio > div > div > div > button').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None
#reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157276
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > app-root > main'):
            lot_details_data = lot_details()
        # Onsite Field -Additional information >> Description of the batch
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#informacio-complementaria-panel app-taula-lots td.cdk-cell.cdk-column-descripcio').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Additional information >> Title of the batch
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, '#informacio-complementaria-panel app-taula-lots  td.cdk-cell.cdk-column-titol').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        



#reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157916        
        # Onsite Field -Additional information >> Title of the batch
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#informacio-complementaria-panel app-taula-lots td.cdk-cell.cdk-column-titol').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Additional information >> Description of the batch
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, '#informacio-complementaria-panel app-taula-lots td.cdk-cell.cdk-column-descripcio').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://contractaciopublica.gencat.cat/ecofin_pscp/AppJava/en_GB/search.pscp?pagingPage=0&reqCode=searchCn&aggregatedPublication=false&sortDirection=1&pagingNumberPer=10&lawType=2"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,None):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div'),page_check))
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