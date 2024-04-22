from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_bund_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_bund_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_bund_spn'
    
    notice_data.main_language = 'DE'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -if  "Ausschreibungsweite = EU tender " than procurement method will be "1" and if  "Ausschreibungsweite = nationale ausschreibung " than procurement method will be "0"                                                          (selector for field "Ausschreibungsweite = EU tender " :- //*[contains(text(),'Ausschreibungsweite')]//following::dd[1] )

    notice_data.procurement_method = 0   
    
    notice_data.notice_type = 4   

   
    # Onsite Field -Veröffentlicht
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2)").text
        publish_date = re.findall('\d+.\d+.\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    # Onsite Field -Angebotsfrist
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3)").text
        notice_deadline = re.findall('\d+.\d+.\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.result-list > li> a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
            
 
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
  
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, '#main > div > div > section > h1').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, '#main > div > div > section > h1').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
            
    # Onsite Field -Vergabeart
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Vergabeart')]//following::dd[1]").text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_bund.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
                   
    
    # Onsite Field -Weitere Informationen
    # Onsite Comment -take additional_tender_url from "Weitere Informationen" only if available eg: 'html page' or 'more information'

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.linklist > ul > li > a').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
 
    try:              
        customer_details_data = customer_details()
                
        # Onsite Field -Vergabestelle:
        # Onsite Comment -None

        org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Vergabestelle')]").text.split('Vergabestelle: ')[1]
        if org_name !='':
            customer_details_data.org_name = org_name
        else:
            return  
        # Onsite Field -Erfüllungsort
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Erfüllungsort')]//following::dd[1]").text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        # Onsite Field -CPV-Code
        # Onsite Comment -if cpv is available in detail pg then take numeric value before -1 and if the cpv is not available in detail pg then take auto cpv
        cpvs_code = page_details.find_element(By.XPATH, "//*[contains(text(),'CPV-Code')]//following::dd[1]").text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
        
           
# Onsite Field -Weitere Informationen
# Onsite Comment -take attachment info from "Weitere Informationen" only

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section > div.linklist'):
            attachments_data = attachments()

        # Onsite Field -Weitere Informationen
        # Onsite Comment -take attachment info from "Weitere Informationen" only and split file_type if available

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'div.linklist > ul > li').text.split('(')[1].split('-')[0]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Weitere Informationen
        # Onsite Comment -take attachment info from "Weitere Informationen" only and split file_name

            attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.linklist > ul > li').text            
        # Onsite Field -Weitere Informationen
        # Onsite Comment -take attachment info from "Weitere Informationen" only and split file_size if available

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'div.linklist > ul > li').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Weitere Informationen
        # Onsite Comment -take attachment info from "Weitere Informationen" only
            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.linklist > ul > li> a').get_attribute('href')
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
    urls = ['http://www.service.bund.de/Content/DE/Ausschreibungen/Suche/Formular.html?view=processForm&nn=4642046'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            clk= WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="main"]/div/div/section[1]/form/fieldset/div[3]/div[3]/input')))
            page_main.execute_script("arguments[0].click();",clk)
        except:
            pass
        try:
            for page_no in range(1,100):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main"]/div/div/section[2]/ul[2]/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div/section[2]/ul[2]/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div/section[2]/ul[2]/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="main"]/div/div/section[2]/div[2]/div/form/fieldset/div/div[1]/ul/li[2]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="main"]/div/div/section[2]/ul[2]'),page_check))
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
    
