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



# Note:Open the site than click on "li:nth-child(5) > ul > li:nth-child(1) > a" this button then grab the data 




NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pl_platformza_spn"
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
    notice_data.script_name = 'pl_platformza_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'PLN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'PL'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.col-sm-8.col-xs-8.product-info > b').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Note:Splite notice_no in local_title ex,."ZP.26.2.135.2023 Dostawa aparatu rtg wraz systemem do radiografii cyfrowej (ID 863319)" take for "ZP.26.2.135.2023".   Note:If notice_no is blank than take from url in page_deatail

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.col-sm-8.col-xs-8.product-info > b').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.col-sm-8.col-xs-8.product-info > b > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.container > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Termin >> Zamieszczenia
    # Onsite Comment -Note:Grab time also

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Zamieszczenia")]//following::td[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Termin >> Składania
    # Onsite Comment -Note:Grab time also

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),"Składania")]//following::td[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Termin >> Rodzaj
    # Onsite Comment -Note:Repleace following keywords with given keywords("Dostawy=Supply","Usługa=Service","Robota budowlana=Works")

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Rodzaj")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -Termin >> Tryb
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Tryb")]//following::td[1]").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/pl_platformza_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass   
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.container > div > div'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -Note:Take after title

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.col-sm-8.col-xs-8.product-info').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.row.company-auction-section div:nth-child(2) div div b').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Take a first data

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.row.company-auction-section div:nth-child(2) div > div > a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -tel.
        # Onsite Comment -Note:Take after this "tel." keyword

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"tel.")]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -e-mail
        # Onsite Comment -Note:Take after this "e-mail" keyword

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"e-mail:")]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'PL'
            customer_details_data.org_language = 'PL'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.container > div > div'):
            attachments_data = attachments()
        # Onsite Field -Attachments to the proceedings >> NAME
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#allAttachmentsTable tr > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachments to the proceedings >> ENLARGEMENT
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#allAttachmentsTable tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachments to the proceedings >> SIZE (kB)
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, '#allAttachmentsTable tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachments to the proceedings >> DOWNLOAD
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#allAttachmentsTable tr > td:nth-child(6) a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

# Onsite Field -VEZI PROCEDURA
# Onsite Comment -take data from "Przedmiot zamówienia" only

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#offerForm > div:nth-child(4) > div > div > table'):
            lot_details_data = lot_details()
        # Onsite Field -LP
        # Onsite Comment -

            try:
                lot_details_data.lot_number = page_details.find_element(By.CSS_SELECTOR, '#offerForm  td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NAZWA
        # Onsite Comment -take data from "Przedmiot zamówienia" only
            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#offerForm  td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -OPIS I ZAŁĄCZNIKI	
        # Onsite Comment -take data from "Przedmiot zamówienia" only

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'd#offerForm  td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ILOŚĆ/ JM
        # Onsite Comment -take data from "Przedmiot zamówienia" only   ..... just take value in quantity eg."50 pcs." take "50 in quantity"
            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, '#offerForm  td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ILOŚĆ/ JM
        # Onsite Comment -take data from "Przedmiot zamówienia" only   ..... just take units in UOM eg."50 pcs." take "pcs in UOM"

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, '#offerForm  td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass


        # Onsite Field -just take data from "Kryteria i warunki formalne"
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(5) > div > div > table > tbody'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -just take data from "Kryteria i warunki formalne"
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.CSS_SELECTOR, '#offerForm td:nth-child(2)').text
			
                    # Onsite Field -CRITERIUM WEIGHT
                    # Onsite Comment -just take data from "Kryteria i warunki formalne"

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.CSS_SELECTOR, '#offerForm td:nth-child(3)').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://platformazakupowa.pl/all"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="active"]/div[1]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="active"]/div[1]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="active"]/div[1]/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="active"]/div[1]/div'),page_check))
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