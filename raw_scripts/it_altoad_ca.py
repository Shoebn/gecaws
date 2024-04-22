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
SCRIPT_NAME = "it_altoad_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_altoad_ca'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
        
    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -Split title from "Oggetto"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > span.organizationUnit').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo aggiudicato
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td.awardedAmount').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split "CIG" number from "oggetto"
    # Onsite Comment -None

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject').text
        if 'CIG:' in notice_no:
            notice_data.notice_no = notice_no.split('CIG:')[1].split(')')[0].strip()
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
   
    
    # Onsite Field -split "Procedura negoziata senza previa pubblicazione, Affidamento diretto" such type from "oggetto"
    # Onsite Comment -None

    try:                                                                                          
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'span.process-type').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data di pubblicazione esito
    # Onsite Comment -None

    try:                                                                   
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.publishedAt").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    if notice_data.publish_date is None:
        return
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject >a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url

    try:
        notice_contract_type = page_details.find_element(By.XPATH,"//*[contains(text(),'Tipo di appalto:')]//following::dd[1]").text
        if 'Servizi' in notice_contract_type or 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'pubblici' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
       
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="Contenuto"]').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -split "buyer" from "Oggetto"
        customer_details_data.org_country = 'IT'
        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -just select " Organo competente per le procedure di ricorso:" for org address

        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, '#Contenuto').text
            if 'Organo competente per le procedure di ricorso:' in org_address:
                customer_details_data.org_address = org_address.split('Organo competente per le procedure di ricorso:')[1].split('Telefono:')[0]
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
               
        # Onsite Field -None
        # Onsite Comment -just select " Organo competente per le procedure di ricorso:" for "org phone"

        try:
            org_phone = page_details.find_element(By.CSS_SELECTOR, '#Contenuto').text
            if 'Telefono:' in org_phone:
                customer_details_data.org_phone = org_phone.split('Telefono:')[1]
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Responsabile unico del Procedimento: ')]//following::dd[1]").text.strip()    
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
# # Onsite Field -None
# # Onsite Comment -None

    try:
        lot_details_data = lot_details()
      # Onsite Field -None
      # Onsite Comment -take same as "local title"

        lot_details_data.lot_title = notice_data.notice_title
        lot_details_data.lot_number = 1
        lot_details_data.contract_type = notice_data.notice_contract_type
        # Onsite Field -None
        # Onsite Comment -None

        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#list-contractors'):
                award_details_data = award_details()

                # Onsite Field -None
                # Onsite Comment -None

                try:
                    award_details_data.address = single_record.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3) > ul > li ').text
                except Exception as e:
                    logging.info("Exception in address: {}".format(type(e).__name__))
                    pass

                # Onsite Field -None
                # Onsite Comment -None

                try:
                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > ul > li > span.name').text
                except Exception as e:
                    logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Importo aggiudicazione
                # Onsite Comment -None

                try:
                    award_details_data.initial_estimated_value = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split('(')[0]
                except Exception as e:
                    logging.info("Exception in initial_estimated_value: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Data aggiudicazione
                # Onsite Comment -None

                try:
                    award_date = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
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

    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="Contenuto"]'):
            cpvs_data = cpvs()
            # Onsite Field -Codice CPV
            # Onsite Comment -split " Codice CPV" from the path
            cpvs_data.cpv_code = single_record.find_element(By.CSS_SELECTOR,'div > b').text.split('-')[0].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo a base di gara (comprensivo di costi di sicurezza e ulteriori componenti non ribassabili):")]//following::dd[1]').text.split('€')[1]
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass

      # Onsite Field -Data Inizio
    # Onsite Comment -None

    try:
        notice_data.document_purchase_start_time = page_details.find_element(By.XPATH, '//*[contains(text(),'Data Inizio')]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data ultimazione
    # Onsite Comment -None

    try:
        notice_data.document_purchase_end_time = page_details.find_element(By.XPATH, '//*[contains(text(),'Data Inizio')]//following::dd[2]').text
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
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
page_main = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.bandi-altoadige.it/awards/list-public/page/1'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,6):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[3]/div[2]/form[2]/div[2]/table/tbody'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[3]/div[2]/form[2]/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[3]/div[2]/form[2]/div[2]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[3]/div[2]/form[2]/div[2]/table/tbody/tr'),page_check))
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
    
