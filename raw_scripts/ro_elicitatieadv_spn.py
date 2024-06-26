

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
SCRIPT_NAME = "ro_elicitatieadv_spn"
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
    notice_data.main_language = 'RO'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'RON'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RO'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div > h2 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Numar anunt
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(1) > strong').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data publicare
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(1) > span > strong").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data limita depunere oferta:
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(2) > span > strong").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    



    # Onsite Field -Descriere succinta
    # Onsite Comment -None
    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Descriere contract:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Descriere contract:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass


    # Onsite Field -Valoare
    # Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/adv-notices/view/100546383"

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Valoare estimata")]//following::div[1] ').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass


    # Onsite Field -Valoare
    # Onsite Comment -

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valoare estimata")]//following::div[1] ').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Tip contract:
    # Onsite Comment -"Lucrari=Works","Furnizare=Supply","Servicii=Service"

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(2) > strong').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tip contract:
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(2) > strong').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ---- "//*[@id="container-sizing"]/div[5]/div[2]/div"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#container-sizing > div:nth-child(3)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    

# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#container-sizing > div:nth-child(3)'):
            customer_details_data = customer_details()


        # Onsite Field -Tara
        # Onsite Comment -None

            try:
                customer_details_data.org_country = page_details.find_element(By.XPATH, '//*[contains(text(),"Tara")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'RO'
        # Onsite Field -Autoritate contractanta
        # Onsite Comment -take data which is after "Autoritate contractanta"

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, ' div:nth-child(2) > dic > strong').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Autoritate contractanta
        # Onsite Comment -take data which is after "Autoritate contractanta"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Punct")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

        # Onsite Field - adrese
        # Onsite Comment -
            
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresa")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-mail
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Tel")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax
        # Onsite Comment -

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Localitate
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Localitate:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        

        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#container-sizing > div:nth-child(3)'):
            custom_tags_data = custom_tags()
        # Onsite Field -CIF
        # Onsite Comment -None

            try:
                custom_tags_data.tender_custom_tag_company_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresa")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in tender_custom_tag_company_id: {}".format(type(e).__name__))
                pass
        
            custom_tags_data.custom_tags_cleanup()
            notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in custom_tags: {}".format(type(e).__name__)) 
        pass
    

# Onsite Field -None
# Onsite Comment - Cod CPV Principal

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#container-sizing > div:nth-child(3)'):
            cpvs_data = cpvs()
        # Onsite Field -None
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




# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#container-sizing > div:nth-child(3)'):
            attachments_data = attachments()
        # Onsite Field -Caiet de sarcini:
        # Onsite Comment -

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Caiet de sarcini:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Caiet de sarcini:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Caiet de sarcini:")]//following::span[1]').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.e-licitatie.ro/pub/adv-notices/list/1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,40):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[5]/div[2]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[5]/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[5]/div[2]/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="container-sizing"]/div[5]/div[2]/div'),page_check))
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
    