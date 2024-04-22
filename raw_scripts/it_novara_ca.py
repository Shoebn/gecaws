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
SCRIPT_NAME = "it_novara_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_novara_ca'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7

# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


    # Onsite Field -Titolo :
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tipologia appalto :
    # Onsite Comment -

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CIG:
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione esito :
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Stato :
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Riferimento procedura :
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -add also this clicks in notice_text:1)click on "div.list-action > a.bkg.table" in tender_html_element."main > div > div" use this selector for notice_text. 2)click on "//*[contains(text(),'Lotti')]//following::a[1]" and "//*[contains(text(),'Altri atti e documenti')]" in page_details."main > div > div" use this selector for notice_text.
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"URL di Pubblicazione su www.serviziocontrattipubblici.it")]//following::td[17]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_codes_at_source = 'CPV'
    
    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
    # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get lot_cpv_details.

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            cpvs_data = cpvs()
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get cpv_details.

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.portgare-view >  div:nth-child(4)'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'COMUNE DI NOVARA'
            customer_details_data.org_parent_id = '1335742'
            customer_details_data.org_language = 'IT'
            customer_details_data.org_country = 'IT'
        # Onsite Field -Responsabile unico procedimento :
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[3]/div[2]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

        # Onsite Field -Tipo di Amministrazione
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element.

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione")]//following::td[4]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Comune Sede di Gara
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element.

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Comune Sede di Gara")]//following::td[6]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Indirizzo Sede di Gara
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element.

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Indirizzo Sede di Gara")]//following::td[7]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on "//*[contains(text(),'Lotti')]//following::a[1]" in page_details to take lot_details.
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            lot_details_data = lot_details()
        # Onsite Field -Titolo :
        # Onsite Comment -1.split after "CIG :".

            try:
                lot_details_data.lot_actual_number = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Titolo :
        # Onsite Comment -1.split after "Titolo :".

            try:
                lot_details_data.lot_title = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

        # Onsite Field -Importo a base di gara : 
        # Onsite Comment -1.split after "Importo a base di gara : ".

            try:
                lot_details_data.lot_grossbudget_lc = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Importo a base di gara : 
        # Onsite Comment -1.split after "Importo a base di gara : ".

            try:
                lot_details_data.lot_grossbudget = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tipologia appalto :
        # Onsite Comment -split after "Tipologia appalto :"

            try:
                lot_details_data.lot_contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tipologia appalto :
        # Onsite Comment -1)split after "Tipologia appalto :".	2)Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply','Altro = pass none')

            try:
                lot_details_data.contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))


        # Onsite Field -Data aggiudicazione :
        # Onsite Comment -None

            try:
                lot_details_data.lot_award_date = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in None.find_elements(By.None, 'None'):
                    award_details_data = award_details()
		
            # Onsite Field -Ditta aggiudicataria :
            # Onsite Comment -None

                    try:
                        award_details_data.bidder_name = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(4)').text
                    except Exception as e:
                        logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                        pass
			
            # Onsite Field -Importo a base di gara :
            # Onsite Comment -None

                    try:
                        award_details_data.initial_estimated_value = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(3)').text
                    except Exception as e:
                        logging.info("Exception in initial_estimated_value: {}".format(type(e).__name__))
                        pass
			
            # Onsite Field -Importo aggiudicazione :
            # Onsite Comment -None

                    try:
                        award_details_data.grossawardvaluelc = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(5)').text
                    except Exception as e:
                        logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                        pass

            # Onsite Field -Importo aggiudicazione :
            # Onsite Comment -None

                    try:
                        award_details_data.grossawardvalueeuro = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(5)').text
                    except Exception as e:
                        logging.info("Exception in grossawardvalueeuro: {}".format(type(e).__name__))
                        pass
			
            # Onsite Field -Data aggiudicazione :
            # Onsite Comment -None

                    try:
                        award_details_data.award_date = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(6)').text
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
    
# Onsite Field -None
# Onsite Comment -take attachments after clicking on "div:nth-child(8) > ul > li > a (Atti e documenti)" in page detils

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            attachments_data = attachments()
        # Onsite Field -Documentazione esito di gara
        # Onsite Comment -1.take in text format.

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione esito di gara
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li > a').get_attribute('href')


#click on "//*[contains(text(),'Altri atti e documenti')]" in page_details to get this attchments_details.          
        # Onsite Field -Documenti
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul > li').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documenti
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul > li > a').get_attribute('href')
        
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
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_esiti_lista.wp?_csrf=P9LAICEYB3R6UL2JAQRJTU67H4RZEU7E"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,15):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
            rows = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.list-item'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)