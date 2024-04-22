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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cg_bizcongo_spn"
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
    notice_data.script_name = 'cg_bizcongo_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'FR'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CG'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'CDF'
    
    # Onsite Field -None
    # Onsite Comment -if "li > div.others > div:nth-child(4)> div > div > div" text has "Avis général de passation des marchés" keyword then take notice_type = 2  (GPN) and if "li > div.others > div:nth-child(4)> div > div > div" text has "Avis de pré-qualification" keyword then take notice_type = 6  (PPN)
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2



    # Onsite Field -Ouverture :
    # Onsite Comment -split only publish_date for ex."Ouverture : 29-11-2023 / " , here take only " 29-11-2023 / "

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.views-field.views-field-field-expiry > div > div").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    # Onsite Field -clôture : 
    # Onsite Comment -split only notice_deadline for ex."clôture : 11-01-2024" , here take only "11-01-2024"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.views-field.views-field-field-expiry > div > div").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'ALL CALLS FOR TENDERS'


    # Onsite Field -Sujet :
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#block-system-main  div:nth-child(3) > div > div div').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass



    try:
        notice_data.local_description = page_details.find_element(By.XPATH, 'div.field-item').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -
    # Onsite Comment -

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, 'div.field-item').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass


    # Onsite Field -En savoir plus
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url


    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, '#block-system-main > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')



    # Onsite Field - Catégorie :
    # Onsite Comment - split the data after "Catégorie :" , Replace following keywords with given respective kywords ('MARCHÉ DE SERVICES = Service' , 'MARCHÉ DE TRAVAUX = Works' , 'MARCHÉ DE FOURNITURES = Supply')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Catégorie :")]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Catégorie :
    # Onsite Comment -format 1

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Catégorie :")]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass    
  

    
    # Onsite Field -   Référence :
    # Onsite Comment - split the data after " Référence :"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '//*[contains(text(),'Référence :')]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass



    # Onsite Field -
    # Onsite Comment -   ref_url : "https://www.bizcongo.com/appels-offres/marche-de-fournitures/cgpmpmsphp-rdc-17"

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, 'div.field-item > p > a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -None
    # Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#block-system-main > div > div > div'):
            customer_details_data = customer_details()

            customer_details_data.org_country = 'CG'
            customer_details_data.org_language = 'FR'


        # Onsite Field -
        # Onsite Comment -

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.XPATH, 'div.others > div.views-field.views-field-title > span').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass

     
        
        # Onsite Field - Lieu : 
        # Onsite Comment - split only city for ex. if format like  "RDCongo - Kinshasa" then here take only  "Kinshasa" and if format like "Kalemie" , then take whole word  , ref_url : "https://www.bizcongo.com/appels-offres/marche-de-fournitures/oim-46" , "https://www.bizcongo.com/appels-offres/marche-de-fournitures/chai-18"

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, 'div.offre-lieu').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
      
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.info-instu-offre.col-xs-12.col-md-8 > div > div > div'):
            lot_details_data = lot_details()


     # Onsite Field -
    # Onsite Comment -   ref_url : "https://www.bizcongo.com/appels-offres/marche-de-fournitures/coopi-sdc" ,  split actual_number for ex."Lot 1 : 5 Véhicules 4x4," , here take only "Lot 1"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.info-instu-offre.col-xs-12.col-md-8 > div > div > div').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -
        # Onsite Comment - ref_url : "https://www.bizcongo.com/appels-offres/marche-de-fournitures/coopi-sdc" ,  split lot_title for ex."Lot 1 : 5 Véhicules 4x4," , here take only "5 Véhicules 4x4"


            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.info-instu-offre.col-xs-12.col-md-8 > div > div > div').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

        # Onsite Field -
        # Onsite Comment - ref_url : "https://www.bizcongo.com/appels-offres/marche-de-fournitures/coopi-sdc", split only lot_grossbudgetlc for ex. "LOT 1 : 10.000 USD" , here take only "10.000", convert the amount from USD to CDF

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div.info-instu-offre.col-xs-12.col-md-8 > div > div > div').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass



# Onsite Field -Attachments
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.top-node-job_posting > div.info-instu-offre.col-xs-12.col-md-8'):
            attachments_data = attachments()
            

        # Onsite Field -
        # Onsite Comment - ref_url :  "https://www.bizcongo.com/appels-offres/marche-de-services/unhcr-19"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.top-node-job_posting > div.info-instu-offre.col-xs-12.col-md-8 > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

        
            # Onsite Field -
            # Onsite Comment -ref_url :  "https://www.bizcongo.com/appels-offres/marche-de-services/unhcr-19"
            
            external_url = page_details.find_element(By.CSS_SELECTOR, 'div.top-node-job_posting > div.info-instu-offre.col-xs-12.col-md-8 > a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bizcongo.com/appels-offres/attribution-de-march%C3%A9s"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
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
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
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
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    