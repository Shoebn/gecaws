from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_empulia_ca"
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
SCRIPT_NAME = "it_empulia_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'it_empulia_ca'
    
    notice_data.main_language = 'IT'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.procurement_method = 2
    
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 7
    
    # Onsite Field -Data pubblicazione
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "p.date").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#template_doc > tbody').get_attribute("outerHTML")                     
        except:
            pass

        try:
            notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'thead > tr > th').text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

        try:
            notice_data.related_tender_id = page_details.find_element(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(2) > td').text
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
        
        # Onsite Field - Data scadenza convenzione
        try:
            notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Data scadenza convenzione')]//following::td[1]").text
            notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        # Onsite Field -Convenzione N.
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Convenzione ')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        # Onsite Field -Oggetto
        try:
            notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Ogg')]//following::td[1]").text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Valore Convenzione
        try:
            est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Valore Convenzione ')]//following::td[1]").text
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
            notice_data.netbudgetlc = notice_data.est_amount
            notice_data.netbudgeteuro = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass

        # Onsite Field -Macro Convenzione
        try:
            notice_data.category = page_details.find_element(By.XPATH, "//*[contains(text(),'Macro Convenzione')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()
        # Onsite Field -Fornitore

            customer_details_data.org_name = "Empulia - InnovaPuglia SpA"

            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        # Onsite Field -Altro indirizzo web
        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Altro indirizzo web')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass
        
        try:
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
            
            lot_details_data.lot_title = notice_data.local_title
            lot_details_data.lot_title_english = notice_data.notice_title

            award_details_data = award_details()

            award_details_data.bidder_name = page_details.find_element(By.XPATH, '''//*[contains(text(),"Fornitore")]//following::td[1]''').text

            try:
                netawardvalue = page_details.find_element(By.XPATH, '//*[contains(text(),"Valore")]/.//following::td[1]').text
                netawardvaluelc = re.sub("[^\d\.\,]", "",netawardvalue)
                netawardvaluelc = netawardvaluelc.replace('.','').replace(',','.')
                award_details_data.netawardvalueeuro = float(netawardvaluelc)
                award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
            except Exception as e:
                logging.info("Exception in netawardvaluelc: {}".format(type(e).__name__))
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
                
            if lot_details_data.award_details != []:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
        try: 
            tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Data stipula convenzione")]//following::td[1]').text
            tender_contract_start_date = re.findall('\d+/\d+/\d{4}',tender_contract_start_date)[0]
            notice_data.tender_contract_start_date =  datetime.strptime(tender_contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass
        
        try: 
            tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Data scadenza convenzione")]//following::td[1]').text
            tender_contract_start_date = re.findall('\d+/\d+/\d{4}',tender_contract_end_date)[0]
            notice_data.tender_contract_end_date =  datetime.strptime(tender_contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ["http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Elenco%20Convenzioni.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.item.link-item')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.item.link-item')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
