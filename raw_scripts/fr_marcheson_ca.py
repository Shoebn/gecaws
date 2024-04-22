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
SCRIPT_NAME = "fr_marcheson_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -click on "Type d'avis" > "Attributions de marchés" to get contract_award
    notice_data.script_name = 'fr_marcheson_ca'
    
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
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Avis N°
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.noticeNumber > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Mise en ligne
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
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Resultats :'
    
    # Onsite Field -None
    # Onsite Comment -Replace following keywords with given respective keywords ("Services = Services","Travaux de bâtiment = work","Etudes, Maîtrise d'oeuvre, Contrôle = Services","Fournitures = supply" ,"Travaux Publics = work")

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.activity').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -format 1,

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.activity').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'section.blockNotice  > a').get_attribute("href")                     
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
    


#    format 1      url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"
# ----------------------------------------------------------------------------------------------------------------------------------------------------

    
    # Onsite Field -
    # Onsite Comment -format 1, split the data between "Type de marché :" and "Les éléments de mission de maitrise d'oeuvre sont :" field 

    try:
        notice_data.local_description = page_main.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Annonce N°
    # Onsite Comment -format 1,   split the data from "Section 1 :"

    try:
        notice_data.related_tender_id = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass


    # Onsite Field -Date d'envoi du présent avis :
    # Onsite Comment -format 1, split the data from "Date d'envoi du présent avis : " field

    try:
        dispatch_date = page_details.find_element(By.CSS_SELECTOR, "div.contenuIntegral.borderBottom").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    


    # Onsite Field -Description succincte du marché :
    # Onsite Comment -format 1,   split the data from "Section 1 :"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = 'CPV'
    
# Onsite Field -Code CPV principal Descripteur principal :
# Onsite Comment -format 1 ,   split the following data from "Code CPV principal Descripteur principal :" field

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            cpvs_data = cpvs()
        # Onsite Field -Code CPV principal Descripteur principal :
        # Onsite Comment -format 1 ,   split the following data from "Code CPV principal Descripteur principal :" field

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
    
    
# Onsite Field -None
# Onsite Comment -format 1 ,

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            customer_details_data = customer_details()
        # Onsite Field -Client :
        # Onsite Comment -format 1 , split the data from detail_page

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ville :
        # Onsite Comment -format 1 , split the data between "N° National d'identification :" and "Code Postal :" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"

            try:
                customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -Code Postal :
        # Onsite Comment -split the data between "Ville :" and "Groupement de commandes :" field , ref_url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"

            try:
                customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
# Onsite Field -Critères d'évaluation des projets :
# Onsite Comment -format 1,   split the data from "Critères d'évaluation des projets" field

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Critères d'évaluation des projets :
        # Onsite Comment -format 1,   split only "tender_criteria_title" , for ex: "Valeur technique : 55%" , here split only "Valeur technique" , ref_url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'évaluation des projets :
        # Onsite Comment -format 1,   split only "tender_criteria_weight" , for ex: "Valeur technique : 55%" , here split only "55%" , ref_url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'évaluation des projets :
        # Onsite Comment -format 1,   split only "tender_criteria_title" , for ex: "Prix : 45%" , here split only "Prix" , ref_url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'évaluation des projets :
        # Onsite Comment -format 1,   split only "tender_criteria_weight" , for ex: "Prix : 45%" , here split only "Prix" , ref_url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Renseignements relatifs à l'attribution du marché et/ou des lots :
# Onsite Comment -format 1, ref_url : "https://www.marchesonline.com/appels-offres/attribution/rehabilitation-de-22-logements-collectifs/am-9084101-1"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            lot_details_data = lot_details()
        # Onsite Field --Lot N° / Marché n° :
        # Onsite Comment -format 1, split  "Lot N°" from the given selector and here in some records split no which is below "Marché n° : 2023" for eg : take "/724" as lot_actual_number if it is not available then pass " Lot N° /  Lot" as lot_actual_number, ref_url : "https://www.marchesonline.com/appels-offres/attribution/rehabilitation-de-22-logements-collectifs/am-9084101-1"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lot N° :
        # Onsite Comment -format 1, split the lot_title for ex."Lot No. 01 - Major Works / Facades" , here split only "Major Works / Facades" as a lot_title

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -format 1, ref_url : "https://www.marchesonline.com/appels-offres/attribution/rehabilitation-de-22-logements-collectifs/am-9084101-1"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -format 1,  split between from "Marché n° : " to "Montant Ht : " , ref_url : "https://www.marchesonline.com/appels-offres/attribution/rehabilitation-de-22-logements-collectifs/am-9084101-1"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
			
                    # Onsite Field -Montant Ht :
                    # Onsite Comment -format 1, split the daat from  "Montant Ht :" field

                    award_details_data.netawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
			
                    # Onsite Field -Montant Ht :
                    # Onsite Comment -format 1, split the daat from  "Montant Ht :" field

                    award_details_data.netawardvalueeuro = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
			
                    # Onsite Field -Date d'attribution :
                    # Onsite Comment -format 1, split award_date from selector and take from where lots are available

                    award_details_data.award_date = page_details.find_element(By.CSS_SELECTOR, 'div.surbrillance_1').text
			
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








# format 2  url : "https://www.marchesonline.com/appels-offres/attribution/accord-cadre-de-coordination-architecturale-urbaine-et/am-9081928-1"
# -------------------------------------------------------------------------------------------------------------------------------------------    



    # Onsite Field -Adresse du profil d'acheteur :
    # Onsite Comment -format 2, split the additional_tender_url from "Adresse du profil d'acheteur :" field

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.1) Intitulé
    # Onsite Comment -format 2,  split the related id from "II.1.1) Intitulé " field , here split only "Numéro de référence : M2023-005" value

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.1) Intitul")]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

      # Onsite Field -IV.1.1) Type de procédure
    # Onsite Comment -split the data from "IV.1.1) Type de procédure" field
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"IV.1.1) Type de procédure")]").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcheson_ca_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Description succincte")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.4) Description succincte :
    # Onsite Comment -format 2,  split the notice_summary_english from "II.1.4) Description succincte" field

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Description succincte")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7) Valeur totale finale du marché (hors TVA)
    # Onsite Comment -format 2,  split the data from "II.1.7) Valeur totale finale du marché (hors TVA)" field

    try:
        notice_data.netbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7) Valeur totale finale du marché (hors TVA)
    # Onsite Comment -format 2,  split the data from "II.1.7) Valeur totale finale du marché (hors TVA)" field

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7) Valeur totale finale du marché (hors TVA)
    # Onsite Comment -format 2,  split the data from "II.1.7) Valeur totale finale du marché (hors TVA)" field

    try:
        notice_data.est_amount = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -VI.5) Date d'envoi du présent avis :
    # Onsite Comment -format 2,  split the following data from "VI.5) Date d'envoi du présent avis :" field

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"VI.5) Date d'envoi du présent avis")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    


    # Onsite Field -None
    # Onsite Comment -format 2, split the customer_Details from detail_page

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -Client :
        # Onsite Comment -format 2,   split the org_name from "Client :" field

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -I.1) Nom et adresses
        # Onsite Comment -format 2 , split the org_address from "I.1) Nom et adresses" field

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text()," I.1) Nom et adresses")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Code NUTS
        # Onsite Comment -format 2,  split the data from "Code NUTS " field till "Adresse(s) internet"

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -I.4) Type de pouvoir adjudicateur
        # Onsite Comment -format 2,  split the data from "I.4) Type de pouvoir adjudicateur" field

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"I.4) Type de pouvoir adjudicateur")]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -I.5) Activité principale
        # Onsite Comment -format 2,  split the data from "I.5) Activité principale" field

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"I.5) Activité principale")]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -None
            notice_data.class_at_source = 'CPV'    
        
        # Onsite Field -Adresse principale :
        # Onsite Comment -format 2,   split the data from "Adresse principale :" field

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse(s) internet")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -courriel
        # Onsite Comment -format 2,   split the following data from "courriel :" field , for ex. "courriel : Contact@lafab-bm.fr" , here split only "Contact@lafab-bm.fr"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text()," I.1) Nom et adresses")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -II.1.2) Code CPV principal
# Onsite Comment -format 2, split the cpvs from "II.1.2) Code CPV principal" field

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            cpvs_data = cpvs()
        # Onsite Field -II.1.2) Code CPV principal
        # Onsite Comment -format 2, split the following data from "II.1.2) Code CPV principal" field

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.2) Code CPV principal")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.2) Additional CPV code(s)
        # Onsite Comment -format2, split the following data from "II.2.2) Code(s) CPV additionnel(s)" field

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.2) Code(s) CPV additionnel(s) ")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -II.2.5) Critères d'attribution
# Onsite Comment -format 2

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -II.2.5) Critères d'attribution
        # Onsite Comment -format 2 , split only title, for ex." Valeur technique / Pondération : 70" , here split only "Valeur technique", ref_url : "https://www.marchesonline.com/appels-offres/attribution/accord-cadre-de-coordination-architecturale-urbaine-et/am-9081928-1"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Critères d'attribution")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.5) Critères d'attribution
        # Onsite Comment -format 2 , split only weight, for ex." Valeur technique / Pondération : 70" , here split only " Pondération : 70", ref_url : "https://www.marchesonline.com/appels-offres/attribution/accord-cadre-de-coordination-architecturale-urbaine-et/am-9081928-1"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Critères d'attribution")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.5) Critères d'attribution
        # Onsite Comment --format 2 , split only title, for ex." - Prix des prestations / Pondération : 30" , here split only "  Prix des prestations", ref_url : "https://www.marchesonline.com/appels-offres/attribution/accord-cadre-de-coordination-architecturale-urbaine-et/am-9081928-1"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Critères d'attribution")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.5) Critères d'attribution
        # Onsite Comment -format 2 , split only weight, for ex." - Prix des prestations / Pondération : 30" , here split only "Pondération : 30", ref_url : "https://www.marchesonline.com/appels-offres/attribution/accord-cadre-de-coordination-architecturale-urbaine-et/am-9081928-1"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.5) Critères d'attribution")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -II.2.13) Information on European Union funds
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -II.2.13) Information sur les fonds de l'Union européenne
        # Onsite Comment -if in below text written as " Le contrat s'inscrit dans un projet/programme financé par des fonds de l'Union européenne : non. " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information sur les fonds de l'Union européenne :  >  Le contrat s'inscrit dans un projet/programme financé par des fonds de l'Union européenne : non. " if the abve  text written as "  Le contrat s'inscrit dans un projet/programme financé par des fonds de l'Union européenne : YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.13)")]').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -format 2

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            lot_details_data = lot_details()
        # Onsite Field -Marché n°
        # Onsite Comment -format 2, split the following data from "Marché n°" field

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Marché n°")]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Intitulé :
        # Onsite Comment -format 2,  split the following data from "Intitulé :" field

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -V.2) Attribution du marché
        # Onsite Comment -format 2,

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
                    award_details_data = award_details()
		
                    # Onsite Field -V.2.1) Date de conclusion du marché
                    # Onsite Comment -format 2, split the following data from "V.2.1) Date de conclusion du marché" field

                    award_details_data.award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.1) Date de conclusion du marché")]').text
			
                    # Onsite Field -V.2.3) Nom et adresse du titulaire
                    # Onsite Comment -format 2, split the bidder_name from "V.2.3) Nom et adresse du titulaire" field

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Nom et adresse du titulaire")]').text
			
                    # Onsite Field -V.2.3) Nom et adresse du titulaire
                    # Onsite Comment -format 2, split the address from "V.2.3) Nom et adresse du titulaire" field

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Nom et adresse du titulaire")]').text
			
                    # Onsite Field -V.2.4) Informations sur le montant du marché/du lot (hors TVA)
                    # Onsite Comment -format 2, split the data from "V.2.4) Informations sur le montant du marché/du lot (hors TVA)" field

                    award_details_data.netawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.4) Informations sur le montant du marché/du lot (hors TVA)")]').text
			
                    # Onsite Field -V.2.4) Informations sur le montant du marché/du lot (hors TVA)
                    # Onsite Comment -format 2, split the data from "V.2.4) Informations sur le montant du marché/du lot (hors TVA)" field

                    award_details_data.netawardvalueeuro = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.4) Informations sur le montant du marché/du lot (hors TVA)")]').text
			
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
    
    
    



# format 3   url="https://www.marchesonline.com/appels-offres/attribution/travaux-de-demolition-et-desamiantage-rue-jules-uhr/am-9082868-1"
# ----------------------------------------------------------------------------------------------------------------------------------------------------
    # Onsite Field -Type de procédure
    # Onsite Comment -split the data from "Type de procédure" field
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Type de procédure")]").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcheson_ca_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
        

# Onsite Field -None
# Onsite Comment -format 3

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.colOne'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -Client
        # Onsite Comment -format 3

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Nom et adresse officiels de l'organisme acheteur :
        # Onsite Comment -format 3 , split  "Nom et adresse officiels de l'organisme acheteur : from the given selector

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Nom et adresse officiels de l'organisme acheteur :")]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
                
                
        
        # Onsite Field -Nom et adresse officiels de l'organisme acheteur :
        # Onsite Comment -format 3 ,

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Nom et adresse officiels de l'organisme acheteur :")]//following::a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Critères d'attributions retenus :
# Onsite Comment -format 3,

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Critères d'attributions retenus :")]'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Critères d'attributions retenus :
        # Onsite Comment -format 3, split the data from "Critères d'attributions retenus :" field

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attributions retenus :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attributions retenus :
        # Onsite Comment -format 3, split the data from "Critères d'attributions retenus :" field

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attributions retenus :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attributions retenus :
        # Onsite Comment -format 3, split the data from "Critères d'attributions retenus :" field

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attributions retenus :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attributions retenus :
        # Onsite Comment -format 3, split the data from "Critères d'attributions retenus :" field

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attributions retenus :")]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -format 3

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -format 3 ,  if lot_details are not available then pass local_title to lot_title

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > h2').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attribution du marché :
        # Onsite Comment -format 3 ,

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
                    award_details_data = award_details()
		
                    # Onsite Field -Titulaire du marché :
                    # Onsite Comment -format 3 , split the data from "Titulaire du marché :" field

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Titulaire du marché :")]').text
			
                    # Onsite Field -Date d'attribution :
                    # Onsite Comment -format 3 , split the data from "Date d'attribution : " field

                    award_details_data.award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date d'attribution :")]').text
			
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
        




# format 4 url : "https://www.marchesonline.com/appels-offres/attribution/enquete-epale-portant-sur-les-utilisateurs-de-la-plate/am-9082079-/1"
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # Onsite Field -Référence d'identification du marché qui figure dans l'appel d'offres
    # Onsite Comment -format 4, split the data from "Référence d'identification du marché qui figure dans l'appel d'offres" field

    try:
        notice_data.related_tender_id = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis à la publication :
    # Onsite Comment -format 4, split the following data from "Date d'envoi du présent avis à la publication : " field

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis à la publication :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Autres informations :
    # Onsite Comment -format 4, split the url data from "Autres informations :" field

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Autres informations :")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
        
        
    # Onsite Field -Type de procédure
    # Onsite Comment -split the data from "Type de procédure" field
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Type de procédure")]").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcheson_ca_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass    
    
# Onsite Field -None
# Onsite Comment -format 4,

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -Client
        # Onsite Comment -format 4, split the data from "Client" field

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Official name and address of the purchasing organization:
        # Onsite Comment -format 4, split the data from  "Nom et adresse officiels de l'organisme acheteur" field

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -courriel :
        # Onsite Comment -format 4, split the data from  "Nom et adresse officiels de l'organisme acheteur" field

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div > span.jqMailto').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Correspondant :
        # Onsite Comment -format 4, split the data from  "Nom et adresse officiels de l'organisme acheteur" field

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -format 4

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -format 4, if lot_details are not available then pass local_title to lot_title

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identityNotice > h2').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -format 4,

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
                    award_details_data = award_details()
		
                    # Onsite Field -Nom du titulaire / organisme :
                    # Onsite Comment -format 4, split the bidder_name from "Nom du titulaire / organisme :" field

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Nom du titulaire / organisme :")]').text
			
                    # Onsite Field -Montant (H.T.) :
                    # Onsite Comment -format 4, split the data from "Montant (H.T.) :" field

                    award_details_data.netawardvaluelc = page_details.find_element(By.XPATH, 'div.contenuIntegral.borderBottom').text
			
                    # Onsite Field -Montant (H.T.) :
                    # Onsite Comment -format 4, split the data from "Montant (H.T.) :" field

                    award_details_data.netawardvalueeuro = page_details.find_element(By.XPATH, 'div.contenuIntegral.borderBottom').text
			
                    # Onsite Field -Date d'attribution du marché :
                    # Onsite Comment -format 4, split the following data from "Date d'attribution du marché :" field

                    award_details_data.award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date d'attribution du marché :")]').text
			
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
        





# Onsite Comment -format 5
#  ref url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"
# -----------------------------------------------------------------------------------------------------------------------------------------------------

    # Onsite Field -None
# Onsite Comment -format 5

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            customer_details_data = customer_details()
        # Onsite Field -Client :
        # Onsite Comment -format 5, grab the data after "Client :" field

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.identityNotice > p').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -format 5, for address split the data between "Directeur Général" and "Tél" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tél. :
        # Onsite Comment -format 5, for org_phone split the data between "Tél. :" and "mèl :" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -mèl :
        # Onsite Comment -format 5, for org_mail split the data between "mèl :" and " web :" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -web
        # Onsite Comment -format 5, for org_website split the data between "web " and "Siret" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"

            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral div.surbrillance_1').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = '"CPV"'
    
# Onsite Field -None
# Onsite Comment -format 5 ,

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            cpvs_data = cpvs()
        # Onsite Field -Classification CPV :
        # Onsite Comment -format 5 , split only cpvs for ex. "Principale : 45210000 travaux de construction de bâtiments" , here split only "45210000"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Classification CPV :")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -format 5

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
            lot_details_data = lot_details()
        # Onsite Field -Marché n° :
        # Onsite Comment -format 5 , split the following data from "Marché n° :" field

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Marché n° :")]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -format 5 , split the data between "Marché n° :" and "Montant HT " field , it is identified there are multiple bidders, take all specified bidders

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Marché n° :")]').text
			
                    # Onsite Field -None
                    # Onsite Comment -format 5 , split only address , and split the data  between "Marché n° :" and "Montant HT " field

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Marché n° :")]').text
			
                    # Onsite Field -Montant HT :
                    # Onsite Comment -format 5 , split the following data from "Montant HT :" field

                    award_details_data.netawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Montant HT :")]').text
			
                    # Onsite Field -Montant HT :
                    # Onsite Comment -format 5 , split the following data from "Montant HT :" field

                    award_details_data.netawardvalueeuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Montant HT :")]').text
			
                    # Onsite Field -Date d'attribution :
                    # Onsite Comment -format 5 , split the following data from "Date d'attribution :" field

                    award_details_data.award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date d'attribution :")]').text
			
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
    
    # Onsite Field -Valeur totale du marché (hors TVA) :
    # Onsite Comment -format 5, split the following data from "Valeur totale du marché (hors TVA) :" field

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur totale du marché (hors TVA) :")]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valeur totale du marché (hors TVA) :
    # Onsite Comment -format 5, split the following data from "Valeur totale du marché (hors TVA) :" field

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur totale du marché (hors TVA) :")]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valeur totale du marché (hors TVA) :
    # Onsite Comment -format 5, split the following data from "Valeur totale du marché (hors TVA) :" field

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur totale du marché (hors TVA) :")]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Pour retrouver cet avis intégral, allez sur
    # Onsite Comment -format 5, split the following data from "Pour retrouver cet avis intégral, allez sur"

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Envoi le
    # Onsite Comment -format 5, split the data between "Envoi le " and " à la publication"

    try:
        dispatch_date = page_details.find_element(By.CSS_SELECTOR, "div.contenuIntegral.borderBottom").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass    
    
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.marchesonline.com/appels-offres/en-cours#id_ref_type_recherche=1&id_ref_type_avis=2&statut_avis%5B%5D=2'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)