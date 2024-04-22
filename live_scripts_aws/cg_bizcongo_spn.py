from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cg_bizcongo_spn"
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
SCRIPT_NAME = "cg_bizcongo_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cg_bizcongo_spn'
    
    notice_data.main_language = 'FR'
  
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CG'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CDF'
    
    notice_data.document_type_description = 'ALL CALLS FOR TENDERS'
    
    notice_data.procurement_method = 2
    
    # Onsite Comment -if "li > div.others > div:nth-child(4)> div > div > div" text has "Avis général de passation des marchés" keyword then take notice_type = 2  (GPN) and if "li > div.others > div:nth-child(4)> div > div > div" text has "Avis de pré-qualification" keyword then take notice_type = 6  (PPN)
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div.others > div:nth-child(4)> div > div > div').text
        if 'Avis général de passation des marchés' in notice_type:
            notice_data.notice_type = 2
        elif 'Avis de pré-qualification' in notice_type:
            notice_data.notice_type = 6
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ouverture :
    # Onsite Comment -split only publish_date for ex."Ouverture : 29-11-2023 / " , here take only " 29-11-2023 / "
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.views-field.views-field-field-expiry > div > div").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -clôture : 
    # Onsite Comment -split only notice_deadline for ex."clôture : 11-01-2024" , here take only "11-01-2024"
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.views-field.views-field-field-expiry > div > div").text.split('/')[1].strip()
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    # Onsite Field -Sujet :
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#block-system-main  div:nth-child(3) > div > div div').text.split('Sujet :')[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -En savoir plus
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#block-system-main > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.field-item').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field - Catégorie :
    # Onsite Comment - split the data after "Catégorie :" , Replace following keywords with given respective kywords ('MARCHÉ DE SERVICES = Service' , 'MARCHÉ DE TRAVAUX = Works' , 'MARCHÉ DE FOURNITURES = Supply')
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Catégorie : ")]//parent::p').text.split('Catégorie : ')[1].strip()
        if 'Marché de Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type ='Service'
        elif 'Marché de Travaux' in notice_data.contract_type_actual:
            notice_data.notice_contract_type ='Works'
        elif 'Marché de Fournitures'  in notice_data.contract_type_actual:
            notice_data.notice_contract_type ='Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -   Référence :
    # Onsite Comment - split the data after " Référence :"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//div[@class='offre-reference']").text.split('Référence :')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Comment -   ref_url : "https://www.bizcongo.com/appels-offres/marche-de-fournitures/cgpmpmsphp-rdc-17"
    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.field-item > p > a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CG'
        customer_details_data.org_language = 'FR'

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.others > div.views-field.views-field-title > span').text

        # Onsite Field - Lieu : 
        # Onsite Comment - split only city for ex. if format like  "RDCongo - Kinshasa" then here take only  "Kinshasa" and if format like "Kalemie" , then take whole word  , ref_url : "https://www.bizcongo.com/appels-offres/marche-de-fournitures/oim-46" , "https://www.bizcongo.com/appels-offres/marche-de-fournitures/chai-18"

        try:
            customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'div.offre-lieu').text.split('Lieu : ')[1].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number =1
        data1=page_details.find_element(By.CSS_SELECTOR, 'div.info-instu-offre.col-xs-12.col-md-8 > div > div > div').text.split('Lot')[1:]
        for single_record1 in data1:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number

#         # Onsite Comment - ref_url : "https://www.bizcongo.com/appels-offres/marche-de-fournitures/coopi-sdc" ,  split lot_title for ex."Lot 1 : 5 Véhicules 4x4," , here take only "5 Véhicules 4x4"
            lot_details_data.lot_title = single_record1.split(':')[1].split(',')[0].strip()
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number+=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -Attachments
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.top-node-job_posting > div.info-instu-offre.col-xs-12.col-md-8 > a'):
            attachments_data = attachments()
            
        # Onsite Comment - ref_url :  "https://www.bizcongo.com/appels-offres/marche-de-services/unhcr-19"
            attachments_data.file_name = single_record.text.strip()
                    
            attachments_data.external_url = single_record.get_attribute("href")            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

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
    urls = ["https://www.tala-com.com/appels-offres/tous"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="block-system-main"]/div/div/div/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-system-main"]/div/div/div/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-system-main"]/div/div/div/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="block-system-main"]/div/div/div/ul/li'),page_check))
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
    
