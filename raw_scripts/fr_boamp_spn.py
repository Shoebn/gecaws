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
SCRIPT_NAME = "fr_boamp_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'fr_boamp_spn'
   
    notice_data.main_language = 'FR'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -take local_title in textform

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification > h2 > p > a > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

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
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Date limite de réponse le
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "p.fr-mb-1w > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Voir l’annonce
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-container> div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
        
    try:
        clik= WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," div > div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button")))
        page_details.execute_script("arguments[0].click();",clik)
    except:
        pass
    
    # Onsite Field -None
    # Onsite Comment -for notice text click on "Voir l'annonce" and take all data in notice text
    try:
        notice_data.notice_text +=  WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-notification'))).get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    
    try:
        dispatch_date = page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').text
        if "Date d'envoi du présent avis" in dispatch_date:
            dispatch_date = dispatch_date.split("Date d'envoi du présent avis")[1]
            dispatch_date = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
            dispatch_date = re.findall('\w+ \d+, \d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, ' div.card-notification-info.fr-scheme-light-white.fr-p-5v.fr-mb-4w > ul > li:nth-child(4) ').text.split("PROCÉDURE : ")[1].strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_spn_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet du marché :
    # Onsite Comment -if "Objet du marché :" field is not available in detail page then take local_title as notice_summary_english

    try:
        notice_summary_english = page_details.find_element(By.XPATH, "//*[contains(text(),'Objet du marché :')]//following::span[1]").text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        notice_data.notice_summary_english = notice_data.notice_title
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
   
    
    # Onsite Field -Type de marché :
    # Onsite Comment -for notice_contract_type click on "Voir l'annonce" and Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works ',' Fournitures = Supply')

    try:
        notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Type de marché :')]//following::tr[1]").text
        if "Services" in notice_contract_type:
            notice_data.notice_contract_type ='Service'
        elif "Travaux" in notice_contract_type:
            notice_data.notice_contract_type ='Works'
        elif "Fournitures" in notice_contract_type:
            notice_data.notice_contract_type ='Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # data is countinuosly change so auable to grap this data.
    
    # Onsite Field -Valeur estimée (H.T.) :
    # Onsite Comment -for grossbudgetlc click on "Voir l'annonce"

#     try:
#         grossbudgetlc = page_details.find_element(By.XPATH, "//*[contains(text(),'Valeur estimée (H.T.) :')]//following::tr[1]").text
#         if ',' in grossbudgetlc:
#             grossbudgetlc = grossbudgetlc.replace(",",".")
#         else:
#             grossbudgetlc = grossbudgetlc.replace(" ","")
#         notice_data.grossbudgetlc =float(grossbudgetlc)
#     except Exception as e:
#         logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
#         pass
    
    # Onsite Field -Valeur estimée (H.T.) :
    # Onsite Comment -for est_amount click on "Voir l'annonce"

#     try:
#         notice_data.est_amount = notice_data.grossbudgetlc
#     except Exception as e:
#         logging.info("Exception in est_amount: {}".format(type(e).__name__))
#         pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        # Onsite Field -ACHETEUR :
        # Onsite Comment -None

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification-info > ul > li:nth-child(2)').text.split("ACHETEUR : ")[1]
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        # Onsite Field -Téléphone :
        # Onsite Comment -None

        try:

            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Téléphone :')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Courriel :
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Courriel :')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:              
        cpvs_data = cpvs()
        
        # Onsite Field -Descripteur principal :
        # Onsite Comment -for cpv code  click on "Voir l'annonce" and if cpv is available in detail pg then take it from "Descripteur principal :"  and if the cpv is not available in detail pg then take auto cpv
        cpvs_data.cpv_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Descripteur principal :')]").text.split(":")[1].strip()
        if cpvs_data.cpv_code != "":
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Renseignements relatifs aux lots :
# Onsite Comment -None
    try:
        
        lot_number = 1
        for lots in page_details.find_elements(By.XPATH, "//*[contains(text(),'Section 5 : Lots')]//following::table"):
            lot = lots.text
            if 'Description du lot :' in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_title = lot.split('Description du lot :')[1].split('\n')[0].strip()
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = lot.split('Code CPV principal : ')[1].split('\n')[0].strip()
                if lot_cpvs_data.lot_cpv_code != "":
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__)) 
        pass   
 
    try:
        tender_criteria_data = tender_criteria()
        title = page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').text
        try:
            tender_criteria_title=fn.get_string_between(title,"Critères d'attribution :",'Section 4')
            tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
        except:
            tender_criteria_title=fn.get_string_between(title,"Critères d'attribution :",'Type de procédure :')
            tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
        if tender_criteria_data.tender_criteria_title != "":
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__)) 
        pass   

        # Onsite Field -Type de marché :
        # Onsite Comment -for contract_type click on "Voir l'annonce" and Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works ',' Fournitures = Supply')







 # Onsite Field -below is new code fro updated formats
    # Onsite Comment -new format 1 https://www.boamp.fr/pages/avis/?q=idweb:%2224-5281%22 and to get more data click on "Voir l'annonce complète" 

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet du marché :")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet du marché :
    # Onsite Comment -cmt :- take only value from "L’essentiel du marché >> Objet du marché :"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet du marché :")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valeur estimée hors TVA
    # Onsite Comment -cmt :- take only value from "Procédure >> Valeur estimée hors TVA " only

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur estimée hors TVA")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valeur estimée hors TVA
    # Onsite Comment -cmt :- take only value from "Procédure >> Valeur estimée hors TVA " only

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur estimée hors TVA")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nature du marché
    # Onsite Comment -cmt :- take only value from "Procédure >> Nature du marché " only and replace the following keywords with given respective keywords(Fournitures = Supply,Services = Service,Travaux =  Work)

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Nature du marché")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nature du marché
    # Onsite Comment -cmt :- take only value from "Procédure >> Nature du marché " only

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Nature du marché")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Adresse internet du profil d'acheteur :
    # Onsite Comment -cmt :- take only value from "L’essentiel du marché >> Adresse internet du profil d'acheteur :" only before clicking on "Voir l'annonce complète"

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse internet du profil d'acheteur :")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis à la publication :
    # Onsite Comment -click on "Voir l'annonce complète" to get data

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis à la publication :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -cmt :- take only value from "L’essentiel du marché >> Objet du marché :"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            customer_details_data = customer_details()
        # Onsite Field -Acheteur :
        # Onsite Comment -org_name has same selector for every format as it is taken from tender_html_page

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification-info > ul > li:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse :
        # Onsite Comment -take only value from "L’essentiel du marché"

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse :")]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Point(s) de contact :
        # Onsite Comment -take only value from "L’essentiel du marché"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Point(s) de contact : ")]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Téléphone :
        # Onsite Comment -take only value from "L’essentiel du marché"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Téléphone :")]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Courriel :
        # Onsite Comment -take only value from "L’essentiel du marché"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Courriel :")]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse internet :
        # Onsite Comment -take only value from "L’essentiel du marché"

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse internet :")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Forme juridique de l’acheteur
        # Onsite Comment -take value from "Section 1 - Acheteur >> Forme juridique de l’acheteur"

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Forme juridique de l’acheteur")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Activité du pouvoir adjudicateur
        # Onsite Comment -take value from "Section 1 - "Acheteur >> Activité du pouvoir adjudicateur" after click on "Voir l'annonce complète"

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Activité du pouvoir adjudicateur")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'FR'
            customer_details_data.org_country = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on "Voir l'annonce complète" to get data

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            cpvs_data = cpvs()
        # Onsite Field -Nomenclature principale
        # Onsite Comment -cmt :- take only value from "Procédure >> Nomenclature principale" only

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Nomenclature principale")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Nomenclature supplémentaire
        # Onsite Comment -cmt :- take only value from "Procédure >> Nomenclature supplémentaire" only

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Nomenclature supplémentaire")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Section 5 - Lot
# Onsite Comment -ref url:- https://www.boamp.fr/pages/avis/?q=idweb:%2224-5281%22    cmt :- take only values which is in "Section 5 - Lot " only

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            lot_details_data = lot_details()
        # Onsite Field -Lot
        # Onsite Comment -here take only eg:- "LOT-0001"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Lot")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Titre
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Titre")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Valeur estimée hors TVA
        # Onsite Comment -None

            try:
                lot_details_data.lot_netbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur estimée hors TVA")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Valeur estimée hors TVA
        # Onsite Comment -None

            try:
                lot_details_data.lot_netbudget = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur estimée hors TVA")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Subdivision pays (NUTS)
        # Onsite Comment -here take full eg:-  "Seine-Maritime ( FRD22 )"

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Subdivision pays (NUTS)")]//following::span').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Date de début
        # Onsite Comment -None

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date de début")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Durée
        # Onsite Comment -here take "MONTH" keyword also

            try:
                lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Nature du marché
        # Onsite Comment -take only values which is in "Section 5 - Lot " and replace the following keywords with given respective keywords(Fournitures = Supply,Services = Service,Travaux =  Work)

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Nature du marché")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Nature du marché
        # Onsite Comment -take only values which is in "Section 5 - Lot "

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Nature du marché")]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Nomenclature principale
                    # Onsite Comment -cmt :- take only value from "Section 5 - Lot >> Nomenclature principale" only

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Nomenclature principale")]//following::span[1]').text
			
                    # Onsite Field -Nomenclature supplémentaire
                    # Onsite Comment -cmt :- take only value from "Section 5 - Lot >> Nomenclature supplémentaire" only

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Nomenclature supplémentaire")]//following::span[1]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -ref url:- https://www.boamp.fr/pages/avis/?q=idweb:%2224-5605%22

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -Type
                    # Onsite Comment -take only value from "5.1.10 Critères d’attribution >> Type"

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d’attribution")]//following::div/span[3]').text
			
                    # Onsite Field -Pondération (points, valeur exacte)
                    # Onsite Comment -split and take only value from "5.1.10 Critères d’attribution >> Pondération (points, valeur exacte) "

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d’attribution")]//following::div/span[3]').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass



    
    # Onsite Field -None
    # Onsite Comment -new format 2 https://www.boamp.fr/pages/avis/?q=idweb:%2224-5822%22 and https://www.boamp.fr/pages/avis/?q=idweb:%2224-6361%22 and to get more data click on "Voir l'annonce complète"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description succincte : ")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description succincte :
    # Onsite Comment -cmt :- take only value from " Description du marché >> Description succincte :" only and if the given slector is not available then take "//*[contains(text(),"Description des prestations : ")]" it as notice_summary_english

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description succincte : ")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de marché :
    # Onsite Comment -take only value from "Description du marché>> Type de marché :" only and replace the following keywords with given respective keywords(Fournitures = Supply,Services = Service,Travaux =  Work)

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché :")]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de marché :
    # Onsite Comment -take only value from "Description du marché>> Type de marché :" only

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché :")]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Adresse internet du profil d'acheteur :
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse internet du profil d'acheteur :")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis à la publication :
    # Onsite Comment -click on "Voir l'annonce complète" to get data

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis à la publication :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -take only value from "L’essentiel du marché >> Objet du marché :" and to get more data click on "Voir l'annonce complète"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            customer_details_data = customer_details()
        # Onsite Field -Acheteur :
        # Onsite Comment -org_name has same selector for every format as it is taken from tender_html_page

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.card-notification-info > ul > li:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse :
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse :")]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Courriel :
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Courriel :")]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Téléphone :
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Téléphone :")]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse internet :
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse internet :")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Type de pouvoir adjudicateur :
        # Onsite Comment -None

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de pouvoir adjudicateur : ")]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Activité principale :
        # Onsite Comment -None

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Activité principale : ")]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Code NUTS :
        # Onsite Comment -None

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Code NUTS : ")]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'FR'
            customer_details_data.org_country = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on "Voir l'annonce complète" to get data

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            cpvs_data = cpvs()
        # Onsite Field -CPV - Objet principal :
        # Onsite Comment -take only value from "Description du marché >>  CPV - Objet principal : " only

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV - Objet principal : ")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Informations pratiques >> Critères d'attribution
# Onsite Comment -ref url "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6361%22"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Informations pratiques >> Critères d'attribution
        # Onsite Comment -split and take all the criteia which are available in source

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attribution")]//following::li').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Informations pratiques >> Critères d'attribution
        # Onsite Comment -split and take all the criteia weight which are available in source

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d'attribution")]//following::li').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Numéro de référence :
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Numéro de référence :")]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Section 4 - Durée du marché ou délai
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Section 4 - Durée du marché ou délai")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass




    
    # Onsite Field -None
    # Onsite Comment -new format 3 https://www.boamp.fr/pages/avis/?q=idweb:%2224-6333%22 and https://www.boamp.fr/pages/avis/?q=idweb:%2224-6464%22 and to get more data click on "Voir l'annonce complète"

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet du marché :")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet du marché :
    # Onsite Comment -take only value from "L’essentiel du marché >> Objet du marché :"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet du marché :")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valeur estimée (H.T.)
    # Onsite Comment -take only value from "Identification du marché >> Valeur estimée (H.T.)" only  only

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur estimée (H.T.) :")]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valeur estimée (H.T.)
    # Onsite Comment -take only value from "Identification du marché >> Valeur estimée (H.T.)" only  only

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Valeur estimée (H.T.) :")]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de marché :
    # Onsite Comment -take only value from "Identification du marché >> Type de marché :" only and replace the following keywords with given respective keywords(Fournitures = Supply,Services = Service,Travaux =  Work)

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché :")]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de marché :
    # Onsite Comment -take only value from "Identification du marché >> Type de marché :" only

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché :")]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Adresse internet du profil d'acheteur :
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse internet du profil d'acheteur :")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date d'envoi du présent avis à la publication :
    # Onsite Comment -None

    try:
        dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),"Date d'envoi du présent avis à la publication :")]").text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durée du marché (en mois) :
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée du marché (en mois) :")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -click on "Voir l'annonce complète" to get data

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -org_name has same selector for every format as it is taken from tender_html_page

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification-info > ul > li:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Code postal :
        # Onsite Comment -None

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code postal :")]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ville :
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Ville :")]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Nom du contact :
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Nom du contact :")]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse mail du contact :
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse mail du contact :")]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'FR'
            customer_details_data.org_country = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -click on "Voir l'annonce complète" to get data

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            cpvs_data = cpvs()
        # Onsite Field -Code CPV principal - Descripteur principal
        # Onsite Comment -take only value from  Identification du marché >> Code CPV principal - Descripteur principal" only

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV principal - Descripteur principal")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -ref url:- https://www.boamp.fr/pages/avis/?q=idweb:%2224-6464%22 and take only values which is in "Section 5 - Lot " only

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
            lot_details_data = lot_details()
        # Onsite Field -Description du lot :
        # Onsite Comment -here take only eg:- "01 "

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Description du lot :")]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description du lot :
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Description du lot :")]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Estimation de la valeur hors taxes du lot :
        # Onsite Comment -None

            try:
                lot_details_data.lot_netbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimation de la valeur hors taxes du lot :")]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Estimation de la valeur hors taxes du lot :
        # Onsite Comment -None

            try:
                lot_details_data.lot_netbudget = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimation de la valeur hors taxes du lot :")]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Type de marché :
        # Onsite Comment -take only value from "Identification du marché >> Type de marché :" only and replace the following keywords with given respective keywords(Fournitures = Supply,Services = Service,Travaux =  Work)

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché :")]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Type de marché :
        # Onsite Comment -take only value from "Identification du marché >> Type de marché :" only

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché :")]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-container.fr-mb-15v'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Code(s) CPV additionnel(s) - Descripteur principal :
                    # Onsite Comment -take only value from "Section 5 - Lot >> Code(s) CPV additionnel(s) - Descripteur principal :" only

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code(s) CPV additionnel(s) - Descripteur principal :")]//following::span[1]').text
			
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
    
# Onsite Field -None
# Onsite Comment -attachments are same for all formats

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.fr-grid-row.fr-col-12.fr-col-sm-6'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -take file_name in textform

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.fr-grid-row.fr-col-12.fr-col-sm-6 > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.fr-grid-row.fr-col-12.fr-col-sm-6 > a').get_attribute('href')
            
        
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&refine.type_avis=5&refine.famille=FNS&refine.famille=MAPA&'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,22):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="toplist"]/li/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="toplist"]/li/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="toplist"]/li/div')))[records]
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
