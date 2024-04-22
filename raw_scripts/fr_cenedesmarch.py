#refer this page detail url for fields "https://centraledesmarches.com/marches-publics/Douai-cedex-Commune-de-Douai-Accords-cadres-de-maintenance-d-espaces-verts/6838902"

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
SCRIPT_NAME = "fr_cenedesmarch"
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
    notice_data.script_name = 'fr_cenedesmarch'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'FR'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.entete').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split data from 'Type de procédure' till 'Conditions de participation'
    # Onsite Comment -ref url "https://centraledesmarches.com/marches-publics/In-Li-Revalorisation-et-renovation-thermique-en-milieu-occupe-d-une-residence-de-60-logements-a-Charenton-le-Pont-94/7794771"

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, '#details').text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date de publication : split data fromDate de publication 'Date de publication'  till   'Publié dans'
    # Onsite Comment -skip first 5-6 records and then take publication date of remaining data

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.infos > div.infoslegales").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    # Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
    # Onsite Comment -split data from " Type de marché" till " Description succincte"

    try:
        notice_data.notice_contract_type = page_details.find_element(By.CSS_SELECTOR, '#content > div.wrapper').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.infos > div.dates").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass


    # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text()," Description succincte")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
    # Onsite Comment -take following  data from the selector

    try:
        notice_data.dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"IV.3) Date d'envoi du présent avis")]').text
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass


    # Onsite Field -take following data
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur totale du marché (hors TVA)")]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -take following data
    # Onsite Comment -None

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur totale du marché (hors TVA)")]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Voir le détail
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.infos > div.liens > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Voir le détail
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content > div.wrapper').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -ref url "https://centraledesmarches.com/marches-publics/In-Li-Revalorisation-et-renovation-thermique-en-milieu-occupe-d-une-residence-de-60-logements-a-Charenton-le-Pont-94/7794771"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div.wrapper'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.infos > div.maitreouvrage').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ref url " https://centraledesmarches.com/marches-publics/In-Li-Revalorisation-et-renovation-thermique-en-milieu-occupe-d-une-residence-de-60-logements-a-Charenton-le-Pont-94/7794771"
        # Onsite Comment -spit data from "Code Postal : " to "Groupement de commandes"

            try:
                customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, '#details').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ref url "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
        # Onsite Comment -spit data from "Nom et adresses: " to "Tél  "

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#details').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -just take NUTS from following data

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Code NUTS")]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass


        # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
        # Onsite Comment -take following  data from the selector... split data from 'Tél' to 'courriel'

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Nom et adresses")][1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
        # Onsite Comment -take following  data from the selector... split data from 'courriel' to  'adresse'

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Nom et adresses")][1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ref url "https://centraledesmarches.com/marches-publics/In-Li-Revalorisation-et-renovation-thermique-en-milieu-occupe-d-une-residence-de-60-logements-a-Charenton-le-Pont-94/7794771"
        # Onsite Comment -spit data from "Ville: " to "Code Postal "

            try:
                customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, '#details').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'FR'
            customer_details_data.org_country = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    
# Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div.wrapper'):
            lot_details_data = lot_details()
        # Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
        # Onsite Comment -split data from " Type de marché" till " Description succincte"

            try:
                lot_details_data.contract_type = page_details.find_element(By.CSS_SELECTOR, '#content > div.wrapper').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Lot nº")][1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -just take lot title

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Intitulé")]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -just take lot description

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"DESCRIPTION")]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -just take lot amount take following data

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Informations sur le montant du marché/du lot")]').text
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -just take NUTS from following data

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Code NUTS")]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div.wrapper'):
            cpvs_data = cpvs()
        # Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
        # Onsite Comment -split data from "Code(s) CPV additionnel"   to " Lieu d'exécution"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, '#content > div.wrapper').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#details'):
            tender_criteria_data = tender_criteria()
        # Onsite Field - 
        # Onsite Comment -take title from 'Critère de qualité' 

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, '//*[contains(text(),"Critères d'attribution")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field - 
        # Onsite Comment -take weight from 'Critère de qualité'
            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, '#details').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass

        # Onsite Field -
        # Onsite Comment -take titel from "Prix" 


            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, '//*[contains(text(),"Critères d'attribution")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -
        # Onsite Comment - take weight from "Prix" 

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, '#details').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text()," Description succincte")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
# Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#details'):
            funding_agencies_data = funding_agencies()

        # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/Douai-cedex-Commune-de-Douai-Accords-cadres-de-maintenance-d-espaces-verts/6838902"
        # Onsite Comment -None

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"européenne")][1]').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
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
    urls = ['https://centraledesmarches.com/marches-publics/liste-avancee'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/div[3]/div/div[2]/section'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[3]/div/div[2]/section')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[3]/div/div[2]/section')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[4]/div[3]/div/div[2]/section'),page_check))
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
    