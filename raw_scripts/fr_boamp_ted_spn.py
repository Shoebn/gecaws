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
SCRIPT_NAME = "fr_boamp_ted_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'fr_boamp_ted_spn'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' p > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
        notice_data.notice_url = url
    logging.info(notice_data.notice_url)
    
    try:
        clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.fr-btn.fr-my-1w.ng-binding'))).click()
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="toplist"]/div/div/div').get_attribute("outerHTML") 
        notice_text = page_details.find_element(By.XPATH, '//*[@id="toplist"]/div/div/div').text
    except:
        pass
    
    try:
        notice_data.document_type_description=fn.get_string_between(notice_text,"Type d'avis : ",'Procédure : ')
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'label.fr-my-0.fr-text--lg.fr-text--regular.ng-binding').text        
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass   

    try:
        notice_data.local_title = page_details.find_element(By.XPATH,"//*[contains(text(),'Objet du marché :')]//following::span[1]").text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data = customer_details()
        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH,"//*[contains(text(),'Nom et adresse officiels de ')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass       
        
        try:
            if 'Téléphone :' in notice_text:
                customer_details_data.org_address = fn.get_string_between(notice_text,'Adresse :','Téléphone :')
            else:
                customer_details_data.org_address = fn.get_string_between(notice_text,'Adresse :','Courriel :')

        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass            
        
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH,"//*[contains(text(),'Courriel ')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass 
        try:
            customer_details_data.customer_nuts = fn.get_string_between(notice_text,"Lieu d'exécution","Lieu principal d'exécution :").split(':')[1]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass 

        
        customer_details_data.org_country = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procédure : ")]//following::span[1]').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_spn_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    
    try:
        deadline_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Date limite de réception des offres :')]//following::span[1]").text
        deadline_date = GoogleTranslator(source='auto', target='en').translate(deadline_date)
        deadline_date = re.findall('\d+/\d+/\d{4}',deadline_date)[0]
        notice_data.notice_deadline = datetime.strptime(deadline_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S') 
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    
    try:
        notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Type de marché')]//following::td[3]").get_attribute('innerHTML')
        if 'Fournitures' in notice_contract_type:
            notice_data.notice_contract_type="Supply"
        if 'Services' in notice_contract_type:
            notice_data.notice_contract_type="Service"
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
   
    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"ENVOI DU PRÉSENT AVIS")]//following::tr/td[3]').get_attribute('innerHTML').replace('&nbsp;',' ')
        dispatch_date = GoogleTranslator(source='fr', target='en').translate(dispatch_date)
        dispatch_date = re.findall('\w+ \d+, \d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass   
  
    try:
        cpvs_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Code CPV ')]//following::tr[1]").text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
            
    try:
        grossbudgetlc=page_details.find_element(By.XPATH, "//*[contains(text(),'Valeur totale estimée : ')]//following::tr[1]").text.split(':')[1]
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace(' ','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    try:
        notice_data.est_amount=notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass    
    
    try:
        contract_duration=page_details.find_element(By.XPATH, "//*[contains(text(),'Durée du marché')]//following::tr[1]").text
        notice_data.contract_duration = GoogleTranslator(source='auto', target='en').translate(contract_duration)
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass   

    try: 
        lot_number = 1
        for lot in page_details.find_elements(By.XPATH, '//*[contains(text(),"Section II : Objet")]//following::table'):
            lot = lot.text
            if "Description des prestations : " in lot:

                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                try:
                    lot_description = lot.split('Description des prestations : ')[1].split('\n')[0].strip()
                    lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)

                except Exception as e:
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass 

                try:
                    lot_title=notice_text.split('Renseignements relatifs aux lots :')[1].split(':')[1].split('/n')[0].strip()
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                except Exception as e:
                    lot_details_data.lot_title=notice_data.notice_title
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass   

                try:
                     lot_details_data.contract_number=fn.get_string_between(notice_text,'Référence de TED : ','- annonce')
                except Exception as e:
                    logging.info("Exception in contract_number: {}".format(type(e).__name__))
                    pass    

                try:
                    lot_grossbudget_lc = lot.split('Valeur hors TVA :')[1].split('euros')[0].replace(' ','').replace(',','.').strip()
                    lot_details_data.lot_grossbudget_lc=float(lot_grossbudget_lc)
                except Exception as e:
                    lot_details_data.lot_grossbudget_lc=notice_data.grossbudgetlc
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass    

                try:
                    lot_details_data.lot_nuts = fn.get_string_between(notice_text,"Lieu d'exécution","Lieu principal d'exécution :").split(':')[1]
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass 

                lot_cpvs_data = lot_cpvs()
                try:
                    lot_cpvs_data.lot_cpv_code = notice_text.split('Code CPV principal : ')[1].split('\n')[0].strip()
                except Exception as e:
                    lot_cpvs_data.lot_cpv_code =  notice_data.cpvs
                    logging.info("Exception in lot_cpv_code: {}".format(type(e).__name__))
                    pass 
   

                if lot_cpvs_data.lot_cpv_code != "":
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)

                try:
                    lot_criteria_title = notice_text.split("Critères d'attribution")[1].split("II.2.6) Valeur estimée")[0].strip()
                    for l in lot_criteria_title.split('\n'):
                        if 'Pondération' in l:
                            lot_criteria_data = lot_criteria()
                            lot_criteria_title = l.split('/ Pondération')[0].strip()
                            lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                            lot_criteria_data.lot_criteria_weight = int(l.split('/ Pondération :')[1].strip())
                            if 'Prix' in l:
                                lot_criteria_data.lot_is_price_related = True
                            else:
                                lot_criteria_data.lot_is_price_related = False

                            lot_criteria_data.lot_criteria_cleanup()
                            lot_details_data.lot_criteria.append(lot_criteria_data) 
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass

                
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass


    try:
        funding_agency = fn.get_string_between(notice_text,"Information sur les fonds de l'Union européenne","Identification du projet")
        if ' non' in funding_agency:
            pass
        else:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency=1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&refine.type_avis=5&refine.type_avis=1&refine.type_avis=2&refine.type_avis=3&refine.type_avis=4&refine.famille=JOUE&q.filtre_etat=(NOT%20%23null(datelimitereponse)%20AND%20datelimitereponse%3E%3D%222023-06-22%22)%20OR%20(%23null(datelimitereponse)%20AND%20datefindiffusion%3E%3D%222023-06-22%22)"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.card-notification.fr-callout.fr-py-4w.fr-px-3w.fr-px-md-6w.fr-mb-4w.ng-scope'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card-notification.fr-callout.fr-py-4w.fr-px-3w.fr-px-md-6w.fr-mb-4w.ng-scope')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card-notification.fr-callout.fr-py-4w.fr-px-3w.fr-px-md-6w.fr-mb-4w.ng-scope')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.card-notification.fr-callout.fr-py-4w.fr-px-3w.fr-px-md-6w.fr-mb-4w.ng-scope'),page_check))
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
