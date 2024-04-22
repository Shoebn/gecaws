from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_bund_ca"
log_config.log(SCRIPT_NAME)
import jsons
from datetime import date, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_bund_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_bund_ca'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.main_language = 'DE'
   
    notice_data.currency = 'EUR'
   
    notice_data.procurement_method = 2
  
    notice_data.notice_type = 7
  
    notice_data.document_type_description = 'Vergebene Aufträge: evergabe-online.de'
    
    # Onsite Field -Auftragsgegenstand
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -Zeitraum
    # Onsite Comment -take only first date as publish date

    notice_data.publish_date = threshold    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Auftragsgegenstand / Art und Umfang der Leistung
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, "//*[contains(text(),'Auftragsgegenstand / Art und Umfang der Leistung')]//following::p[1]").text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Auftraggeber
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        # Onsite Field -Auftraggeber
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.result-list > li> a > div:nth-child(2)').text
        
        # Onsite Field -Auftraggeber
        # Onsite Comment -None

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.result-list > li> a > div:nth-child(2) > p').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        # Onsite Field -Telefon:
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Telefon:')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        # Onsite Field -Fax:
        # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, "//*[contains(text(),'Fax:')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
   
        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'span > a').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        # Onsite Field -Auftragsgegenstand
        # Onsite Comment -None
        try:
            award_details_data = award_details()
            # Onsite Field -Beauftragtes Unternehmen
            # Onsite Comment -None
            bidder_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Beauftragtes Unternehmen')]//following::p[1]").text
            if bidder_name!="":
                if "Firma" in bidder_name:
                    award_details_data.bidder_name =bidder_name.split("Firma:")[1].strip()
                else:
                    award_details_data.bidder_name=bidder_name

            # Onsite Field -Zeitraum
            # Onsite Comment -take only second date as award date

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
    urls = ['https://www.service.bund.de/Content/DE/Ausschreibungen/Suche/Formular.html?nn=4641482&ambit_distance=10&input_=4641482&solr_opengeo_id.HASH=e4c88mmUvUFPfSuWzcwh3sMpD84XqFQ%3D&type=2&submit=Finden&resourceId=4641464&pageLocale=de'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,3):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div/section[2]/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div/section[2]/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div/section[2]/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="main"]/div/div/section[2]/div[2]/div/form/fieldset/div/div[1]/ul/li[2]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="main"]/div/div/section[2]/ul/li'),page_check))
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
    
