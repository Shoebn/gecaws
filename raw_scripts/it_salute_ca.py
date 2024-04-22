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
SCRIPT_NAME = "it_salute_ca"
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
    notice_data.script_name = 'it_salute_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "li> p.titolo").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Avvisi sui risultati della procedura di affidamento
    # Onsite Comment -take only local_title for ex."Avvisi sui risultati della procedura di affidamento - Procedura negoziata mediante R.d.O. aperta sul m.e.p.a. per l’affidamento dei servizi di produzione e stampa di materiale informativo ed editoriale" ,  here split only "Procedura negoziata mediante R.d.O. aperta sul m.e.p.a. per l’affidamento dei servizi di produzione e stampa di materiale informativo ed editoriale"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(2) > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CIG
    # Onsite Comment -split the notice_no for ex."CIG 9123706060" , here split only "9123706060"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'li > p:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -if notice_no is not available in "CIG" field , then pass the notice_no from url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(2) > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Avvisi sui risultati della procedura di affidamento
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        
    # Onsite Field -None
    # Onsite Comment -split the data between "importo" and "Iva" , for ex."importo € 79.930,00 (settantanovemilanovecentotrenta/00) Iva esclusa" , here split only "€ 79.930,00" , ref_url = "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2_1.jsp?lingua=italiano&id=2414"

    try:
        notice_data.netbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'div.portlet-content').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split the data between "importo" and "Iva" , for ex."importo € 79.930,00 (settantanovemilanovecentotrenta/00) Iva esclusa" , here split only "€ 79.930,00" , ref_url = "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2_1.jsp?lingua=italiano&id=2414"

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.CSS_SELECTOR, 'div.portlet-content').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split the data between "importo" and "Iva" , for ex."importo € 79.930,00 (settantanovemilanovecentotrenta/00) Iva esclusa" , here split only "€ 79.930,00" , ref_url = "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2_1.jsp?lingua=italiano&id=2414"

    try:
        notice_data.est_amount = page_details.find_element(By.CSS_SELECTOR, 'div.portlet-content').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass


    # Onsite Field -None
    # Onsite Comment -ref_url : "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2_1.jsp?lingua=italiano&id=2414"

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.portlet-content > p > a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass



    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'li > p:nth-child(2)'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -take last line as a org_name for ex."DG Comunicazione e Rapporti europei e internazionali"

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'li > p:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
# Onsite Field -Documentazione
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#documentazione'):
            attachments_data = attachments()
        # Onsite Field -Documentazione
        # Onsite Comment -split only file_name for ex."Elenco verbali Commissione di gara DGCOREI 2022 (PDF, 129.0 Kb)" , here split only "Elenco verbali Commissione di gara DGCOREI 2022" ,   ref_url : "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2_1.jsp?lingua=italiano&id=2443"

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Documentazione")]//following::p/a[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione
        # Onsite Comment -split only file_type , for ex."Elenco verbali Commissione di gara DGCOREI 2022 (PDF, 129.0 Kb)" , here split only "PDF" , ref_url : "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2_1.jsp?lingua=italiano&id=2443"

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Documentazione")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione
        # Onsite Comment -split only file_size , for ex."Elenco verbali Commissione di gara DGCOREI 2022 (PDF, 129.0 Kb)" , here split only "129.0 Kb" , ref_url : "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2_1.jsp?lingua=italiano&id=2443"

            try:
                attachments_data.file_size = page_details.find_element(By.XPATH, '//*[contains(text(),"Documentazione")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Documentazione")]//following::p/a[1]').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.portlet-content'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -take only as a text ,  take only local_title for ex."Avvisi sui risultati della procedura di affidamento - Procedura negoziata mediante R.d.O. aperta sul m.e.p.a. per l’affidamento dei servizi di produzione e stampa di materiale informativo ed editoriale" ,  here split only "Procedura negoziata mediante R.d.O. aperta sul m.e.p.a. per l’affidamento dei servizi di produzione e stampa di materiale informativo ed editoriale"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(2) > a').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'p:nth-child(2) > a'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -take only bidder_name for ex."Società aggiudicataria: Arti Grafiche Cardamone Srl , importo " , here split only "Arti Grafiche Cardamone Srl",   ref_url : "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2_1.jsp?lingua=italiano&id=2414"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div.portlet-content').text
			
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
    
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_2.jsp?lingua=italiano&tp=Avvisi+sui+risultati+della+procedura+di+affidamento&btnCerca="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'div.ricerca-documenti > ul > li'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, 'div.ricerca-documenti > ul > li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, 'div.ricerca-documenti > ul > li')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'div.ricerca-documenti > ul > li'),page_check))
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