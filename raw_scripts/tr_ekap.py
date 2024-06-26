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
SCRIPT_NAME = "tr_ekap"
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
    notice_data.script_name = 'tr_ekap'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'tr'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'TRY'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -grab only numeric value , for ex. 2023/735464

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text> h6').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.card-text').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.card-text').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.card-text').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text > div > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_contract_type. eg., here "Hizmet - Açık İhale İlanı Yayımlanmış" take only "Hizmet" in notice_contract_type. 			2.replace following keword with given keywords("Hizmet=Service","Mal=Supply","Danışmanlık=Consultancy","Yapım=Works" )

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text > div').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split type_of_procedure_actual. eg., here "Hizmet - Açık İhale İlanı Yayımlanmış" take only "Açık" in type_of_procedure_actual.
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.card-text > div").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/tr_ekap_procedure",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text > div > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -İhale Onay Tarihi
    # Onsite Comment -click on  "Bilgiler" option for page_main and select  "İhale Bilgileri" tab for publish_date

    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),"İhale Onay Tarihi")]//following::td[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -split only date ,for ex: "HAKKARİ - 07.09.2023 10:00" , here take only "07.09.2023"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div p.alt.text-muted").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bilgiler
    # Onsite Comment -for page_main you have to click on "Bilgiler" option , you will be see the 4 tabs for tender information
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-5  li:nth-child(1)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#sonuclar > div > div'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-5  p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -split only city, for ex. "ANKARA - 20.09.2023 11:00", here split only "ANKARA"

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.alt.text-muted').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -İhale Yeri - Tarihi - Saati
        # Onsite Comment -click on " Bilgiler" tab for page_main after that, you will see "İhale Yeri - Tarihi - Saati" field,                 split only address, for ex. "Samsun 19 Mayıs Polis Meslek Yüksek Okulu Brifing Salonu - 04.10.2023 10:00", here split only "Samsun 19 Mayıs Polis Meslek Yüksek Okulu Brifing Salonu"

            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"İhale Yeri")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'Turkey'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    


# Onsite Field -Bilgiler
# Onsite Comment -when you click on "Bilgiler", main page will open , you can see "cpvs" in " İhale  Bilgileri"  section

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'li:nth-child(1) > button'):
            cpvs_data = cpvs()

        # Onsite Field -İhale Branş Kodları (OKAS)
        # Onsite Comment -split the data from page_main

            try:
                cpvs_data.cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"İhale Branş Kodları (OKAS)")]//following::td[1]').text
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
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div > p.card-text.ihaleAdi'):
            lot_details_data = lot_details()
            
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.card-text').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.card-text').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split notice_contract_type. eg., here "Hizmet - Açık İhale İlanı Yayımlanmış" take only "Hizmet" in notice_contract_type. 2.replace following keword with given keywords("Hizmet=Service","Mal=Supply","Danışmanlık=Consultancy","Yapım=Works" )

            try:
                lot_details_data.contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text > div').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass


        # Onsite Field -Bilgiler
        # Onsite Comment -when you click on "Bilgiler", main page will open , you can see "cpvs" in " İhale Bilgileri" section

            try:
                for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'li:nth-child(1) > button'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -İhale Branş Kodları (OKAS)
                    # Onsite Comment -split the data from page_main

                    lot_cpvs_data.lot_cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"İhale Branş Kodları (OKAS)")]//following::td[1]').text
			
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
    
# Onsite Field -Doküman
# Onsite Comment -click on " Doküman" for attachments,    Note: to grab the bid document Captch solving is required.. if possible add the condition for the Captcha..

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'li:nth-child(3)  span'):
            attachments_data = attachments()
        # Onsite Field -"Dokümanı Gör" , " Teknik Şartnamesiz İhale Dokümanı Gör"
        # Onsite Comment -grab only file_name For ex."Teknik Şartnamesiz İhale Dokümanı Gör ~ 100 KB"  and  "Dokümanı Gör ~2.6 MB",  here, grab only "Teknik Şartnamesiz İhale Dokümanı Gör" and "Dokümanı Gör"                  , there are 2 buttons are available for download document but, it is required to solve capcha for download the documents , if possible add the condition for the Captcha

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'div.card-footer  div> button').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -"Dokümanı Gör"  , " Teknik Şartnamesiz İhale Dokümanı Gör"
        # Onsite Comment -grab only file_size For ex."Teknik Şartnamesiz İhale Dokümanı Gör ~ 100 KB"  and  "Dokümanı Gör ~2.6 MB",  here, grab only "100 KB" and "2.6 MB"                  , there are 2 buttons are available for download document but, it is required to solve capcha, if possible add the condition for the Captcha

            try:
                attachments_data.file_size = page_main.find_element(By.CSS_SELECTOR, 'div.card-footer  div> button').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://ekap.kik.gov.tr/EKAP/Ortak/IhaleArama/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="sonuclar"]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="sonuclar"]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="sonuclar"]/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="sonuclar"]/div'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)