from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_marcheson_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium import webdriver
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "fr_marcheson_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global tnotice_count
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
    notice_data.document_type_description = 'Resultats :'
    notice_data.class_at_source = 'CPV'
    
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
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.noticeNumber > span').text.split(":")[1].strip()
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
    # Onsite Comment -Replace following keywords with given respective keywords ("Services = Services","Travaux de bâtiment = work","Etudes, Maîtrise d'oeuvre, Contrôle = Services","Fournitures = supply" ,"Travaux Publics = work")
    #("Services = Services","Travaux de bâtiment = work","Etudes, Maîtrise d'oeuvre, Contrôle = Services","Fournitures = supply" ,"Travaux Publics = work")
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'ul.colOne > li.activity').text
        if 'Services' in notice_contract_type or "Etudes, Maîtrise d'oeuvre, Contrôle" in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Travaux de bâtiment' in notice_contract_type or "Travaux Publics" in notice_contract_type :
            notice_data.notice_contract_type = 'Works'
        elif "Fournitures" in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass  
    # Onsite Field -None
    # Onsite Comment -format 1,

    try:
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'section.blockNotice  > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
             
    try:
        clk4 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="didomi-notice-agree-button"]')))
        page_details.execute_script("arguments[0].click();",clk4)
    except:
        pass
     
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div.colOne').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_text = WebDriverWait(page_details, 200).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div > div.colOne'))).text
    except:
        pass

#    format 1      url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"
# ----------------------------------------------------------------------------------------------------------------------------------------------------
    # Onsite Field -
    # Onsite Comment -format 1, split the data between "Type de marché :" and "Les éléments de mission de maitrise d'oeuvre sont :" field 
    if "Intitulé du marché" in notice_text:
        try:
            notice_data.local_description = notice_text.split("Description succincte du marché :")[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -Annonce N°
        # Onsite Comment -format 1,   split the data from "Section 1 :"

        try:
            notice_data.related_tender_id = notice_text.split("Section 1 :")[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass

        # Onsite Field -Date d'envoi du présent avis :
        # Onsite Comment -format 1, split the data from "Date d'envoi du présent avis : " field

        try:
            dispatch_date = notice_text.split("Date d'envoi du présent avis")[1].split("\n")[0]
            dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.dispatch_date)
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass

        # Onsite Field -Description succincte du marché :
        # Onsite Comment -format 1,   split the data from "Section 1 :"

        try:
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass

    # Onsite Field -Code CPV principal Descripteur principal :
    # Onsite Comment -format 1 ,   split the following data from "Code CPV principal Descripteur principal :" field

        try:
            cpvs_data = cpvs()
            cpv_record = notice_text.split("Descripteur principal :")[1].split("\n")[0].strip()
            if cpv_record =='':
                cpv_record = notice_text.split("Descripteur principal :")[1].split("\n")[1].strip()
                # Onsite Field -Code CPV principal :
                # Onsite Comment -data is in paragraph format split cpv where keyword "Code CPV principal" is available 
            cpv_code1 = re.findall('\d{8}',cpv_record)[0]
            cpvs_data.cpv_code = cpv_code1
            notice_data.cpv_at_source = cpv_code1
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass
        

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'p.clientName > span > a').text
    # Onsite Field -Ville :
    # Onsite Comment -format 1 , split the data between "N° National d'identification :" and "Code Postal :" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"
            try:
                customer_details_data.org_city = notice_text.split("Ville :")[1].split("\n")[0].strip()
                if customer_details_data.org_city =='':
                    customer_details_data.org_city = notice_text.split("Ville :")[1].split("\n")[1].strip()
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -Code Postal :
        # Onsite Comment -split the data between "Ville :" and "Groupement de commandes :" field , ref_url : "https://www.marchesonline.com/appels-offres/attribution/veloroute-sud-leman-maitrise-d-oeuvre/am-9062220-1"

            try:
                customer_details_data.postal_code = notice_text.split("Code Postal :")[1].split("\n")[0].strip()
                if customer_details_data.postal_code == '':
                    customer_details_data.postal_code = notice_text.split("Code Postal :")[1].split("\n")[1].strip()
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
            
            try:
                org_address = re.search(r'Montant Ht\s*()',notice_text).group()
                customer_details_data.org_address = notice_text.split(org_address)[0].split("\n")[-2]
            except:
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    
    # Onsite Field -Critères d'évaluation des projets :
    # Onsite Comment -format 1,   split the data from "Critères d'évaluation des projets" field
        try:              
            single_record = notice_text.split("Critères d'évaluation des projets : ")[1].split('%.')[0]
            for criteria in single_record.split('%'):
                tender_criteria_data = tender_criteria()
                tender_criteria_data.tender_criteria_title = criteria.split(':')[0].strip()
                if 'prix' in tender_criteria_data.tender_criteria_title.lower():
                    tender_criteria_data.tender_is_price_related = True
    
                tender_criteria_weight = criteria.split(':')[1].strip()
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
               
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
            pass
    # Onsite Field -Renseignements relatifs à l'attribution du marché et/ou des lots :
    # Onsite Comment -format 1, ref_url : "https://www.marchesonline.com/appels-offres/attribution/rehabilitation-de-22-logements-collectifs/am-9084101-1"
        try:              
            records_text = notice_text.split("Lot N°")
            lot_number = 1
            for single_record in records_text:
                
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type=notice_data.notice_contract_type
            # Onsite Field --Lot N° / Marché n° :
            # Onsite Comment -format 1, split  "Lot N°" from the given selector and here in some records split no which is below "Marché n° : 2023" for eg : take "/724" as lot_actual_number if it is not available then pass " Lot N° /  Lot" as lot_actual_number, ref_url : "https://www.marchesonline.com/appels-offres/attribution/rehabilitation-de-22-logements-collectifs/am-9084101-1"
                try:
                    lot_details_data.lot_title = single_record.split("-")[1].split("\n")[0].strip()
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except:
                    lot_details_data.lot_title = notice_data.local_title
                    notice_data.is_lot_default = True
                    lot_details_data.lot_title_english = notice_data.notice_title
                try:
                    lot_details_data.lot_actual_number = single_record.split("Marché n° :")[1].split("\n")[1].replace(":",'').strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -None
            # Onsite Comment -format 1, ref_url : "https://www.marchesonline.com/appels-offres/attribution/rehabilitation-de-22-logements-collectifs/am-9084101-1"

                try:
                    award = notice_text.split("Date d'attribution")
                    for single_record1 in award[1:]:
                        award_details_data = award_details()
                        # Onsite Field -None
                        # Onsite Comment -format 1,  split between from "Marché n° : " to "Montant Ht : " , ref_url : "https://www.marchesonline.com/appels-offres/attribution/rehabilitation-de-22-logements-collectifs/am-9084101-1"
                        # Onsite Field -Montant Ht :
                        # Onsite Comment -format 1, split the daat from  "Montant Ht :" field
                        bidder_name = re.search(r'Montant Ht\s*()',single_record1).group()
                        award_details_data.bidder_name = single_record1.split(bidder_name)[0].split(",")[0].split("\n")[-1]
                        try:
                            netawardvalueeuro = single_record1.split('Montant Ht :')[1].split("Euros")[0]
                            netawardvalueeuro = re.sub("[^\d\.\,]","",netawardvalueeuro)
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro.replace(',','.').strip())
                            award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                            notice_data.grossbudgetlc = award_details_data.netawardvaluelc
                            notice_data.grossbudgeteuro = award_details_data.netawardvaluelc
                        except:
                            pass

                        # Onsite Field -Date d'attribution :
                        # Onsite Comment -format 1, split award_date from selector and take from where lots are available
                        try:
                            award_date = single_record1.split("Date d'attribution :")[0].split('\n')[0]
                            award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
                
                if lot_details_data.lot_title is None and lot_details_data.award_details == []:
                    notice_data.lot_details = []
                elif lot_details_data.lot_title is None and lot_details_data.award_details != []:
                    lot_details_data.lot_title = notice_data.local_title
                    notice_data.is_lot_default = True
                    lot_details_data.lot_title_english = notice_data.notice_title
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
                elif lot_details_data.lot_title == '' and lot_details_data.award_details != []:
                    lot_details_data.lot_title = notice_data.local_title
                    lot_details_data.lot_title_english = notice_data.notice_title
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
                elif lot_details_data.lot_title is not None and lot_details_data.award_details != []:
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
                
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass


# format 2  url : "https://www.marchesonline.com/appels-offres/attribution/accord-cadre-de-coordination-architecturale-urbaine-et/am-9081928-1"
# -------------------------------------------------------------------------------------------------------------------------------------------    
    
    # Onsite Field -Adresse du profil d'acheteur :
    # Onsite Comment -format 2, split the additional_tender_url from "Adresse du profil d'acheteur :" field
    if "AVIS D'ATTRIBUTION DE MARCHE" in notice_text:
        try:
            notice_data.additional_tender_url = notice_text.split("Adresse du profil d'acheteur :")[1].split("\n")[0]
        except:
            try:
                notice_data.additional_tender_url = notice_text.split("Adresse du profil acheteur :")[1].split("\n")[0]
            except Exception as e:
                logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
                pass
        # Onsite Field -II.1.1) Intitulé
        # Onsite Comment -format 2,  split the related id from "II.1.1) Intitulé " field , here split only "Numéro de référence : M2023-005" value
        try:
            notice_data.related_tender_id = notice_text.split('Numéro de référence :')[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass

    #       Onsite Field -IV.1.1) Type de procédure
    #     Onsite Comment -split the data from "IV.1.1) Type de procédure" field
        try:
            notice_data.type_of_procedure_actual = notice_text.split('Type de procédure')[1].split("\n")[1].replace(":",'').strip()
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcheson_ca_procedure.csv",type_of_procedure)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

        try:
            notice_data.local_description = notice_text.split("Description succincte :")[1].split("II.1.6) Information sur les lots")[0]
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        # Onsite Field -II.1.4) Description succincte :
        # Onsite Comment -format 2,  split the notice_summary_english from "II.1.4) Description succincte" field
        try:
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass
    #     Onsite Field -II.1.7) Valeur totale finale du marché (hors TVA)
    #     Onsite Comment -format 2,  split the data from "II.1.7) Valeur totale finale du marché (hors TVA)" field
        try:
            if 'Valeur totale finale du marché (hors TVA) :' in notice_text:
                try:
                    netbudgetlc = notice_text.split('Valeur totale finale du marché (hors TVA) :')[1].split("\n")[0].strip()
                except:
                    pass
            elif 'Valeur totale finale du marché (hors TVA)' in notice_text:
                try:
                    netbudgetlc = notice_text.split('Valeur totale finale du marché (hors TVA)')[1].split("\n")[1].replace(":",'').strip()
                except:
                    pass
            elif 'Valeur totale du marché (hors TVA) :' in notice_text:
                try:
                    netbudgetlc = notice_text.split(" Valeur totale du marché (hors TVA) :")[1].split("\n")[1].strip()
                except:
                    pass
            netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
            notice_data.netbudgetlc = float(netbudgetlc.strip())
            notice_data.netbudgeteuro = notice_data.netbudgetlc
            notice_data.est_amount = notice_data.netbudgetlc
        except Exception as e:
            logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
            pass
    #     Onsite Field -VI.5) Date d'envoi du présent avis :
    #     Onsite Comment -format 2,  split the following data from "VI.5) Date d'envoi du présent avis :" field
        try:
            try:
                dispatch_date = notice_text.split("Date d'envoi du présent avis ")[1].split("\n")[0]
            except:
                try:
                    dispatch_date = notice_text.split("Date d'envoi du présent avis ")[1]
                except:
                    pass
            dispatch_date = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
            dispatch_date = re.findall('\w+ \d+, \d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.dispatch_date)
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass
    #     Onsite Field -None
    #     Onsite Comment -format 2, split the customer_Details from detail_page

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'p.clientName > span > a').text
            customer_details_data.org_language = 'FR'
        # Onsite Field -Client :
        # Onsite Comment -format 2,   split the org_name from "Client :" field

        # Onsite Field -I.1) Nom et adresses
        # Onsite Comment -format 2 , split the org_address from "I.1) Nom et adresses" field
            try:
                customer_details_data.org_address = notice_text.split("Nom et adresses :")[1].split("courriel :")[0]
            except:
                try:
                    customer_details_data.org_address = notice_text.split("NOM ET ADRESSES")[1].split("courriel :")[0]
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass
#         Onsite Field -Code NUTS
#         Onsite Comment -format 2,  split the data from "Code NUTS " field till "Adresse(s) internet"
            try:
                customer_details_data.customer_nuts = notice_text.split("Code NUTS :")[1].split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        # Onsite Field -I.4) Type de pouvoir adjudicateur
        # Onsite Comment -format 2,  split the data from "I.4) Type de pouvoir adjudicateur" field
            try:
                if 'I.4) Type de pouvoir adjudicateur :' in notice_text:
                    customer_details_data.type_of_authority_code = notice_text.split('I.4) Type de pouvoir adjudicateur :')[1].split("\n")[0].strip()
                elif "Type de pouvoir adjudicateur" in notice_text:
#                     if customer_details_data.type_of_authority_code =='':
                    customer_details_data.type_of_authority_code = notice_text.split('Type de pouvoir adjudicateur')[1].split("\n")[1].replace(":",'').strip()
                else:
                    customer_details_data.type_of_authority_code = notice_text.split('TYPE DE POUVOIR ADJUDICATEUR')[1].split("\n")[1].strip()
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
#         Onsite Field -I.5) Activité principale
#         Onsite Comment -format 2,  split the data from "I.5) Activité principale" field
            try:
                if 'I.5) Activité principale :' in notice_text:
                    customer_details_data.customer_main_activity = notice_text.split('I.5) Activité principale :')[1].split("\n")[0].strip()
                elif 'Activité principale' in notice_text:
                    customer_details_data.customer_main_activity = notice_text.split('Activité principale')[1].split("\n")[1].strip()
                else:
                    customer_details_data.customer_main_activity = notice_text.split('ACTIVITÉ PRINCIPALE')[1].split("\n")[1].strip()
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass                 

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse(s) internet")]//following::a[1]').text
            except:
                try:
                    customer_details_data.org_website = notice_text.split('Adresse(s) internet :')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass
         
        # Onsite Field -courriel
        # Onsite Comment -format 2,   split the following data from "courriel :" field , for ex. "courriel : Contact@lafab-bm.fr" , here split only "Contact@lafab-bm.fr"       
            try:
                org_email = notice_text.split("courriel :")[1].split(",")[0].strip()
                email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
                customer_details_data.org_email = email_regex.findall(org_email)[0]
            except:
                try:
                    org_email = notice_text.split("courriel :")[1].split("\n")[0].strip()
                    email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
                    customer_details_data.org_email = email_regex.findall(org_email)[0]
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
        # Onsite Field -II.1.2) Code CPV principal
        # Onsite Comment -format 2, split the following data from "II.1.2) Code CPV principal" fiel
            cpv_code = notice_text.split('Code CPV principal')[1].split("II.1.3) Type de marché :")[0]
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass
        
        try:
            cpv_at_source = notice_text.split('Code CPV principal')[1].split("II.1.3) Type de marché :")[0]
            cpv_at_source  = re.findall('\d{8}',cpv_at_source)[0]
            notice_data.cpv_at_source  = cpv_at_source
        except:
            pass

        try:
            tender_criteria_data = notice_text.split("Critères d'attribution")[1].split("II.2.11) Information sur les options")[0].strip()
            tender_criteria_data = tender_criteria_data.split('\n')
            for each_criteria in tender_criteria_data:
                if 'Pondération' in each_criteria or 'VALEUR TECHNIQUE' in each_criteria:
                    tender_criteria_data = tender_criteria()
                    try:
                        tender_criteria_data.tender_criteria_title = each_criteria.split('/ Pondération')[0].strip()
                        tender_criteria_data.tender_criteria_weight = int(each_criteria.split(':')[1].strip())
                    except:
                        try:
                            tender_criteria_title = each_criteria.split('/ Pondération')[0].replace("-",'').strip()
                            tender_criteria_data.tender_criteria_title = tender_criteria_title.split(':')[0]
                            tender_criteria_data.tender_criteria_weight = int(each_criteria.split(':')[1].strip())
                        except:
                            pass

                    if 'Prix' in each_criteria or 'PRIX' in each_criteria or 'prix' in each_criteria:
                        tender_criteria_data.tender_is_price_related  = True
                    
                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
                elif 'technique' in each_criteria.lower():
                    tender_criteria_data = tender_criteria()
                    tender_criteria_data.tender_criteria_title = 'technique'
                    tender_criteria_data.tender_criteria_weight = int(each_criteria.split('/ Pondération :')[1].strip())
                    if 'Prix' in each_criteria or 'PRIX' in each_criteria or 'prix' in each_criteria:
                        tender_criteria_data.tender_is_price_related  = True

                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
            pass

        # Onsite Field -II.2.13) Information sur les fonds de l'Union européenne
        # Onsite Comment -if in below text written as " Le contrat s'inscrit dans un projet/programme financé par des fonds de l'Union européenne : non. " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT	" "II.2.13) Information sur les fonds de l'Union européenne :  >  Le contrat s'inscrit dans un projet/programme financé par des fonds de l'Union européenne : non. " if the abve  text written as "  Le contrat s'inscrit dans un projet/programme financé par des fonds de l'Union européenne : YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

        try:
            try:
                funding_agency = notice_text.split("Information sur les fonds de l'Union européenne")[1].split("\n")[2]
            except:
                try:
                    funding_agency = notice_text.split("Information sur les fonds de l'Union européenne")[1].split("\n")[1]
                except:
                    funding_agency = notice_text.split("V.2.5) Information sur la sous-traitance :")[1].split("\n")[1]
            funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
            if 'yes' in funding_agency or "Yes" in funding_agency:
                funding_agencies_data = funding_agencies()
                funding_agencies_data.funding_agency = 1344862
                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
        except Exception as e:
            logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
            pass
        
        try:
            lot_number = 1
            if 'II.2) DESCRIPTION' in notice_text:
                lot_record = notice_text.split("II.2) DESCRIPTION")
            else:
                lot_record = notice_text.split("II.2) Description")

            for single_record in lot_record:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_details_data.lot_contract_type_actual=notice_data.contract_type_actual
                lot_details_data.contract_type=notice_data.notice_contract_type
            # Onsite Field -Marché n°
            # Onsite Comment -format 2, split the following data from "Marché n°" field

                try:
                    lot_details_data.lot_actual_number = single_record.split("Intitulé :")[1].split("\n")[1].strip()
                except:
                    try:
                        lot_details_data.lot_actual_number = single_record.split("Marché nº :")[1].split("\n")[0].strip()
                    except Exception as e:
                        logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                        pass
                
                try:
                    lot_details_data.lot_title = single_record.split("Intitulé :")[1].split("\n")[0].strip()
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except:
                    pass
                    
                    
                try:
                    lot_c = single_record.split("Critère(s) de qualité :")[1].split("II.2.11) Information sur les options :")[0]
                    lots_c = lot_c.split("\n")
                    for lc in lots_c[1:]:
                        lot_criteria_data = lot_criteria()
                        if 'valeurs techniques' in lc.lower():
                            lot_criteria_data.lot_criteria_title = 'VALEURS TECHNIQUES'
                        elif 'prix' in lc.lower():
                            lot_criteria_data.lot_criteria_title = 'Prix'
                            lot_criteria_data.lot_is_price_related = True
                        lot_criteria_data.lot_criteria_weight=int(re.findall('\d{2}',lc)[0])
                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
                except:
                    pass
            
                try:
                    lot_details_data.lot_nuts = single_record.split("Code NUTS :")[1].split("\n")[0].strip()
                except:
                    pass

                try:
                    lot_cpv_at = single_record.split("II.2.2) Code(s) CPV additionnel(s) :")[1].split("II.2.3) Lieu d'exécution")[0]
                    cpvss1 = re.findall('\d{8}',lot_cpv_at)[0]
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = cpvss1
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_class_codes_at_source="CPV"

                try:
                    lot_cpv_at = single_record.split("II.2.2) Code(s) CPV additionnel(s) :")[1].split("II.2.3) Lieu d'exécution")[0]
                    lot_cpv_at1 =re.findall('\d{8}',lot_cpv_at)[0]
                    lot_details_data.lot_cpv_at_source = lot_cpv_at1
                except:
                    pass
    #     #         Onsite Field -V.2) Attribution du marché
    #         Onsite Comment -format 2,
                try:  
#                     award_detail = single_record.split("Nom et adresse du titulaire")
                    award_detail = single_record.split("V.2) Attribution du marché")
                    for single_record in award_detail[1:]:
                        award_details_data = award_details()
                        # Onsite Field -V.2.1) Date de conclusion du marché
                        # Onsite Comment -format 2, split the following data from "V.2.1) Date de conclusion du marché" field
                        try:
                            award_date1 = re.search(r'Date de conclusion du marché : \s*(\w+ \w+ \w+)',single_record).group(1)
                            award_date2 = GoogleTranslator(source='auto', target='en').translate(award_date1)
                            award_date = re.findall('\w+ \d+, \d{4}',award_date2)[0]
                            award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
                        except:
                            pass

                        # Onsite Field -V.2.3) Nom et adresse du titulaire
                        # Onsite Comment -format 2, split the bidder_name from "V.2.3) Nom et adresse du titulaire" field
                        award_details_data.bidder_name = single_record.split(",")[0].split("\n")[1].strip()
                        if 'Partager' in award_details_data.bidder_name:
                            award_details_data.bidder_name = notice_text.split("Nom et adresse du titulaire")[1].split(",")[0].replace(":",'').strip()
                        # Onsite Field -V.2.3) Nom et adresse du titulaire
                        # Onsite Comment -format 2, split the address from "V.2.3) Nom et adresse du titulaire" field
                        try:
                            award_details_data.address = single_record.split(",")[1]
                        except:
                            pass
                        # Onsite Field -V.2.4) Informations sur le montant du marché/du lot (hors TVA)
                        # Onsite Comment -format 2, split the data from "V.2.4) Informations sur le montant du marché/du lot (hors TVA)" field
                        try:
                            netawardvalueeuro = single_record.split("Valeur totale du marché/du lot :")[1].split("\n")[0]
                            netawardvalueeuro = re.sub("[^\d\.\,]", "",netawardvalueeuro)
                            award_details_data.netawardvalueeuro = float(netawardvalueeuro)
                            notice_data.netbudgeteuro = award_details_data.netawardvalueeuro
                        except:
                            pass
    #                     Onsite Field -V.2.4) Informations sur le montant du marché/du lot (hors TVA)
    #                     Onsite Comment -format 2, split the data from "V.2.4) Informations sur le montant du marché/du lot (hors TVA)" field
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass

                if lot_details_data.lot_title is None and lot_details_data.award_details == []:
                    notice_data.lot_details = []
                elif lot_details_data.lot_title is None and lot_details_data.award_details != []:
                    lot_details_data.lot_title = notice_data.local_title
                    lot_details_data.lot_title_english = notice_data.notice_title
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
                elif lot_details_data.lot_title == '' and lot_details_data.award_details != []:
                    lot_details_data.lot_title = notice_data.local_title
                    lot_details_data.lot_title_english = notice_data.notice_title
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
                elif lot_details_data.lot_title is not None and lot_details_data.award_details != []:
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

# format 3   url="https://www.marchesonline.com/appels-offres/attribution/travaux-de-demolition-et-desamiantage-rue-jules-uhr/am-9082868-1"
# ----------------------------------------------------------------------------------------------------------------------------------------------------
#         Onsite Field -Type de procédure
#         Onsite Comment -split the data from "Type de procédure" field
    
    if "Nom et adresse officiels de l'organisme acheteur" in notice_text:
        try:
            notice_data.type_of_procedure_actual = notice_text.split("Type de procédure :")[1].split("\n")[0]
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcheson_ca_procedure.csv",type_of_procedure)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'p.clientName > span > a').text
        # Onsite Field -Client
        # Onsite Comment -format 3
        # Onsite Field -Nom et adresse officiels de l'organisme acheteur :
        # Onsite Comment -format 3 , split  "Nom et adresse officiels de l'organisme acheteur : from the given selector
            try:
                customer_details_data.org_address = notice_text.split("Nom et adresse officiels de l'organisme acheteur :")[1].split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

#             Onsite Field -Nom et adresse officiels de l'organisme acheteur :
#             Onsite Comment -format 3 ,
    
            try:
                org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Nom et adresse officiels de l")]//following::a').text
                if 'www.' in org_website:
                    customer_details_data.org_website = org_website
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            tender_c1 = notice_text.split("Critères d'attributions retenus :")[1].split("Type de procédure : ")[0]
            tender_c = tender_c1.split("\n")
            for criteria in tender_c[:-2]:
                tender_criteria_data = tender_criteria()
                if 'valeur technique' in criteria.lower():
                    tender_criteria_data.tender_criteria_title = 'VALEURS TECHNIQUES'
                elif 'prix' in criteria.lower():
                    tender_criteria_data.tender_criteria_title = 'Prix'
                    tender_criteria_data.tender_is_price_related = True
                tender_criteria_data.tender_criteria_weight=int(re.findall('\d{2}',criteria)[0])
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
        except:
            pass
        
        try:
            grossbudgetlc = lot.split('Montant mini/maxi annuel :')[1].split("/")[1]
            grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)
            notice_data.grossbudgetlc = float(grossbudgetlc)
        except:
            pass

        # Onsite Field -None
        # Onsite Comment -format 3 ,  if lot_details are not available then pass local_title to lot_title
        try:
            try:
                lot_text1 = notice_text.split('Attribution des marchés ou des lots :')[1].split("Autres informations :")[0]
                lot_text = lot_text1.split("\n")
            except:
                lot_text = notice_text.split('Attribution du lot :')
            lot_number = 1
            for lot in lot_text[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                try:
                    lot_details_data.lot_actual_number = re.search(r'LOT \s*(\d+)',lot).group()
                except:
                    try:
                        lot_details_data.lot_actual_number = re.search(r'Lot\(s\) \d+',lot).group()
                    except:
                        pass

                if lot_details_data.lot_actual_number is not None and lot_details_data.lot_actual_number in lot:
                    lot_details_data.lot_title = lot.split(lot_details_data.lot_actual_number)[1].replace(":",'').strip()
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                else:
                    lot_details_data.lot_number = 1
                    lot_details_data.lot_title = notice_data.local_title
                    lot_details_data.lot_title_english = notice_data.notice_title
                    
                try:
                    lot_details_data.lot_contract_type_actual=notice_data.contract_type_actual
                    lot_details_data.contract_type=notice_data.notice_contract_type
                except:
                    pass

                try:
                    lot_grossbudget_lc = lot.split('Montant mini/maxi annuel :')[1].split("/")[1]
                    lot_grossbudget_lc = re.sub("[^\d\.\,]", "", lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                except:
                    pass

                try:
                    bidder_name = re.search(r'Titulaire du \s*(\w+) :',single_record).group()
                except:
                    bidder_name = notice_text.split("Autres informations :")

                for single_record in bidder_name[1:]:
                    award_details_data = award_details()
                # Onsite Field -Titulaire du marché :
                # Onsite Comment -format 3 , split the data from "Titulaire du marché :" field
                    try:
                        award_details_data.bidder_name = single_record.split("Lot 1 -")[1].split("Marché n o")[0]
                    except:
                        award_details_data.bidder_name = single_record.split("\n")[0].strip()
                # Onsite Field -Date d'attribution :
                # Onsite Comment -format 3 , split the data from "Date d'attribution : " field
                    try:
                        award_date = single_record.split("Date d'attribution :")[1].split("\n")[0]
                        award_date = GoogleTranslator(source='auto', target='en').translate(award_date)
                        award_date = re.findall('\w+ \d+, \d{4}',award_date)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
                    except:
                        pass

                    try:
                        num = re.search(r'Montant du marché ou niveau des offres : \s*()',single_record).group()
                        if num in single_record:
                            netawardvaluelc1 = single_record.split(num)[1].split("euro(s)")[0]
                            netawardvaluelc = re.sub("[^\d\.\,]", "", netawardvaluelc1)
                            award_details_data.netawardvaluelc = float(netawardvaluelc)
                            award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                    except:
                        pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except:
            pass
#             
# format 4 url : "https://www.marchesonline.com/appels-offres/attribution/enquete-epale-portant-sur-les-utilisateurs-de-la-plate/am-9082079-/1"
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # Onsite Field -Référence d'identification du marché qui figure dans l'appel d'offres
    # Onsite Comment -format 4, split the data from "Référence d'identification du marché qui figure dans l'appel d'offres" field
    if 'Autres informations' in notice_text:
        try:
            notice_data.related_tender_id = notice_text.split("Référence d'identification du marché qui figure dans l'appel d'offres : ")[1].split("\n")[0].split(".")[0].strip()
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
        # Onsite Field -Date d'envoi du présent avis à la publication :
        # Onsite Comment -format 4, split the following data from "Date d'envoi du présent avis à la publication : " field
        try:
            dispatch_date = notice_text.split("Date d'envoi du présent avis ")[1].split("\n")[0]
            dispatch_date = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
            dispatch_date = re.findall('\w+ \d+, \d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
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

#         Onsite Field -Type de procédure
#         Onsite Comment -split the data from "Type de procédure" field                                                
        try:
            notice_data.type_of_procedure_actual = notice_text.split("Type de procédure :")[1].split("\n")[0].strip()
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marcheson_ca_procedure.csv",type_of_procedure)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass    

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
        # Onsite Field -Client
        # Onsite Comment -format 4, split the data from "Client" field
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'p.clientName > span > a').text
        # Onsite Field -Official name and address of the purchasing organization:
        # Onsite Comment -format 4, split the data from  "Nom et adresse officiels de l'organisme acheteur" field
            try:
                customer_details_data.org_address = notice_text.split("Nom et adresse officiels de l'organisme acheteur :")[1].split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
#             Onsite Field -courriel :
#             Onsite Comment -format 4, split the data from  "Nom et adresse officiels de l'organisme acheteur" field
            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div > span.jqMailto').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        # Onsite Field -Correspondant :
        # Onsite Comment -format 4, split the data from  "Nom et adresse officiels de l'organisme acheteur" field
            try:
                customer_details_data.contact_person = notice_text.split("Correspondant :")[1].split(",")[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass


        try:              
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -format 4, if lot_details are not available then pass local_title to lot_title
            lot_details_data.lot_title = notice_data.local_title
            lot_details_data.lot_title_english = notice_data.notice_title
            lot_details_data.lot_number = 1
            
            lot_details_data.lot_contract_type_actual=notice_data.contract_type_actual
            lot_details_data.contract_type=notice_data.notice_contract_type
        # Onsite Field -None
        # Onsite Comment -format 4,

            award_details_data = award_details()
            # Onsite Field -Nom du titulaire / organisme :
            # Onsite Comment -format 4, split the bidder_name from "Nom du titulaire / organisme :" fiel
            award_details_data.bidder_name = notice_text.split("Nom du titulaire / organisme :")[1].split(",")[0]
            # Onsite Field -Montant (H.T.) :
            # Onsite Comment -format 4, split the data from "Montant (H.T.) :" field
            try:
                netawardvalueeuro =notice_text.split("Montant (H.T.) :")[1].split("euros.")[0].strip()
                netawardvalueeuro = re.sub("[^\d\.\,]","",netawardvalueeuro)
                award_details_data.netawardvalueeuro =float(netawardvalueeuro.replace(',','.').strip())
                award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
            except:
                pass

                # Onsite Field -Date d'attribution du marché :
                # Onsite Comment -format 4, split the following data from "Date d'attribution du marché :" field

            try:                                                       
                award_date = notice_text.split("Date d'attribution du marché ")[1].split("\n")[0]
                award_date = GoogleTranslator(source='auto', target='en').translate(award_date)
                award_date = re.findall('\w+ \d+, \d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
            except:
                pass                                                


            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
        
        # Onsite Comment -format 5
#  ref url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"
# -----------------------------------------------------------------------------------------------------------------------------------------------------
# Onsite Comment -format 5
    if 'Référence acheteur :' in notice_text:
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'p.clientName > span > a').text
        # Onsite Field -None
        # Onsite Comment -format 5, for address split the data between "Directeur Général" and "Tél" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"
            try:
                org_address = notice_text.split("Tél.")[0].split(",")[1:]
                customer_details_data.org_address = ''.join(org_address)
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.org_fax = notice_text.split("Fax :")[0].split(",")[1].strip()
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        # Onsite Field -Tél. :
        # Onsite Comment -format 5, for org_phone split the data between "Tél. :" and "mèl :" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"
            try:
                customer_details_data.org_phone = notice_text.split("Tél. : ")[1].split("\n")[0].split(",")[0].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        # Onsite Field -mèl :
        # Onsite Comment -format 5, for org_mail split the data between "mèl :" and " web :" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"
            try:
                customer_details_data.org_email = notice_text.split("mèl :")[1].split(",")[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        # Onsite Field -web
        # Onsite Comment -format 5, for org_website split the data between "web " and "Siret" field, ref_url : "https://www.marchesonline.com/appels-offres/attribution/construction-de-49-logements-et-commerces-49-a-57-rue/am-9087994-1"
            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div.contenuIntegral.borderBottom > div.surbrillance_1 > a').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

# Onsite Field -None
# Onsite Comment -format 5 ,

        try:              
            cpvs_data = cpvs()
        # Onsite Field -Classification CPV :
        # Onsite Comment -format 5 , split only cpvs for ex. "Principale : 45210000 travaux de construction de bâtiments" , here split only "45210000"
            cpv_code = notice_text.split("Classification CPV :")[1].split("\n")[0]
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]     

            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass

        try:
            cpv_code = notice_text.split("Classification CPV :")[1].split("\n")[0]
            notice_data.cpv_at_source = re.findall('\d{8}',cpv_code)[0]
        except:
            pass
# Onsite Field -None
# Onsite Comment -format 5
        try:
            lot_text =  notice_text.split("Marché n° :")
            for lot_detail in lot_text[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_title = notice_data.local_title
                lot_details_data.lot_title_english = notice_data.notice_title
                lot_details_data.lot_number = 1
                
                lot_details_data.lot_contract_type_actual=notice_data.contract_type_actual
                lot_details_data.contract_type=notice_data.notice_contract_type
            # Onsite Field -Marché n° :
            # Onsite Comment -format 5 , split the following data from "Marché n° :" field
                try:
                    lot_details_data.lot_actual_number = lot_detail.split("\n")[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                award_text = lot_detail.split("Marché n° :")
                for award in award_text[0:]:
                    award_details_data = award_details()
                    # Onsite Field -None
                    # Onsite Comment -format 5 , split the data between "Marché n° :" and "Montant HT " field , it is identified there are multiple bidders, take all specified bidders
                    award_details_data.bidder_name = award.split("\n")[1].split(",")[0].strip()

                    # Onsite Field -None
                    # Onsite Comment -format 5 , split only address , and split the data  between "Marché n° :" and "Montant HT " field
                    try:
                        address = award.split("\n")[1].split("\n")[0].split(",")[0]
                        award_details_data.address = l.split("\n")[1].split("\n")[0].replace(address+',','')
                    except:
                        pass

                    # Onsite Field -Montant HT :
                    # Onsite Comment -format 5 , split the following data from "Montant HT :" field
                    try:
                        netawardvalueeuro = award.split("Montant HT :")[1].split("\n")[0].strip()
                        netawardvalueeuro = re.sub("[^\d\.\,]","",netawardvalueeuro)
                        award_details_data.netawardvalueeuro =float(netawardvalueeuro.replace(',','.').strip())
                        award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                    except:
                        pass

                    # Onsite Field -Date d'attribution :
                    # Onsite Comment -format 5 , split the following data from "Date d'attribution :" field
                    try:
                        award_date = award.split("Date d'attribution : ")[1].split("\n")[0]
                        award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                    except:
                        pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
             
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    # Onsite Field -Valeur totale du marché (hors TVA) :
    # Onsite Comment -format 5, split the following data from "Valeur totale du marché (hors TVA) :" field

        try:
            netbudgetlc = notice_text.split("Valeur totale du marché (hors TVA) :")[1].split('euros')[0]
            netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
            notice_data.netbudgetlc = float(netbudgetlc.strip())
            notice_data.netbudgeteuro = notice_data.netbudgetlc
            notice_data.est_amount = notice_data.netbudgetlc
        except Exception as e:
            logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
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
            dispatch_date = notice_text.split("Envoi")[1].split("\n")[0]
            dispatch_date = re.findall('\d+/\d+/\d{2}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.dispatch_date)
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass    
        
    if notice_data.customer_details == []:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'p.clientName > span > a').text
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
page_main = webdriver.Chrome(options=options)
time.sleep(20)
 
options = webdriver.ChromeOptions()
page_details = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.marchesonline.com/appels-offres/en-cours#id_ref_type_recherche=1&id_ref_type_avis=2&statut_avis%5B%5D=2'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            clk2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="didomi-notice-agree-button"]')))
            page_main.execute_script("arguments[0].click();",clk2)
        except:
            pass
        
        try:
            clk3 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="id_ref_type_avis_2"]')))
            page_main.execute_script("arguments[0].click();",clk3)
        except:
            pass
        try:
            for page_no in range(2,50):
                logging.info(page_no)
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.blockResults section'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.blockResults section')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.blockResults section')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                    if notice_count == 50:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.blockResults section'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
                
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
