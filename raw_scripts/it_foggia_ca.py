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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_foggia_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_foggia_ca'
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'
    notice_data.notice_type = 7
    
    # Onsite Field -Titolo
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div div:nth-child(2)').text.split(':')[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        notice_data.notice_summary_english = notice_data.notice_title
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia appalto
    # Onsite Comment -None

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div div:nth-child(3)').text.split(':')[1].strip()
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione esito
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "form > div div:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Avvisi di aggiudicazione, esiti e affidamenti
    # Onsite Comment -None

    try:                                                                         
        notice_data.document_type_description = tender_html_element.find_element(By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/h2').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Riferimento procedura
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div div:nth-child(6)').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div div.list-action > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country ='IT'
        customer_details_data.org_language ='IT'
    # Onsite Field -Denominazione
    # Onsite Comment -None

        try:
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.first-detail-section > div:nth-child(2)').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

    # Onsite Field -Responsabile unico procedimento
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.first-detail-section > div:nth-child(3)').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -Lotti
# Onsite Comment -None

    try:
        lots_url = page_details.find_element(By.CSS_SELECTOR, 'div div:nth-child(7) > ul > li > a').get_attribute("href")
        fn.load_page(page_details1,lots_url,80)
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
    # Onsite Field -None
    # Onsite Comment -None

        try:
            lot_details_data.contract_type = notice_data.notice_contract_type
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            passs
            
        try:
            lot_grossbudget_lc = page_details1.find_element(By.CSS_SELECTOR, 'div.last-detail-section > div:nth-child(3)').text.split('Importo a base di gara :')[1].split('€')[0]
            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Titolo
    # Onsite Comment -None

        try:
            lot_details_data.lot_title = page_details1.find_element(By.CSS_SELECTOR, 'div.last-detail-section > div:nth-child(2)').text.split(':')[1].strip()
        except:
            lot_details_data.lot_title = notice_data.notice_title

    # Onsite Field -Titolo
    # Onsite Comment -None

        try:
            lot_details_data.lot_description = page_details1.find_element(By.CSS_SELECTOR, 'div.last-detail-section > div:nth-child(2)').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
    
        try:
            award_details_data = award_details()

            try:
                grossawardvaluelc = page_details1.find_element(By.CSS_SELECTOR, "div > div.last-detail-section > div:nth-child(5)").text.split('Importo aggiudicazione :')[1].split('€')[0].strip()
                grossawardvaluelc = re.sub("[^\d\.\,]", "",grossawardvaluelc)
                grossawardvaluelc = grossawardvaluelc.replace('.','').replace(',','.').strip()
                award_details_data.grossawardvaluelc = float(grossawardvaluelc)
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                pass

        # Onsite Field -Aggiudicatari
        # Onsite Comment -None

            try:                                                                              
                award_details_data.bidder_name = page_details1.find_element(By.CSS_SELECTOR, "div > div.last-detail-section > div:nth-child(4)").text.split('Ditta aggiudicataria :')[1].strip()
            except Exception as e:
                logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                pass

            try:
                award_date = page_details1.find_element(By.CSS_SELECTOR, 'div.last-detail-section > div:nth-child(6)').text.split(':')[1]
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass

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

    try:
        grossbudgetlc = page_details1.find_element(By.CSS_SELECTOR, 'div.last-detail-section > div:nth-child(3)').text.split('Importo a base di gara :')[1].split('€')[0]
        grossbudgetlc = re.sub("[^\d\.\,]", "",grossbudgetlc)
        grossbudgetlc = grossbudgetlc.replace('.','').replace(',','.').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:
        attachments_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Atti e documenti')]").get_attribute("href")                     
        fn.load_page(page_details2,attachments_url,80)

        for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'div.detail-section > div > ul > li'):

            try:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                if 'javascript' in external_url:

                    javascript_url = single_record.find_element(By.CSS_SELECTOR,'ul > li> form').get_attribute("action")
                    fn.load_page(page_details3,javascript_url,80)

                    for java_doc in page_details3.find_elements(By.CSS_SELECTOR, 'ul.list'):
                        attachments_data = attachments()
                        attachments_data.file_name = java_doc.find_element(By.CSS_SELECTOR,'li a').text
                        attachments_data.external_url = java_doc.find_element(By.CSS_SELECTOR,' li a').get_attribute('href')
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
                else:
                    attachments_data = attachments()
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass

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
page_details = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments) 
page_details2 = fn.init_chrome_driver(arguments)
page_details3 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://appalti.provincia.foggia.it/PortaleAppalti/it/ppgare_esiti_lista.wp?_csrf=A2VE5KOAE2BMEG5YYPQQG87JBKNYLO7Z'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div')))
            length = len(rows)
            for records in range(2,length-1):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="pagination-navi"]/input[8]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div'),page_check))
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
    page_details1.quit() 
    page_details2.quit()
    page_details3.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
