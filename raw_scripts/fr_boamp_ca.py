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
SCRIPT_NAME = "fr_boamp_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'fr_boamp_ca'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -take local_title in textform

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification > h2 > p > a > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
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


    try:
        type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, " div.card-notification-info.fr-scheme-light-white.fr-p-5v.fr-mb-4w > ul > li:nth-child(4) > span.ng-binding").text
        notice_data.type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_ca_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass
    # Onsite Field -Voir l’annonce
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-container> div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -for notice text click on "Voir l'annonce" and take all data in notice txt
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button')))
        page_details.execute_script("arguments[0].click();",click)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.dg-notice-state > span')))
    except:
        pass
    
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
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
    
#     # Onsite Field -Type de marché :
#     # Onsite Comment -for notice_contract_type click on "Voir l'annonce" and  Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works ',' Fournitures = Supply')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH,  '//*[contains(text(),"Type de marché :")]//following::tr[1]').text
        if "Services" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Service"
        elif "Travaux" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Work"
        elif "Fournitures" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text
        if "Date d'envoi du présent avis à la publication :" in dispatch_date:
            dispatch_date = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
            dispatch_date = re.findall('\w+ \d+, \d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
# Onsite Field -ACHETEUR :
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        # Onsite Field -ACHETEUR :
        # Onsite Comment -None

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, ' li.fr-my-1v.fr-py-0 > span.ng-binding').text
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
        # Onsite Field -Descripteur principal :
        # Onsite Comment -for cpv code  click on "Voir l'annonce" and take data between "Descripteur principal :" and  "Type de marché :" and if cpv is available in detail pg then take numeric value and if the cpv is not available in detail pg then take auto cpv
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Descripteur principal :')]//following::tr[1]").text
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Objet du marché :
# Onsite Comment -take lots info from "Objet du marché :" if available

    try:              
        
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -Objet du marché :
        # Onsite Comment -split lot_title from "Objet du marché :"  eg : split between "lot 1-" and "lot 2-"

        try:
            lot_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Objet du marché :')]//following::span[1]").text
            lot_details_data.lot_title= GoogleTranslator(source='auto', target='en').translate(lot_title)
        except:
            lot_details_data.lot_title=notice_data.notice_title
        
        # Onsite Field -Objet du marché :
        # Onsite Comment -split lot_ description from "Objet du marché :"  eg : split between "lot 1-" and "lot 2-"

        try:
            lot_details_data.lot_description = lot_details_data.lot_title
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Type de marché :
        # Onsite Comment -for contract_type click on "Voir l'annonce" and Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works ',' Fournitures = Supply')

        try:
            lot_details_data.contract_type = notice_data.notice_contract_type
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass
        
        try: 
            bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').text
            if 'Nom du titulaire / organisme :' in bidder_name:
                award_details_data = award_details()
                award_details_data.bidder_name = bidder_name.split('Nom du titulaire / organisme :')[1].split('\n')[0]
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



# --------------------------------------------------------------------------------------------------------------------------------------------------------
#    -first_format reference_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6000%22" 
# ---------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # Onsite Field -None
    # Onsite Comment --first_format reference_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6000%22"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#toplist > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


            # Onsite Field -Section 1 - Reference de l'avis initial >> Annonce n°
    # Onsite Comment -split the data after "Annonce n" field

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '(//*[contains(text(),"Annonce n°")])[1]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Section 3 - Description du marché >> Objet du marché :
    # Onsite Comment -if local_title is missing from tender_html_page then grab the local_title from "Objet du marché :" field

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '(//div//*[contains(text(),"Objet du marché :")])[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
# Onsite Field -L’essentiel du marché
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(6) > div > div'):
            customer_details_data = customer_details()
        # Onsite Field -ACHETEUR :
        # Onsite Comment -split the data from html_page

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.card-notification-info > ul > li:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse :
        # Onsite Comment -split the data after "Adresse :" field

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Adresse :")])[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Téléphone :
        # Onsite Comment -split the data after "Téléphone :" fielde

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '( //*[contains(text(),"Téléphone :")])[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Courriel :
        # Onsite Comment -split the data after "Courriel :" field

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Courriel :")])[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse internet :
        # Onsite Comment -split the data after "Adresse internet :" fielde

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '(//*[contains(text(),"Adresse internet :")])[1]').text
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
    

    
# Onsite Field -Section 5 - Attribution(s) du marché
# Onsite Comment -ref_url ( without lot ) : (https://www.boamp.fr/pages/avis/?q=idweb:%2224-6000%22) , ref_url (with lot ) : https://www.boamp.fr/pages/avis/?q=idweb:%2224-6627%22

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(13)'):
            lot_details_data = lot_details()
        # Onsite Field -Section 5 - Attribution(s) du marché
        # Onsite Comment -lot available in "Section 5 - Attribution(s) du marché" section  , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6627%22"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '(//div//*[contains(text(),"Lot(s)")])').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Section 5 - Attribution(s) du marché >> Lot(s) 1
        # Onsite Comment -split the data between "Lot(s) 1 - " and "Détail de l'attribution" ,  ref_url (with lot ) : https://www.boamp.fr/pages/avis/?q=idweb:%2224-6627%22

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '(//div//*[contains(text(),"Section 5 - Attribution(s) du marché")])//following::div[2]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Section 5 - Attribution(s) du marché
        # Onsite Comment -ref_url (with lot ) : https://www.boamp.fr/pages/avis/?q=idweb:%2224-6627%22

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(13)'):
                    award_details_data = award_details()
		
                    # Onsite Field -Section 5 - Attribution(s) du marché >> Nom du titulaire / organisme :
                    # Onsite Comment -split the data between  "Nom du titulaire / organisme :"  and "Adresse :" , ref_url (with lot ) : https://www.boamp.fr/pages/avis/?q=idweb:%2224-6627%22

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '(//div//*[contains(text(),"Nom du titulaire / organisme :")])').text
			
                    # Onsite Field -Section 5 - Attribution(s) du marché >> Adresse
                    # Onsite Comment -split the data between "Adresse :" and "Montant (H.T.) : " , ref_url (with lot ) : https://www.boamp.fr/pages/avis/?q=idweb:%2224-6627%22

                    award_details_data.address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Détail de l'attribution")])//following::span[2]').text
			
                    # Onsite Field -Section 5 - Attribution(s) du marché >> Montant (H.T.) :
                    # Onsite Comment -split the data after "Montant (H.T.) :" , ref_url (with lot ) : https://www.boamp.fr/pages/avis/?q=idweb:%2224-6627%22

                    award_details_data.netawardvaluelc = page_details.find_element(By.XPATH, '(//div//*[contains(text(),"Montant (H.T.) :")])').text
			
                    # Onsite Field -Section 5 - Attribution(s) du marché >> Montant (H.T.) :
                    # Onsite Comment -split the data after "Montant (H.T.) :" , ref_url (with lot ) : https://www.boamp.fr/pages/avis/?q=idweb:%2224-6627%22

                    award_details_data.netawardvalueeuro = page_details.find_element(By.XPATH, '(//div//*[contains(text(),"Montant (H.T.) :")])').text
			
                    # Onsite Field -Section 5 - Attribution(s) du marché >> Montant (H.T.) :
                    # Onsite Comment -split the data after "Date d'attribution du marché : "

                    award_details_data.award_date = page_details.find_element(By.XPATH, '(//div//*[contains(text(),"Date d'attribution du marché :")])[1]').text
			
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
        




# --------------------------------------------------------------------------------------------------------------------------------------------------------
#    -second_format reference_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22"  , "https://www.boamp.fr/pages/avis/?q=idweb:%2224-5989%22" , "https://www.boamp.fr/pages/avis/?q=idweb:%2224-5983%22"
# ---------------------------------------------------------------------------------------------------------------------------------------------------------
   


    # Onsite Field -None
    # Onsite Comment --first_format reference_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6000%22"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#toplist > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Section 1 - Reference de l'avis initial >> Annonce n°
    # Onsite Comment -split the data after "Annonce n" field

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '(//*[contains(text(),"Annonce n°")])[1]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Section 3 - Identification du marché >> Intitulé du marché :
    # Onsite Comment -if local_title is not available in tender_html page then split the data from "Intitulé du marché : " field from detail_page

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '(//*[contains(text(),"Intitulé du marché :")])[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass  


            # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = '"CPV"'
    
    # Onsite Field -Section 3 - Identification du marché >> Type de marché :
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works',' Fournitures = Supply')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché :")]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description succincte du marché :")]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description succincte du marché :
    # Onsite Comment -split the data between "Description succincte du marché :" and "Critères d'attribution :" , ref_url : https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description succincte du marché :")]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass  
    
# Onsite Field -Section 2 - Identification de l'acheteur
# Onsite Comment -ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22" , "https://www.boamp.fr/pages/avis/?q=idweb:%2224-5989%22" , "https://www.boamp.fr/pages/avis/?q=idweb:%2224-5983%22"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(10)'):
            customer_details_data = customer_details()
        # Onsite Field -Acheteur :
        # Onsite Comment -split the data from html_page

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification-info > ul > li:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ville :
        # Onsite Comment -split the data after "Ville :" field

            try:
                customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, '(//*[contains(text(),"Ville ")])[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -postal_code
        # Onsite Comment -split the data after "postal_code" field

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '( //*[contains(text(),"Code postal :")])[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Courriel :
        # Onsite Comment -split the data after "Courriel :" field

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Courriel :")])[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresse internet :
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '(//*[contains(text(),"Adresse internet :")])[1]').text
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
        


    
# Onsite Field -Code CPV principal - Descripteur principal :
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Code CPV principal - Descripteur principal :")]'):
            cpvs_data = cpvs()
        # Onsite Field -Code CPV principal - Descripteur principal :
        # Onsite Comment -split the data after "Code CPV principal - Descripteur principal :" field

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV principal - Descripteur principal :")]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Code CPV principal - Descripteur principal :
    # Onsite Comment -split the data after "Code CPV principal - Descripteur principal :" field

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV principal - Descripteur principal :")]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    

    
  
    
# Onsite Field -Section 3 - Identification du marché >> Critères d'attribution :
# Onsite Comment -3 ref_url for tender_Criteria : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22","https://www.boamp.fr/pages/avis/?q=idweb:%2224-5983%22","https://www.boamp.fr/pages/avis/?q=idweb:%2224-5989%22"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -for following ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6040%22"   		                                                                                                   for ex. split the data between "Critères d'attribution :" and "40%" , also split the data between "40%" and "10%" ,and split the data between " 10%" and ":50%"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -for following ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6040%22"   		                                                                                                   for ex. split the data between " Valeur technique au vu des renseignements du 														   Cadre de Réponse Technique :" and "Mesures mise" , also split the data between "Mesures mise en oeuvre par le candidat pour répondre aux enjeux environnementaux et réduire l'empreinte carbone de son activité dans le cadre du présent marché :" and "Prix des prestations :" and split the data after "Prix des prestations :"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
        


    
# Onsite Field -Critères d'attribution :
# Onsite Comment -ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)'):
            tender_criteria_data = tender_criteria()
# Onsite Field -Critères d'attribution :
# Onsite Comment -ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -for following ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22"   		                                                                                                   for ex. split the data between "Critères d'attribution :" and "70 % :" , also  split the data between "70 Prix sur 30 points" and "(note sur 30) : 30"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -cmt : for following ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22"   		                                                                                                   for ex. split the data between "Valeur technique de l'offre :" and "Valeur 																technique" , split the data after "Analysés à partir du Devis Quantitatif Estimatif (Dqe) non contractuel, en cohérence avec les tarifs du Bordereau des Prix (note sur 30) :"

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
        

    
# Onsite Field -Critères d'attribution :
# Onsite Comment -ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6505%22"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -for following ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6505%22"   		                                                                                                   for ex. split the data between "Critères d'attribution :" and " 60%"

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Critères d'attribution :
        # Onsite Comment -cmt : for following ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6505%22"   		                                                                                                   for ex. split the data between " Valeur technique de l'offre :" and " Prix : "

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(12) > div:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
        
    
# Onsite Field -Section 4 - Attribution du marché
# Onsite Comment -ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6505%22"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)'):
            lot_details_data = lot_details()
        # Onsite Field -Section 3 - Identification du marché >> Type de marché :
        # Onsite Comment -notice_contract_type == lot contract_type

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché :")]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Marché n° :
        # Onsite Comment -split the data between "Marché n° :" and "Barde Sud Ouest" , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6040%22"

            try:
                lot_details_data.contract_number = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in contract_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Renseignements relatifs à l'attribution du marché et/ou des lots :
        # Onsite Comment -split the data between "Renseignements relatifs à l'attribution du marché et/ou des lots :" and "Terrassements" , ref_url "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6505%22"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Renseignements relatifs à l'attribution du marché et/ou des lots :
        # Onsite Comment -split the data between "Lot N°" and "Vrd Nombre d'offres reçues :" , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6505%22"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Renseignements relatifs à l'attribution du marché et/ou des lots :
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)'):
                    award_details_data = award_details()
		
                    # Onsite Field -Date d'attribution :
                    # Onsite Comment -split the data between "Date d'attribution :" and "Marché n°" , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6040%22"

                    award_details_data.award_date = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -split the data between "Pa2322" and "Ld Le Pestre,"   , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-604022"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -split the data between "Marché n° : " and "Montant Ht"  , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-604022"

                    award_details_data.address = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -split the data between "Montant Ht : " and "Euros "

                    award_details_data.netawardvalueeuro = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -split the data between "Montant Ht : " and "Euros "

                    award_details_data.netawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -cmt : split the data between "Montant annuel maxi :" and "Ht Voies de recours :"  , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22"

                    award_details_data.netawardvalueeuro = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -cmt : split the data between "Montant annuel maxi :" and "Ht Voies de recours :"  , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22"

                    award_details_data.netawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -cmt : split the data between "Montant annuel maxi :" and "Ht Voies de recours :"  , ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2224-6326%22"

                    award_details_data.netawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14) > div:nth-child(2)').text
			
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
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------




    
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
    urls = ['https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&refine.type_avis=10&refine.famille=MAPA&refine.famille=FNS'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,4):
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
    
