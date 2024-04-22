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
SCRIPT_NAME = "fr_boamp_ted_ca"
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
    notice_data.script_name = 'fr_boamp_ted_ca'
    
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
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Avis n°
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-grid-row > div.fr-checkbox-group > label').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publié le
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.fr-grid-row > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -take local_title in textform

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification > h2 > p > a > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -TYPE D'AVIS :
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification-info > ul > li:nth-child(3) > span.ng-binding').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -PROCÉDURE :
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, ".fr-mb-4w > ul > li:nth-child(4) > span.ng-binding").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_ted_ca_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Voir l’annonce
    # Onsite Comment -inspect url for detail page , url ref ="https://www.boamp.fr/pages/avis/?q=idweb:%2223-136872%22"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.fr-container.fr-container--fluid > div').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet du marché :")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet du marché :
    # Onsite Comment -split the following data from "Objet du marché :" field

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet du marché :")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Adresse internet du profil d'acheteur :
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse internet du profil d'acheteur :")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Liens vers les avis initiaux : Avis de marché :
    # Onsite Comment -take only in text format and split only related_id for ex. "Référence : 23-65912" , here split only "23-65912"

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Avis de marché")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
        

     # Onsite Field -II.1.3)Type de marché
    # Onsite Comment -for notice_contract_type click on "Voir l'annonce" and  Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works ',' Fournitures = Supply')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché")]//following::td[3]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.3)Type de marché
    # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and grabbed the data from "II.1.3)Type de marché" field

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché")]//following::td[3]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass    
        
        
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = '"CPV"'    


        
    # Onsite Field -II.1.7)Valeur totale du marché (hors TVA) :
    # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and  take the value from  "II.1.7)Valeur totale du marché (hors TVA) :" field

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),'Valeur totale du marché')]//following::td[3]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -II.1.7)Valeur totale du marché (hors TVA) :
    # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and  take the value from  "II.1.7)Valeur totale du marché (hors TVA) :" field

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),'Valeur totale du marché')]//following::td[3]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # # Onsite Field -II.1.7)Valeur totale du marché (hors TVA) :
    # # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and  take the value from  "II.1.7)Valeur totale du marché (hors TVA) :" field

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),'Valeur totale du marché')]//following::td[3]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
                  

    # Onsite Field -VI.5)	DATE D'ENVOI DU PRÉSENT AVIS
    # Onsite Comment -split the data from "VI.5)		DATE D'ENVOI DU PRÉSENT AVIS" field

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),'VI.5)')]//following::tr[1]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass   

    # Onsite Field -II.1.2)Code CPV principal : > Descripteur principal :
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV principal :")]//following::tr[1]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass   

    # Onsite Field -Durée en mois :
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée en mois")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass      
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#toplist >  div'):
            customer_details_data = customer_details()
            
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -ACHETEUR :
        # Onsite Comment -split the following data from "ACHETEUR :" field

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'li.fr-my-1v.fr-py-0 > span.ng-binding').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse :
        # Onsite Comment -split the following data from "Adresse :" field

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(5) div  li:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Téléphone :
        # Onsite Comment -split the following data from "Téléphone :" field

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),'Téléphone :')]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Courriel :
        # Onsite Comment -split the following data from "Courriel :" field

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),'Courriel :')]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse internet :
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),'Adresse internet :')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -I.4)TYPE DE POUVOIR ADJUDICATEUR
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and grabbed the data from "I.4)TYPE DE POUVOIR ADJUDICATEUR" field

            try:
                customer_details_data.type_of_authority_code = None.find_element(By.None, '//*[contains(text(),'TYPE DE POUVOIR ADJUDICATEUR')]//following::td[3]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -I.5)ACTIVITÉ PRINCIPALE
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and grabbed the data from "I.5)ACTIVITÉ PRINCIPALE" field

            try:
                customer_details_data.customer_main_activity = None.find_element(By.None, '//*[contains(text(),'ACTIVITÉ PRINCIPALE')]//following::td[3]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
   
    
# Onsite Field -II.1.2)Code CPV principal :
# Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and cpv_code split after "Descripteur principal :"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > table'):
            cpvs_data = cpvs()
        # Onsite Field -II.1.2)Code CPV principal :  >  Descripteur principal :
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and cpv_code split after "Descripteur principal :"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV principal :")]//following::tr[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass


    
# Onsite Field -None
# Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") to view to lot_details

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > table'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -take only lot_number for ex."Ce marché comporte 2 lots" , here split only "2"

            try:
                lot_details_data.lot_number = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > div > li > div  button').text
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lot nº :
        # Onsite Comment -lot_actual_number split after "Lot nº" field.

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),'Lot nº')]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Intitulé :
        # Onsite Comment -split lot_title after "Intitulé :" field

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),'II.2.1)')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -lI.2.4)Description des prestations
        # Onsite Comment -split lot_description after "Description des prestations :", ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2223-136481%22"

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),'II.2.4)')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.3)	Lieu d'exécution >> Code NUTS :
        # Onsite Comment -lot_nuts split after "	Code NUTS :

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Lieu d'exécution")]//following::tr[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -Date de conclusion du marché :
        # Onsite Comment -split the data after "V.2.1) Date de conclusion du marché :" field

            try:
                lot_details_data.lot_award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date de conclusion du marché : ")]').text
            except Exception as e:
                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -II.2.2)Code(s) CPV additionnel(s)
        # Onsite Comment -None

            try:
                lot_details_data.lot_cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Code(s) CPV additionnel(s)")]//following::tr[1]').text
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                pass     

        # Onsite Field -Durée en mois :
        # Onsite Comment -if contract_duration is available in lots then take the given data

            try:
                lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée en mois")]').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass           
        
        # Onsite Field -II.2.2)Code(s) CPV additionnel(s)
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") to view to lot_details

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > table'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -II.2.2)Code(s) CPV additionnel(s)
                    # Onsite Comment -split lot_cpv_code after "Code CPV principal :" ,  split all the lot_cpv_code between "II.2.2)Code(s) CPV additionnel(s)" and "II.2.3)Lieu d'exécution" field          ,    ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2223-136481%22"

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code(s) CPV additionnel(s)")]//following::tr[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -II.2.5)Critères d'attribution
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") to view to lot_details

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > table'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -II.2.5)Critères d'attribution >>  2. Valeur technique / Pondération :
                    # Onsite Comment -split lot_criteria_title. eg., here "2. Valeur technique / Pondération : 10" take only "Valeur technique " in lot_criteria_title.,   ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2223-136818%22"

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attribution")]//following::tr[3]').text
			
                    # Onsite Field -II.2.5)Critères d'attribution >>  2. Valeur technique / Pondération :
                    # Onsite Comment -split lot_criteria_weight. eg., here "2. Valeur technique / Pondération : 30" take only "30" in lot_criteria_weight. ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2223-136818%22"

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attribution")]//following::tr[3]').text
			
                    # Onsite Field -II.2.5)Critères d'attribution >>  Prix :
                    # Onsite Comment -split lot_criteria_title. eg., here "Prix :1. Prix / Pondération : 70" take only "Prix" in lot_criteria_title., ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2223-136818%22"

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attribution")]//following::tr[4]').text
			
                    # Onsite Field -II.2.5)Critères d'attribution >>  Prix :
                    # Onsite Comment -split lot_criteria_weight. eg., here "Prix :1. Prix / Pondération : 70" take only "70" in lot_criteria_weight, ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2223-136818%22"

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attribution")]//following::tr[4]').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -V.2.3)Nom et adresse du titulaire
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") to view to award_details

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > table'):
                    award_details_data = award_details()
		
                    # Onsite Field -V.2.3)Nom et adresse du titulaire
                    # Onsite Comment -split bidder_name. eg., here "GEDIA SEML, Dreux, F, Code NUTS : FRB02 Le titulaire est une PME : oui" take only "GEVEKO MARKINGS SAS" in bidder_name.

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Nom et adresse du titulaire')]//following::tr[1]').text
			
                    # Onsite Field -V.2.3)Nom et adresse du titulaire
                    # Onsite Comment -split address. eg., here "GEVEKO MARKINGS SAS, 16-18-16 rue du Bon Puits - St Sylvain d'Anjou, 49480, VERRIERES EN ANJOU, FR, Code NUTS : FRG02," take only "GEVEKO MARKINGS SAS, 16-18-16 rue du Bon Puits - St Sylvain d'Anjou, 49480, VERRIERES EN ANJOU, FR," in address., ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2223-136818%22"

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),'Nom et adresse du titulaire')]//following::tr[1]').text
			
                    # Onsite Field -V.2.4)Informations sur le montant du marché/du lot   >> Estimation initiale du montant total du marché/du lot :
                    # Onsite Comment -split initial_estimate_amount after "Estimation initiale du montant total du marché/du lot :"

                    award_details_data.initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),'Estimation initiale du montant total du marché/du lot :')]').text
			
                    # Onsite Field -Valeur totale du marché/du lot :
                    # Onsite Comment -split grossawardvaluelc after "Valeur totale du marché/du lot :"

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),'Valeur totale du marché/du lot :')]').text
			
                    # Onsite Field -Valeur totale du marché/du lot :
                    # Onsite Comment -split grossawardvalueeuro  after "Valeur totale du marché/du lot :"

                    award_details_data.grossawardvalueeuro = page_details.find_element(By.XPATH, '//*[contains(text(),'Valeur totale du marché/du lot :')]').text

                    # Onsite Field -Date de conclusion du marché :
                    # Onsite Comment -split the data after "V.2.1)	Date de conclusion du marché :" field

                    award_details_data.award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date de conclusion du marché : ")]').text
			
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
    
# Onsite Field -II.2.13)Information sur les fonds de l'Union européenne
# Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and split the data from "II.2.13)Information sur les fonds de l'Union européenne" field

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > table'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -II.2.13)Information sur les fonds de l'Union européenne
        # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT" "II.2.13) Information about European Union Funds  >  	The contract is part of a project/program financed by European Union funds: no " if the above  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),'II.2.13)')]//following::tr[1]').text
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&refine.type_avis=10&refine.type_avis=8&refine.type_avis=6&refine.famille=JOUE&q.filtre_etat=(NOT%20%23null(datelimitereponse)%20AND%20datelimitereponse%3E%3D%222023-10-05%22)%20OR%20(%23null(datelimitereponse)%20AND%20datefindiffusion%3E%3D%222023-10-05%22)#resultarea"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,15):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="toplist"]/li/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="toplist"]/li/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="toplist"]/li/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="toplist"]/li/div'),page_check))
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