from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_coordination_spn"
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_coordination_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
# after opening the url fields in front of "Date limite de remise des plis" such as "Entre le" and "et le" shuold be blank. and in the fields in front of "Date de mise en ligne" such as "Entre le" and "et le" select date.
    
    notice_data.script_name = 'fr_coordination_spn'
   
    notice_data.main_language = 'FR'

    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    
    try:#Clôture le 29/02/2024
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, ' div.extra-header').text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div.entry-content-wrapper.clearfix.standard-content > header > h3 ').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.entry-content-wrapper.clearfix.standard-content > header > span.author').text
    except:
        pass
    
    try:
        performance = tender_html_element.find_element(By.CSS_SELECTOR, ' div.entry-content-wrapper.clearfix.standard-content > ul > li:nth-child(1)').text.split('Pays :')[1].strip()
        country = performance.split(',')
        for countries in country:
            country_title = GoogleTranslator(source='auto', target='en').translate(countries)
            performance_country_data = performance_country()
            performance_country_data.performance_country = fn.procedure_mapping("assets/fr_coordination_spn_countrycode.csv",country_title.strip())
            if performance_country_data.performance_country == None:
                performance_country_data.performance_country = 'FR'
            notice_data.performance_country.append(performance_country_data)
    except:
        try:
            performance_country_data = performance_country()
            performance_country_data.performance_country = 'FR'
            notice_data.performance_country.append(performance_country_data)
        except Exception as e:
            logging.info("Exception in performance_country: {}".format(type(e).__name__))
            pass
        
    try:
        notice_data.class_title_at_source = tender_html_element.find_element(By.CSS_SELECTOR, ' div.entry-content-wrapper.clearfix.standard-content > ul > li:nth-child(2)').text.split('Compétences :')[1].strip()
    except:
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'div.entry-content-wrapper.clearfix.standard-content > ul > li:nth-child(2)').text.split('Compétences :')[1].strip()
        category_title = GoogleTranslator(source='auto', target='en').translate(notice_data.category)
        category_name = category_title.split(',')
        for data in category_name:
            category = data.strip().lower()
            cpv_codes_list = fn.CPV_mapping("assets/fr_coordination_spn.csv",category)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = each_cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
   
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.entry-content-wrapper.clearfix.standard-content > header > h3 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div.container_wrap.container_wrap_first.main_color.fullsize > div > main > article').get_attribute("outerHTML")                     
    except:
        pass
    
    try:#Le 19/02/2024  
        publish_date = page_details.find_element(By.CSS_SELECTOR, "section:nth-child(3) > div > div > section > div > span.date-publication").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"À télécharger")]//following::div[1]/article/div/header/h3/a'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text
            
            attachments_data.external_url = single_record.get_attribute('href')
        
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_number=1
        single_record = page_details.find_element(By.XPATH, '//*[@id="main"]/div[1]/div/main/article/div[1]/div[2]/section/div').text
        lot_data = single_record.split('Lot N°')
        for data in lot_data[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number= lot_number
            
            try:
                lot_details_data.lot_actual_number = 'Lot N°'+str(lot_number)
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pas
            
            if ":"in data:
                lot_details_data.lot_title = data.split(":")[1].split('\n')[0].strip()
                lot_details_data.lot_title_english =GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            else:
                no = str(lot_number)
                lot_details_data.lot_title = data.split(no)[1].strip()
                lot_details_data.lot_title_english =GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'

        customer_details_data.org_name = org_name
        
        try:
            org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Contact")])[2]//following::a[1]').text
            email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
            customer_details_data.org_email = email_regex.findall(org_email)[0]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            org_email = page_details.find_element(By.XPATH, '//*[@id="main"]/div[1]/div/main/article/div[1]/div[2]/section/div').text
            if 'La proposition est à adresser à l’adresse électronique suivante :' in org_email:
                org_email = org_email.split('La proposition est à adresser à l’adresse électronique suivante :')[1].split('\n')[0].strip()
    
            elif 'Le dossier complet sera envoyé par chaque candidat.e aux deux adresses électroniques suivantes :' in org_email:
                org_email = org_email.split('Le dossier complet sera envoyé par chaque candidat.e aux deux adresses électroniques suivantes :')[1].split('\n')[0].strip() 
        
            elif 'For international tenderers: tenders can be received through electronic mail (e-mail):' in org_email:
                org_email = org_email.split('For international tenderers: tenders can be received through electronic mail (e-mail):')[1].split('\n')[0].strip() 
            
            elif 'Les candidats intéressés doivent soumettre leur candidature à' in org_email:
                org_email = org_email.split('Les candidats intéressés doivent soumettre leur candidature à')[1].split('\n')[0].strip() 
            
            elif 'Please share your application by email :' in org_email:
                org_email = org_email.split('Please share your application by email :')[1].split('\n')[0].strip()
            
            elif 'Les propositions sont à rédiger en anglais et à adresser par mail à l’adresse suivante' in org_email:
                org_email = org_email.split('Les propositions sont à rédiger en anglais et à adresser par mail à l’adresse suivante')[1].split('\n')[0].strip()
                
            email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
            customer_details_data.org_email = email_regex.findall(org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Site internet")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main =  fn.init_chrome_driver(arguments)
page_details =  fn.init_chrome_driver(arguments)
action = ActionChains(page_main)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.coordinationsud.org/appels-doffres/?_sort=1_date_desc"]
    
    for url in urls:
        fn.load_page(page_main, url, 90)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'section > div > div > section:nth-child(6) > div > div.facetwp-template > div > div > div > article'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' section > div > div > section:nth-child(6) > div > div.facetwp-template > div > div > div > article')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' section > div > div > section:nth-child(6) > div > div.facetwp-template > div > div > div > article')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'section:nth-child(6) > div > div:nth-child(10) > div > a.facetwp-page.next')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,' section > div > div > section:nth-child(6) > div > div.facetwp-template > div > div > div > article'),page_check))
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
