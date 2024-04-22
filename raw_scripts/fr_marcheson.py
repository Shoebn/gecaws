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
SCRIPT_NAME = "fr_marcheson"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -the following formats have been identified ------------- Format 1 :  https://www.marchesonline.com/appels-offres/avis/marche-de-desherbage-thermique-des-voiries-communales/ao-9084146-1
# Format 2 :  https://www.marchesonline.com/appels-offres/avis/missions-de-controle-technique-et-coordination-sps-pou/ao-9084145-1

# Format 3 :  https://www.marchesonline.com/appels-offres/avis/fourniture-de-colis-de-noel-pour-les-aines/ao-9084131-1

# Format 4 : https://www.marchesonline.com/appels-offres/avis/amo-pour-la-preparation-des-marches-de-fournitures-de/ao-9084139-1

# Format 5 : https://www.marchesonline.com/appels-offres/avis/travaux-de-rehabilitation-plan-climat-et-d-ameliorati/ao-9082791-1

# Format 6 :https://www.marchesonline.com/appels-offres/avis/travaux-d-assainissement-et-d-amenagement-de-voirie-ru/ao-9084118-1

# Format 7 : https://www.marchesonline.com/appels-offres/avis/veille-juridique-echanges-d-experiences-mise-a-dis/ao-9082918-1
    notice_data.script_name = 'fr_marcheson'
    
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
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Avis N° :
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.noticeNumber > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Mise en ligne :
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "li.onlineDate").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Limite de réponse :
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "li.answerDate > span.dateColor").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Replace following keywords with given respective keywords ("Services = Services","Travaux de bâtiment = work","Etudes, Maîtrise d'oeuvre, Contrôle = Services","Fournitures = supply" ,"Travaux Publics = work")

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.activity').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.activity').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass 
        
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "ul.colOne > li.process").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcheson_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'section.blockNotice > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div.colOne').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.identityNotice > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
 
 #----------------------------------------------------------------------------------------------------------------
    # Onsite Field -None
    # Onsite Comment -Format 1 : "https://www.marchesonline.com/appels-offres/avis/marche-de-desherbage-thermique-des-voiries-communales/ao-9084146-1"


 
    # Onsite Field -Description :
    # Onsite Comment -Format 1 : "https://www.marchesonline.com/appels-offres/avis/marche-de-desherbage-thermique-des-voiries-communales/ao-9084146-1"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durée :
    # Onsite Comment -Split data from "Durée "till "Description "

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée :")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Envoi à la publication le :
    # Onsite Comment -None

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Envoi à la publication le :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
        # Onsite Field -Client  :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.location').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tél. :
        # Onsite Comment -Split data from "Tél" till "mèl "

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -mèl :
        # Onsite Comment -Split data from "mèl "till "web"

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -web :
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1 > a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
  



 #----------------------------------------------------------------------------------------------------------------
    # Onsite Field -None
    # Onsite Comment -Format 2 :  "https://www.marchesonline.com/appels-offres/avis/missions-de-controle-technique-et-coordination-sps-pou/ao-9084145-1"    
    
    
    
  
    # Onsite Field -Nom du contact :
    # Onsite Comment -Format 2 :  "https://www.marchesonline.com/appels-offres/avis/missions-de-controle-technique-et-coordination-sps-pou/ao-9084145-1"      ----------------------------- split data from "Nom du contact" till "Section" (just take url)

        # Onsite Field -None
    # Onsite Comment -None
    notice_data.cpv_at_source = 'CPV'
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durée du marché
    # Onsite Comment -split data and take only 'Durée du marché '

    try:
        notice_data.contract_duration = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
        # Onsite Field -Client  :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.location').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Code Postal
        # Onsite Comment -Split data from "Code Postal" till "Groupement de commandes"

            try:
                customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Descripteur principal :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            cpvs_data = cpvs()
        # Onsite Field -Descripteur principal :
        # Onsite Comment -split data after "Descripteur principal : " till "Type de marché : "

            try:
                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuDeLAvis'):
            lot_details_data = lot_details()
        # Onsite Field -Description du lot :
        # Onsite Comment -split data after "Description du lot :" just take number

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.contenuDeLAvis').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description du lot :
        # Onsite Comment -split data after "Description du lot :" till "Code(s) CPV additionnel(s)"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.contenuDeLAvis').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
        # Onsite Field -Estimation de la valeur hors taxes du lot :
        # Onsite Comment -split data after "Estimation de la valeur hors taxes du lot :"

            try:
                lot_details_data.lot_grossbudget = page_details.find_element(By.CSS_SELECTOR, 'div.contenuDeLAvis').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Estimation de la valeur hors taxes du lot :
        # Onsite Comment -split data after "Estimation de la valeur hors taxes du lot :"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div.contenuDeLAvis').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Code(s) CPV additionnel(s)
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuDeLAvis'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Code CPV principal :
                    # Onsite Comment -None

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.CSS_SELECTOR, 'div.contenuDeLAvis').text
			          
                    lot_details_data.lot_cpv_at_source = 'CPV'
                     
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
  




#----------------------------------------------------------------------------------------------------------------
    # Onsite Field -None
    # Onsite Comment -Format 3 :  "https://www.marchesonline.com/appels-offres/avis/fourniture-de-colis-de-noel-pour-les-aines/ao-9084131-1"
    
    
    

  
    # Onsite Field -Objet du marché :
    # Onsite Comment -Format 3 :  "https://www.marchesonline.com/appels-offres/avis/fourniture-de-colis-de-noel-pour-les-aines/ao-9084131-1"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durée du marché ou délai d'exécution :
    # Onsite Comment -split data after 'Durée du marché ou délai d'exécution :'

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée du marché ou délai d'exécution :")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis à la publication :
    # Onsite Comment -split data after 'Date d'envoi du présent avis à la publication : '

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis à la publication :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
        # Onsite Field -Client  :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.location').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Identification de l'organisme qui passe le marché :
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Critères de sélection :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Critères de sélection :")]'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Critères de sélection :
        # Onsite Comment -Split data from "Critères de sélection :" till "Date limite : "JUST TAKE TITLE SKIP VALUE" ... eg "Qualité des produits proposés et de l'emballage - 30 %," ---- just take "Qualité des produits proposés et de l'emballage"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères de sélection :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères de sélection :
        # Onsite Comment -Split data from "Critères de sélection :" till "Date limite : "JUST TAKE VALUE SKIP WEIGHT" ... eg "Qualité des produits proposés et de l'emballage - 30 %," ---- just take "30 %"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères de sélection :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères de sélection :
        # Onsite Comment -Split data from "Critères de sélection :" till "Date limite : "JUST TAKE TITLE SKIP VALUE" ... eg " Prix - 50 %," ---- just take "Prix"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères de sélection :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères de sélection :
        # Onsite Comment -Split data from "Critères de sélection :" till "Date limite : "JUST TAKE VALUE SKIP WEIGHT" ...  eg " Prix - 50 %," ---- just take "50 %"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères de sélection :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères de sélection :
        # Onsite Comment -Split data from "Critères de sélection :" till "Date limite : "JUST TAKE TITLE SKIP VALUE" ... eg "Conditions de livraison (préciser si franco de port - 10 %," JUST TAKE "Conditions de livraison (préciser si franco de por"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères de sélection :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères de sélection :
        # Onsite Comment -Split data from "Critères de sélection :" till "Date limite : "JUST TAKE VALUE SKIP WEIGHT" ... eg "Conditions de livraison (préciser si franco de port - 10 %," JUST TAKE "10%"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères de sélection :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères de sélection :
        # Onsite Comment -Split data from "Critères de sélection :" till "Date limite : "JUST TAKE TITLE SKIP VALUE" ... eg "Circuits courts & développement durable - 10 %." just take "Circuits courts & développement durable"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères de sélection :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères de sélection :
        # Onsite Comment -Split data from "Critères de sélection :" till "Date limite : "JUST TAKE VALUE SKIP WEIGHT" ... eg "Circuits courts & développement durable - 10 %."just take "10%"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères de sélection :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
  


#----------------------------------------------------------------------------------------------------------------
    # Onsite Field -None
    # Onsite Comment -Format 4 : "https://www.marchesonline.com/appels-offres/avis/amo-pour-la-preparation-des-marches-de-fournitures-de/ao-9084139-1"



    
    # Onsite Field -Objet du marché :
    # Onsite Comment -Format 4 : "https://www.marchesonline.com/appels-offres/avis/amo-pour-la-preparation-des-marches-de-fournitures-de/ao-9084139-1"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durée du marché ou délai d'exécution :
    # Onsite Comment -split data after 'Durée du marché ou délai d'exécution :  '

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée du marché ou délai d'exécution :")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis à la publication :
    # Onsite Comment -split data after 'Date d'envoi du présent avis à la publication : '

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis à la publication :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
        # Onsite Field -Client  :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.location').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -I.1) Nom et adresses :
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tél :
        # Onsite Comment -split data after 'Tél : ' till 'courriel :'

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -courriel :
        # Onsite Comment -split data after 'courriel :' till 'adresse internet :'

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse du profil d'acheteur :
        # Onsite Comment -split data after  adresse internet du profil acheteur :'  take url only

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Code NUTS :
        # Onsite Comment -split data after  'Code NUTS :'

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Critères d'attribution :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral > pce > pce > pce > pce > pce > span'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -Split data from "Critères d'attribution :" JUST TAKE TITLE SKIP VALUE" ... eg "Valeur technique de l'offre appréciée à l'aide du mémoire technique (50 %)" ---- just take "Valeur technique de l'offre appréciée à l'aide du mémoire technique"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral > pce > pce > pce > pce > pce > span').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -Split data from "Critères d'attribution :" JUST TAKE TITLE SKIP VALUE" ... eg "Valeur technique de l'offre appréciée à l'aide du mémoire technique (50 %)" ---- just take "50 %"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral > pce > pce > pce > pce > pce > span').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -Split data from "Critères d'attribution :" JUST TAKE TITLE SKIP VALUE" ... eg "Prix (50 %)" ---- just take "Prix"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral > pce > pce > pce > pce > pce > span').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -Split data from "Critères d'attribution :" JUST TAKE TITLE SKIP VALUE" ... eg "Prix (50 %)" ---- just take "50 %"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral > pce > pce > pce > pce > pce > span').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Lot
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            lot_details_data = lot_details()
        # Onsite Field -Lot
        # Onsite Comment -split data from "Lot" take only "Lot 1"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div > div.colOne').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lot
        # Onsite Comment -split data after "Lot"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div > div.colOne').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
 

#----------------------------------------------------------------------------------------------------------------
    # Onsite Field -None
    # Onsite Comment -format 5 : "https://www.marchesonline.com/appels-offres/avis/travaux-de-rehabilitation-plan-climat-et-d-ameliorati/ao-9082791-1"




 
    # Onsite Field -II.1.4) Description succincte :
    # Onsite Comment -format 5 : "https://www.marchesonline.com/appels-offres/avis/travaux-de-rehabilitation-plan-climat-et-d-ameliorati/ao-9082791-1"

        # Onsite Field -None
    # Onsite Comment -None
    notice_data.cpv_at_source = 'CPV'

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.5) Valeur totale estimée
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durée en mois :
    # Onsite Comment -split data after 'Durée en mois :'

    try:
        notice_data.contract_duration = page_details.find_element(By.CSS_SELECTOR, 'p_lot').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis :
    # Onsite Comment -split data after 'Date d'envoi du présent avis :'

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
        # Onsite Field -Client  :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.location').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Nom et adresse officiels de l'organisme acheteur
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -tél. :
        # Onsite Comment -split data after 'tél. :' till 'courriel :'

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -courriel :
        # Onsite Comment -split data after 'courriel :' till 'Fax : '

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax :
        # Onsite Comment -split data after 'Fax : ' till 'Code NUTS :'

            try:
                customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -adresse internet du profil acheteur
        # Onsite Comment -split data after 'adresse internet du profil acheteur'

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
        # Onsite Field -Code NUTS :
        # Onsite Comment -split data after 'Code NUTS :' till 'Code d'identification national'

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Activité principale :
        # Onsite Comment -split data after ' Activité principale :'

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
                
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR' 
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Code CPV principal :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            cpvs_data = cpvs()
        # Onsite Field -Code CPV principal :
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.2) Code(s) CPV additionnel(s) :
        # Onsite Comment -split after 'II.2.2) Code(s) CPV additionnel(s) :'

            try:
                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, 'p_lot').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -II.2.5) Critères d'attribution :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'p_lot'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -II.2.5) Critères d'attribution :
        # Onsite Comment -Split data from "II.2.5) Critères d'attribution :" JUST TAKE TITLE SKIP VALUE" ... eg " Valeur technique de l'offre / Pondération : 60" ---- just take "Valeur technique"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'p_lot').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.5) Critères d'attribution :
        # Onsite Comment -Split data from "II.2.5) Critères d'attribution :" JUST TAKE TITLE SKIP VALUE" ... eg "Valeur technique de l'offre / Pondération : 60" ---- just take " 60"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'p_lot').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.5) Critères d'attribution :
        # Onsite Comment -Split data from "II.2.5) Critères d'attribution :" JUST TAKE TITLE SKIP VALUE" ... eg "Prix - Pondération : 40" ---- just take "Prix"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'p_lot').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.5) Critères d'attribution :
        # Onsite Comment -Split data from "II.2.5) Critères d'attribution :" JUST TAKE TITLE SKIP VALUE" ... eg "Prix - Pondération : 40" ---- just take "40"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'p_lot').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Information sur les fonds de l'Union européenne :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'p_lot'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Information sur les fonds de l'Union européenne :
        # Onsite Comment -if in below text written as " Le contrat s'inscrit dans un projet/programme financé par des fonds de l'Union européenne : non " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" if the abve  text written as " Le contrat s'inscrit dans un projet/programme financé par des fonds de l'Union européenne : YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.CSS_SELECTOR, 'p_lot').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
 

#----------------------------------------------------------------------------------------------------------------
    # Onsite Field -None
    # Onsite Comment -format 6 : "https://www.marchesonline.com/appels-offres/avis/travaux-d-assainissement-et-d-amenagement-de-voirie-ru/ao-9084118-1"



 
    # Onsite Field -1. Objet de la consultation :
    # Onsite Comment -format 6 : "https://www.marchesonline.com/appels-offres/avis/travaux-d-assainissement-et-d-amenagement-de-voirie-ru/ao-9084118-1"
 
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.cpv_at_source = 'CPV''
    
    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Les dates prévisionnelles de début et fin de chantier sont les suivantes :
    # Onsite Comment -take first date as tender_contract_start_date

    try:
        notice_data.tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Les dates prévisionnelles de début et fin de chantier sont les suivantes :")]').text
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Les dates prévisionnelles de début et fin de chantier sont les suivantes :
    # Onsite Comment -take second date as tender_contract_end_date

    try:
        notice_data.tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Les dates prévisionnelles de début et fin de chantier sont les suivantes :")]').text
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis à la publication :
    # Onsite Comment -split after 'Date d'envoi du présent avis à la publication :'

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis à la publication :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Délai de validité des offres :
    # Onsite Comment -split after ' Délai de validité des offres : '

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Délai de validité des offres :")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
        # Onsite Field -Client  :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.location').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -2. Pouvoir adjudicateur :
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tél. :
        # Onsite Comment -split after ' Tél. :'

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tél. adresse du profil acheteur :
        # Onsite Comment -split after 'adresse du profil acheteur :  '

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Classification CPV (Vocabulaire commun pour les marchés publics) :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > span:nth-child(8)'):
            cpvs_data = cpvs()
        # Onsite Field -Classification CPV (Vocabulaire commun pour les marchés publics) :
        # Onsite Comment -split data after 'Classification CPV (Vocabulaire commun pour les marchés publics) :'

            try:
                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > span:nth-child(8)').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
  


#----------------------------------------------------------------------------------------------------------------
    # Onsite Field -None
    # Onsite Comment -format 7  : "https://www.marchesonline.com/appels-offres/avis/veille-juridique-echanges-d-experiences-mise-a-dis/ao-9082918-1"
    
    
    
    
  
    # Onsite Field -1. Objet de la consultation :
    # Onsite Comment -format 7  : "https://www.marchesonline.com/appels-offres/avis/veille-juridique-echanges-d-experiences-mise-a-dis/ao-9082918-1"

        # Onsite Field -None
    # Onsite Comment -None
    notice_data.cpv_at_source = 'CPV'
    
    
    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_2').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date prévisionnelle de début des prestations :
    # Onsite Comment -take first date as tender_contract_start_date

    try:
        notice_data.tender_contract_start_date = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > span:nth-child(14)').text
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durée de validité des offres
    # Onsite Comment -split after 'Durée de validité des offres'

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée de validité des offres")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis :
    # Onsite Comment -split after 'Date d'envoi du présent avis :'

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
        # Onsite Field -Client  :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Pouvoir adjudicateur :
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    


#new format https://www.marchesonline.com/appels-offres/avis/delegation-de-service-public-relative-a-l-accueil-p/ao-9125615-1

# Onsite Field -Valeur totale estimée :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            lot_details_data = lot_details()
        # Onsite Field -Valeur totale estimée :
        # Onsite Comment -take lot_actual_number for ex."lot 1 : 2 728 000 euros hors taxes" , here split only "lot 1 :"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Valeur totale estimée :
        # Onsite Comment -take lot_title for ex."lot 1 : 2 728 000 euros hors taxes" , here split only "lot 1 :" as a lot_title

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Valeur totale estimée :
        # Onsite Comment -take lot_netbudget for ex."lot 1 : 2 728 000 euros hors taxes" , here split only "2 728 000 euros" as a lot_netbudget

            try:
                lot_details_data.lot_netbudget = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Valeur totale estimée :
        # Onsite Comment -take lot_netbudgetlc for ex."lot 1 : 2 728 000 euros hors taxes" , here split only "2 728 000 euros" as a lot_netbudgetlc

            try:
                lot_details_data.lot_netbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Date envoi du présent avis
    # Onsite Comment -split the data after "Date envoi du présent avis :" field

    try:
        dispatch_date = page_details.find_element(By.CSS_SELECTOR, "strong:nth-child(61)").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Pouvoir adjudicateur :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > txt:nth-child(7)'):
            customer_details_data = customer_details()
        # Onsite Field -Pouvoir adjudicateur
        # Onsite Comment -"split data after 'Pouvoir adjudicateur ' "

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > txt:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'FR'
            customer_details_data.org_country = 'FR'
        # Onsite Field -Commune de Grasse :
        # Onsite Comment -split data after 'Commune de Grasse :'

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > txt:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tél. :
        # Onsite Comment -split data after 'Tél.

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > txt:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -courriel :
        # Onsite Comment -split data after "courriel :'

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > txt:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > p_nul:nth-child(5)  strong:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description succincte
    # Onsite Comment -split data after 'Description succincte ' till 'Valeur totale estimée : '

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > p_nul:nth-child(5)  strong:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

# Onsite Field -Code CPV : 
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            cpvs_data = cpvs()
        # Onsite Field -Code CPV : 
        # Onsite Comment - "split data after Code CPV : 


            try:
                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass

            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
   




#new format https://www.marchesonline.com/appels-offres/avis/travaux-de-restauration-des-facades-du-musee-internat/ao-9134343-1


   
    
# Onsite Field -Critères d'attribution :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Critères d'attribution :")]'):
            tender_criteria_data = tender_criteria()

        # Onsite Field -Critères d'attribution :
        # Onsite Comment -

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attribution :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attribution :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass

            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass


# Onsite Field -CPV :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"CPV :")]'):
            cpvs_data = cpvs()
        # Onsite Field -CPV :
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV :")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass



# Onsite Field -None
# Onsite Comment -

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -Nom et adresse officiels de l'organisme acheteur :
        # Onsite Comment -

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Nom et adresse officiels de l'organisme acheteur :
        # Onsite Comment -

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -courriel :
        # Onsite Comment -

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tél.
        # Onsite Comment -

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

        # Onsite Field -Télécopieur
        # Onsite Comment -

            try:
                customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

        # Onsite Field -adresse Internet :
        # Onsite Comment -

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    # Onsite Field -Durée et délai du marché :
    # Onsite Comment -split after 'Durée et délai du marché : '

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée et délai du marché :")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass


    # Onsite Field -and split data between "Nature et étendue (travaux) :"  and "La procédure d'achat du présent avis est couverte par l'accord sur les marchés publics de l'OMC :
    # Onsite Comment -and split data between "Nature et étendue (travaux) :"  and "La procédure d'achat du présent avis est couverte par l'accord sur les marchés publics de l'OMC :
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée et délai du marché :")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass


    # Onsite Field -and split data between "Nature et étendue (travaux) :"  and "La procédure d'achat du présent avis est couverte par l'accord sur les marchés publics de l'OMC :
    # Onsite Comment -and split data between "Nature et étendue (travaux) :"  and "La procédure d'achat du présent avis est couverte par l'accord sur les marchés publics de l'OMC :

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée et délai du marché :")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass


    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
        
        
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.marchesonline.com/appels-offres/en-cours'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
    urls = ['https://www.marchesonline.com/appels-offres/en-cours#id_ref_type_recherche=1&id_ref_type_avis=2&statut_avis%5B%5D=2'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/div[2]/form/article/div[8]/section'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[2]/form/article/div[8]/section')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[2]/form/article/div[8]/section')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[4]/div[2]/form/article/div[8]/section'),page_check))
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
        for page_no in range(2,6):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'/html/body/div[4]/div[2]/form/article/div[8]/section'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '/html/body/div[4]/div[2]/form/article/div[8]/section')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '/html/body/div[4]/div[2]/form/article/div[8]/section')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'/html/body/div[4]/div[2]/form/article/div[8]/section'),page_check))
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
    
    page_details.quit() 
    
    page_details.quit() 
    
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    