from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_boamp_ted_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_boamp_ted_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'fr_boamp_ted_ca'
    notice_data.main_language = 'FR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.notice_type = 7
    notice_data.procurement_method = 2
    notice_data.class_at_source = 'CPV'  
    
    # Onsite Field -Avis n°
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-grid-row > div.fr-checkbox-group > label').text.split('Avis n° ')[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publié le
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.fr-grid-row > span").text
        publish_date = GoogleTranslator(source='fr', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
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
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.fr-mb-4w > ul > li:nth-child(4) > span.ng-binding").text
        type_of_procedure = GoogleTranslator(source='fr', target='en').translate(notice_data.type_of_procedure_actual).lower()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_ted_ca_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Voir l’annonce
    # Onsite Comment -inspect url for detail page , url ref ="https://www.boamp.fr/pages/avis/?q=idweb:%2223-136872%22"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.fr-container.fr-container--fluid > div > a').get_attribute("href")                     
    except:
        pass
    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Acheteur(s) ')]")))
        
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Objet du marché : ')]//parent::li").text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except:
            pass
        # Onsite Field -Adresse internet du profil d'acheteur :
        # Onsite Comment -None

        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, '''//*[contains(text(),"Adresse internet du profil d'acheteur :")]//following::a[1]''').text
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass

        # Onsite Field -Liens vers les avis initiaux : Avis de marché :
        # Onsite Comment -take only in text format and split only related_id for ex. "Référence : 23-65912" , here split only "23-65912"

        try:
            notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Avis de marché")]//following::a[1]').text.split('Référence : ')[1].strip()
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass 

        try:
            org_address_1 = page_details.find_element(By.XPATH, "//*[contains(text(),'Adresse :')]//parent::li").text.split('Adresse :')[1].strip()
        except Exception as e:
            logging.info("Exception in org_address_1: {}".format(type(e).__name__))
            pass

        try:
            org_phone_1 = page_details.find_element(By.XPATH, "(//li/*[contains(text(),'Téléphone :')])//parent::li").text 
            org_phone_1 = re.findall('\d+',org_phone_1)[0]

        except Exception as e:
            logging.info("Exception in org_phone_1: {}".format(type(e).__name__))
            pass

        try:
            org_email_1 = page_details.find_element(By.XPATH, "(//*[contains(text(),'Courriel :')])[1]//parent::li").text.split('Courriel :')[1].strip()
        except Exception as e:
            logging.info("Exception in org_email_1: {}".format(type(e).__name__))
            pass

        try:
            org_website_1 = page_details.find_element(By.XPATH, "(//*[contains(text(),'Adresse internet :')])[1]//following::a[1]/span").text
        except Exception as e:
            logging.info("Exception in org_website_1: {}".format(type(e).__name__))
            pass

        try:
            contact_person_1 = page_details.find_element(By.XPATH, "//*[contains(text(),'Point(s) de contact : ')]//parent::li").text.split('contact : ')[1]
        except Exception as e:
            logging.info("Exception in contact_person_1: {}".format(type(e).__name__))


        Voir_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="toplist"]/div/div/div/div[6]/div/div[1]/button')))
        page_details.execute_script("arguments[0].click();",Voir_clk)
        time.sleep(5)
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Section 1')]")))
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="toplist"]/div/div/div').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass

        notice_text = page_details.find_element(By.XPATH, '//*[@id="toplist"]/div/div/div').text

        # Onsite Field -II.1.3)Type de marché
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and grabbed the data from "II.1.3)Type de marché" field

        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché")]//following::td[3]').text
            if 'Services' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Service'
            elif 'Travaux' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Works'
            elif 'Fournitures' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Supply'
            else:
                pass
        except:
            try:
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Nature du marché")]//following::span[2]').text
                if 'Services' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Service'
                elif 'Travaux' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works'
                elif 'Fournitures' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
                pass    

        # Onsite Field -II.1.7)Valeur totale du marché (hors TVA) :
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and  take the value from  "II.1.7)Valeur totale du marché (hors TVA) :" field

        try:
            netbudgetlc = page_details.find_element(By.XPATH, "(//*[contains(text(),'Valeur totale du marché')])[1]//following::td[3]").text
            netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
            notice_data.netbudgetlc = float(netbudgetlc.replace(',','.').strip())
            notice_data.netbudgeteuro = notice_data.netbudgetlc
            notice_data.est_amount = notice_data.netbudgetlc
        except:
            try:
                netbudgetlc = page_details.find_element(By.XPATH, "//*[contains(text(),'Valeur estimée hors TVA')]//following-sibling::span[2]").text
                netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
                notice_data.netbudgetlc = float(netbudgetlc.replace(',','').strip())
                notice_data.netbudgeteuro = notice_data.netbudgetlc
                notice_data.est_amount = notice_data.netbudgetlc
            except Exception as e:
                logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
                pass


        # Onsite Field -VI.5)DATE D'ENVOI DU PRÉSENT AVIS
        # Onsite Comment -split the data from "VI.5)DATE D'ENVOI DU PRÉSENT AVIS" field

        try:
            dispatch_date = page_details.find_element(By.XPATH, "//*[contains(text(),'VI.5)')]//following::tr[1]").text
            dispatch_date = GoogleTranslator(source='fr', target='en').translate(dispatch_date)
            dispatch_date = re.findall('\w+ \d+, \d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.dispatch_date)
        except:
            try:
                dispatch_date = notice_text.split("Date d'envoi du présent avis à la publication : ")[1].split('\n')[0]
                dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
                notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.dispatch_date)            
            except Exception as e:
                logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
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
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'

            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'li.fr-my-1v.fr-py-0 > span.ng-binding').text

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(5) div  li:nth-child(4)').text.split('Adresse :')[1].strip()
            except :
                try:
                    customer_details_data.org_address = org_address_1
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass
            try:
                org_phone = page_details.find_element(By.XPATH, "(//*[contains(text(),'Téléphone :')])[1]//following::span[1]").text
                customer_details_data.org_phone = re.findall('\d+',org_phone)[0]

            except:
                try:
                    customer_details_data.org_phone = org_phone_1
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, "(//*[contains(text(),'Courriel :')])[1]//following::span[1]").text
                if '@' not in customer_details_data.org_email:
                    customer_details_data.org_email = org_email_1
            except:
                try:
                    customer_details_data.org_email = org_email_1
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, "(//*[contains(text(),'Adresse internet :')])[1]//following::a[1]/span").text
                if customer_details_data.org_website  == '':
                    customer_details_data.org_website = org_website_1
            except:
                try:
                    customer_details_data.org_website = org_website_1
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.contact_person = contact_person_1
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, "//*[contains(text(),'TYPE DE POUVOIR ADJUDICATEUR')]//following::td[3]").text
            except:
                try:
                    customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Forme juridique de l’acheteur')]//following::span[2]").text
                except Exception as e:
                    logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, "(//*[contains(text(),'ACTIVITÉ PRINCIPALE')])[1]//following::td[3]").text
            except:
                try:
                    customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, "//*[contains(text(),'Activité du pouvoir adjudicateur')]//following::span[2]").text
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
            cpvs_data = cpvs()
    #     # Onsite Field -II.1.2)Code CPV principal :  >  Descripteur principal :
    #     # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and cpv_code split after "Descripteur principal :"
            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '(//*[contains(text(),"Code CPV principal :")])[1]//following::tr[1]').text.split(':')[1].strip()
            except:
                cpvs_data.cpv_code = page_details.find_elements(By.XPATH, '//td[contains(text(),"Code CPV principal :")]').text.split(':')[1].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except:       
            try:
                notice_data.class_at_source = "CPV" 
                cpvs_code = page_details.find_element(By.XPATH, "(//*[contains(text(),'Nomenclature principale')])[1]//following::span[5]").text
                cpv_regex = re.compile(r'\d{8}')
                cpvs_data = cpv_regex.findall(cpvs_code)
                for cpv in cpvs_data:
                    cpv_at_source = ''
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv
                    notice_data.cpvs.append(cpvs_data) 
                    notice_data.cpv_at_source = cpv +','

                cpvs_code = page_details.find_element(By.XPATH, "(//*[contains(text(),'Nomenclature supplémentaire')])[1]//following::span[5]").text
                cpv_regex = re.compile(r'\d{8}')
                cpvs_data = cpv_regex.findall(cpvs_code)
                for cpv in cpvs_data:
                    cpv_at_source = ''
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv
                    notice_data.cpvs.append(cpvs_data)  

                    notice_data.cpv_at_source +=  cpv
                    notice_data.cpv_at_source += ','
                notice_data.cpv_at_source = notice_data.cpv_at_source.rstrip(',')

            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass


    # # Onsite Field -None
    # # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") to view to lot_details

        try:
            if 'Information sur le' in notice_text:

                lot_number = 1
                for lot in page_details.find_elements(By.XPATH, '//*[contains(text(),"Information sur les lots :")]//following::tbody'):
                    lot = lot.text
                    if 'Intitulé' in lot or 'Lot nº :' in lot or 'Code CPV principal : ' in lot or 'Nom et adresse du titulaire' in lot:
                        lot_title =lot.split('Intitulé :')[1].split('\n')[0]

                        if lot_title != '':

                            lot_details_data = lot_details()
                            lot_details_data.lot_number = lot_number

                            lot_details_data.lot_title =lot.split('Intitulé :')[1].split('\n')[0]
                            lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)

                            try:
                                lot_actual_number =lot.split('Lot nº :')[1].split('\n')[0]
                                lot_details_data.lot_actual_number = 'Lot nº :'+str(lot_actual_number)
                            except:
                                pass

                            try:
                                lot_details_data.contract_type = notice_data.notice_contract_type
                                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                            except Exception as e:
                                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                                pass    

                            try:
                                lot_details_data.lot_description = lot.split('Description des prestations :')[1].split("II.2.5) Critères d'attribution")[0].strip()
                                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                            except Exception as e:
                                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                                pass  

                            try:
                                lot_details_data.lot_nuts = lot.split('Code NUTS :')[1].split('\n')[0].strip()
                            except Exception as e:
                                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                                pass

                            try: 
                                lot_date = lot.split('Date de conclusion du marché :')[1].split('\n')[0].strip()
                                lot_date = GoogleTranslator(source='fr', target='en').translate(lot_date)
                                lot_award_date = re.findall('\w+ \d+, \d{4}',lot_date)[0]
                                lot_details_data.lot_award_date = datetime.strptime(lot_award_date,'%B %d, %Y').strftime('%Y/%m/%d')
                            except Exception as e:
                                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                                pass    

                            try:
                                lot_cpv1 = re.compile(r'\d{8}')
                                lot_cpv_at_source2 = lot_cpv1.findall(lot)
                                for lot1 in lot_cpv_at_source2:
                                    lot_cpvs_data = lot_cpvs()
                                    lot_cpvs_data.lot_cpv_code = lot1
                                    lot_cpvs_data.lot_cpvs_cleanup()
                                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                                    cpvs_data = cpvs()
                                    cpvs_data.cpv_code = lot1
                                    notice_data.cpvs.append(cpvs_data) 
                            except:
                                pass

                            try:
                                lot_cpv_at_source = ''
                                for singlerecord in lot.split('Code CPV principal : ')[1:]:
                                    if singlerecord != '':
                                        lot_cpv_at_source += singlerecord.split('\n')[0].strip()
                                        lot_cpv_at_source += ','
                                lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                                notice_data.cpv_at_source = notice_data.cpv_at_source + ',' +lot_details_data.lot_cpv_at_source
                            except:
                                pass

                            lot_details_data.lot_class_codes_at_source="CPV"

                            try:
                                lot_criteria_title = notice_text.split("Critères d'attribution")[1].split("II.2.6) Valeur estimée")[0].strip()
                                for l in lot_criteria_title.split('\n'):
                                    if 'Pondération' in l or 'VALEUR TECHNIQUE' in l:

                                        lot_criteria_data = lot_criteria()

                                        lot_criteria_title = l.split('/ Pondération')[0].strip()

                                        if 'valeur technique' in lot_criteria_title.lower():
                                            lot_criteria_data.lot_criteria_title = 'Valeur technique'
                                        elif 'technique' in lot_criteria_title.lower():
                                            lot_criteria_data.lot_criteria_title = 'technique'
                                        elif 'prix des prestations' in lot_criteria_title.lower():
                                            lot_criteria_data.lot_criteria_title = 'Prix des prestations'
                                        elif 'prix' in lot_criteria_title.lower():
                                            lot_criteria_data.lot_criteria_title = 'Prix'

                                        lot_criteria_data.lot_criteria_weight = int(l.split('/ Pondération :')[1].strip())
                                        if 'Prix' in l or 'PRIX' in l or 'prix' in l:
                                            lot_criteria_data.lot_is_price_related = True

                                        lot_criteria_data.lot_criteria_cleanup()
                                        lot_details_data.lot_criteria.append(lot_criteria_data) 
                            except Exception as e:
                                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                                pass

                            try:
                                award_details_data = award_details()

                                # Onsite Field -V.2.3)Nom et adresse du titulaire
                                # Onsite Comment -split bidder_name. eg., here "GEDIA SEML, Dreux, F, Code NUTS : FRB02 Le titulaire est une PME : oui" take only "GEVEKO MARKINGS SAS" in bidder_name.
                                award_details_data.bidder_name = lot.split('Nom et adresse du titulaire')[1].split('\n')[1].split(',')[0]
                                # Onsite Field -V.2.3)Nom et adresse du titulaire
                                # Onsite Comment -split address. eg., here "GEVEKO MARKINGS SAS, 16-18-16 rue du Bon Puits - St Sylvain d'Anjou, 49480, VERRIERES EN ANJOU, FR, Code NUTS : FRG02," take only "GEVEKO MARKINGS SAS, 16-18-16 rue du Bon Puits - St Sylvain d'Anjou, 49480, VERRIERES EN ANJOU, FR," in address., ref_url : "https://www.boamp.fr/pages/avis/?q=idweb:%2223-136818%22"
                                try:
                                    award_details_data.address = lot.split('Nom et adresse du titulaire')[1].split(', Code NUTS :')[0].strip()
                                except Exception as e:
                                    logging.info("Exception in award_details_data.address: {}".format(type(e).__name__))
                                    pass 
                                # Onsite Field -V.2.4)Informations sur le montant du marché/du lot   >> Estimation initiale du montant total du marché/du lot :
                                # Onsite Comment -split initial_estimate_amount after "Estimation initiale du montant total du marché/du lot :"

                                try:
                                    initial_estimated_value = lot.split('Estimation initiale du montant total du marché/du lot :')[1].split('H.T')[0].strip()
                                    initial_estimated_value = re.sub("[^\d\.\,]","",initial_estimated_value)
                                    award_details_data.initial_estimated_value = float(initial_estimated_value.replace(' ','').strip())
                                except Exception as e:
                                    logging.info("Exception in award_details_data.initial_estimated_value: {}".format(type(e).__name__))
                                    pass
                                # Onsite Field -Valeur totale du marché/du lot :
                                # Onsite Comment -split grossawardvaluelc after "Valeur totale du marché/du lot :"

                                try:
                                    grossawardvaluelc = lot.split('Valeur totale du marché/du lot :')[1].split('\n')[0].strip()
                                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                                    award_details_data.netawardvaluelc = float(grossawardvaluelc.replace(',','.').strip())
                                    award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                                except Exception as e:
                                    logging.info("Exception in award_details_data.grossawardvalueeuro: {}".format(type(e).__name__))
                                    pass

                                # Onsite Field -Valeur totale du marché/du lot :
                                # Onsite Comment -split grossawardvalueeuro  after "Valeur totale du marché/du lot :

                                # Onsite Field -Date de conclusion du marché :
                                # Onsite Comment -split the data after "V.2.1)	Date de conclusion du marché :" field
                                try:
                                    award_date_data = lot.split('Date de conclusion du marché : ')[1].split('\n')[0]
                                    award_date = GoogleTranslator(source='fr', target='en').translate(award_date_data)
                                    award_date = re.findall('\w+ \d+, \d{4}',award_date)[0]
                                    award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
                                except Exception as e:
                                    logging.info("Exception in award_details_data.award_date: {}".format(type(e).__name__))
                                    pass

                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)
                            except Exception as e:
                                logging.info("Exception in award_details: {}".format(type(e).__name__))
                                pass
                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number += 1
            else:
                lot_number = 1
                for lot in page_details.find_elements(By.XPATH, '//*[contains(text(),"Section 5")]//following-sibling::div'):
                    lot = lot.text

                    if 'Lot' in lot:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number

                        lot_details_data.lot_title =lot.split('Titre :')[1].split('\n')[0]
                        lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)


                        lot_details_data.lot_actual_number =lot.split('Lot :')[1].split('\n')[0]


                        try:
                            lot_details_data.contract_type = notice_data.notice_contract_type
                            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        except Exception as e:
                            logging.info("Exception in contract_type: {}".format(type(e).__name__))
                            pass    

                        try:
                            lot_details_data.lot_description = lot.split('Description : ')[1].split("\n")[0].strip()
                            lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                        except Exception as e:
                            logging.info("Exception in lot_description: {}".format(type(e).__name__))
                            pass 

                        try:
                            lot_details_data.contract_duration  = lot.split('Durée : ')[1].split('\n')[0]
                        except:
                            pass

                        try:
                            lot_details_data.lot_nuts = lot.split('Code NUTS :')[1].split('\n')[0].strip()
                        except Exception as e:
                            logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                            pass


                        try:
                            lot_details_data.contract_start_date = lot.split('Date de début : ')[1].split('\n')[0]
                            lot_details_data.contract_start_date = datetime.strptime(lot_details_data.contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass

                        try:
                            for lot1 in page_details.find_elements(By.XPATH, "//*[contains(text(),'Critères d’attribution')]//following-sibling::div"):
                                lot1=lot1.text
                                lot_criteria_data = lot_criteria()

                                lot_criteria_data.lot_criteria_title = lot1.split('Type : ')[1].split('\n')[0].strip()
                                if 'Prix' in lot_criteria_data.lot_criteria_title:
                                    lot_criteria_data.lot_is_price_related = True

                                lot_criteria_data.lot_criteria_weight = lot1.split('Pondération (points, valeur exacte) :')[1].split('\n')[0].strip()
                                lot_criteria_data.lot_criteria_weight = int(lot_criteria_data.lot_criteria_weight)

                                lot_criteria_data.lot_criteria_cleanup()
                                lot_details_data.lot_criteria.append(lot_criteria_data) 
                        except:
                            pass
                        try:
                            lot_cpv1 = re.compile(r'\d{8}')
                            lot_cpv_at_source2 = lot_cpv1.findall(lot)
                            for lot1 in lot_cpv_at_source2:
                                lot_cpvs_data = lot_cpvs()
                                lot_cpvs_data.lot_cpv_code = lot1
                                lot_cpvs_data.lot_cpvs_cleanup()
                                lot_details_data.lot_cpvs.append(lot_cpvs_data)
                                cpvs_data = cpvs()
                                cpvs_data.cpv_code = lot1
                                notice_data.cpvs.append(cpvs_data)
                        except:
                            pass

                        try:
                            lot_cpv_at_source = ''
                            lot_cpv1 = re.compile(r'\d{8}')
                            lot_cpv_at_source2 = lot_cpv1.findall(lot)
                            for lot1 in lot_cpv_at_source2:
                                lot_details_data.lot_cpv_at_source = lot1
                                notice_data.cpv_at_source += ','
                                notice_data.cpv_at_source += lot_details_data.lot_cpv_at_source
                        except:
                            pass

                        lot_details_data.lot_class_codes_at_source="CPV"

                        try:
                            for award in page_details.find_elements(By.XPATH, "//*[contains(text(),'Informations sur les lauréats')]//following-sibling::div"):
                                award = award.text
                                award_details_data = award_details()

                                if lot_details_data.lot_actual_number in award:
                                    
                                    award_details_data.bidder_name = award.split('Nom officiel : ')[1].split('\n')[0]
                                    
                                    try:
                                        grossawardvaluelc1 = award.split('Valeur du résultat : ')[1].split('\n')[0].strip()
                                        grossawardvaluelc =  re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b',grossawardvaluelc1)[0]
                                        if '.' not in  grossawardvaluelc:
                                            grossawardvaluelc=grossawardvaluelc.replace(',', '')
                                        else:
                                            grossawardvaluelc = grossawardvaluelc.replace(',', '')

                                        award_details_data.netawardvaluelc = float(grossawardvaluelc)
                                        award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                                    except:
                                        try:
                                            grossawardvaluelc = lot.split('Valeur totale du marché/du lot :')[1].split('\n')[0].strip()
                                            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                                            award_details_data.netawardvaluelc = float(grossawardvaluelc.replace(',','.').strip())
                                            award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                                        except Exception as e:
                                            logging.info("Exception in award_details_data.grossawardvalueeuro: {}".format(type(e).__name__))
                                            pass


                                    try:
                                        award_date_data = award.split('Date de conclusion du marché : ')[1].split('\n')[0]
                                        award_date = GoogleTranslator(source='fr', target='en').translate(award_date_data)
                                        award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                                        award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%Y').strftime('%Y/%m/%d')
                                    except:
                                        try:
                                            award_date_data = lot.split('Date de conclusion du marché : ')[1].split('\n')[0]
                                            award_date = GoogleTranslator(source='fr', target='en').translate(award_date_data)
                                            award_date = re.findall('\w+ \d+, \d{4}',award_date)[0]
                                            award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')

                                        except Exception as e:
                                            logging.info("Exception in award_details_data.award_date: {}".format(type(e).__name__))
                                            pass
                                    try:
                                        lot_details_data.lot_award_date = award_details_data.award_date
                                    except:
                                        pass

                                    try:
                                        award_details_data.address = lot.split('Nom et adresse du titulaire')[1].split(', Code NUTS :')[0].strip()
                                    except Exception as e:
                                        logging.info("Exception in award_details_data.address: {}".format(type(e).__name__))
                                        pass 
                                    try:
                                        initial_estimated_value = lot.split('Estimation initiale du montant total du marché/du lot :')[1].split('H.T')[0].strip()
                                        initial_estimated_value = re.sub("[^\d\.\,]","",initial_estimated_value)
                                        award_details_data.initial_estimated_value = float(initial_estimated_value.replace(' ','').strip())
                                    except Exception as e:
                                        logging.info("Exception in award_details_data.initial_estimated_value: {}".format(type(e).__name__))
                                        pass


                                    award_details_data.award_details_cleanup()
                                    lot_details_data.award_details.append(award_details_data)
                        except Exception as e:
                            logging.info("Exception in award_details: {}".format(type(e).__name__))
                            pass

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1        
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass   

        # Onsite Field -II.2.13)Information sur les fonds de l'Union européenne
        # Onsite Comment -click on "Voir l'annonce" ( selector : "div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button") and split the data from "II.2.13)Information sur les fonds de l'Union européenne" field

        try:              
            for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'II.2.13)')]//following::tr[1]"):
                funding_agency = single_record.text
                if 'yes' in funding_agency.lower():
                    funding_agencies_data = funding_agencies()
                    funding_agencies_data.funding_agencies = 1344862
                    funding_agencies_data.funding_agencies_cleanup()
                    notice_data.funding_agencies.append(funding_agencies_data) 

            # Onsite Field -II.2.13)Information sur les fonds de l'Union européenne
            # Onsite Comment -if in below text written as " financed by European Union funds: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT" "II.2.13) Information about European Union Funds  >  	The contract is part of a project/program financed by European Union funds: no " if the above  text written as " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"

        except Exception as e:
            logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
            pass

        try:               
            for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Obtenir un extrait de l’avis')]"):
                attachments_data = attachments()

                attachments_data.file_name = single_record.text
                attachments_data.external_url = single_record.get_attribute("href")
                try:
                    if 'pdf' in attachments_data.external_url:
                        attachments_data.file_type = 'pdf'
                    elif 'PDF' in attachments_data.external_url:
                        attachments_data.file_type = 'pdf'
                    elif 'zip' in attachments_data.external_url:
                        attachments_data.file_type = 'zip'
                    elif 'ZIP' in attachments_data.external_url:
                        attachments_data.file_type = 'zip'
                    elif 'DOCX' in attachments_data.external_url:
                        attachments_data.file_type = 'DOCX'
                    elif 'docx' in attachments_data.external_url:
                        attachments_data.file_type = 'docx'
                    elif 'XLS' in attachments_data.external_url:
                        attachments_data.file_type = 'XLS'
                    elif 'xlsx' in attachments_data.external_url:
                        attachments_data.file_type = 'xlsx'
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass   
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) +str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
        try:
            for page_no in range(2,50):
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
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
