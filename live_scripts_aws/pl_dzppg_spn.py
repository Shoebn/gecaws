from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pl_dzppg_spn"
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
SCRIPT_NAME = "pl_dzppg_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'pl_dzppg_spn'

    notice_data.main_language = 'PL'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'PLN'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4


    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, '#main-content > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nazwa postępowania:
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nr postępowania:
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data ogłoszenia:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None
#     notice_data.notice_deadline = 'take as threshold'
    
    # Onsite Field -Rodzaj zamówienia:
    # Onsite Comment -Replace the following keywords with respective keywords(Usługi= Service , Dostawy= Supply, Roboty budowlane = Work)


    # Onsite Field -Rodzaj zamówienia:
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if 'Usługi' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Dostawy' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Roboty budowlane' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'          
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nazwa postępowania:
    # Onsite Comment -None

    


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'POLITECHNIKA GDAŃSKA'
    # Onsite Field -Kod jedn. prowadzącej:
    # Onsite Comment -and take the following address as static  "ul. G. Narutowicza 11/12 80-233 Gdańsk"

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_phone = '+48 58 347 25 87'
        customer_details_data.org_fax = '+48 58 347 28 21'
        customer_details_data.org_email = 'zam.publiczne.wftims@pg.edu.pl'
        customer_details_data.org_website = 'www.pg.edu.pl'
        customer_details_data.org_parent_id = '7780515'
        customer_details_data.org_language = 'PL'
        customer_details_data.org_country = 'PL'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on "Przeglądaj:" of each row to get diff documents (td:nth-child(2) > a)
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#main-content > table > tbody > tr')[1:]:
        
            attachment_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')
            fn.load_page(page_details1,attachment_url,80)
            time.sleep(5)
           
            for single_record1 in page_details1.find_elements(By.CSS_SELECTOR, '#main-content > table > tbody > tr')[2:]:
                attachments_data = attachments()
                attachments_data.file_name = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            # Onsite Field -Przeglądaj:
            # Onsite Comment -None
                
                attachments_data.external_url = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
    urls = ['https://dzp.pg.edu.pl/?sort=do&dir=DESC&start=0&perpage=200%27'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main-content"]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main-content"]/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main-content"]/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="main-content"]/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
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
    
