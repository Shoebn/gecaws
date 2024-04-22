from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_boamp_spn"
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
    notice_data.class_at_source = "CPV"
   
    # Onsite Field -None
    # Onsite Comment -take local_title in textform

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification > h2 > p > a > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Publié le

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.fr-grid-row > span").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date limite de réponse le
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "p.fr-mb-1w > span").text
        notice_deadline1 = re.findall('\d+/\d+/\d{4} à \d+h\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline1,'%d/%m/%Y à %Hh%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Voir l’annonce
    # "https://www.boamp.fr/pages/avis/?q=idweb:%2224-1662%22"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-container> div > a').get_attribute("href")   
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    
    try:
        fn.load_page(page_details,notice_data.notice_url,80) 
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//div/label')))
        logging.info(notice_data.notice_url)
        time.sleep(10)

    # Onsite Field -Avis n°

        try:
            notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-grid-row > div.fr-checkbox-group > label').text
            notice_data.notice_no = re.findall('\d+-\d+',notice_no)[0]
        except:
            try:
                notice_no = page_details.find_element(By.XPATH, "//h1").text
                notice_data.notice_no  = re.sub("[^\d\.\-]", "", notice_no)
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass 


# Onsite Field -Objet du marché :
# Onsite Comment -if "Objet du marché :" field is not available in detail page then take local_title as notice_summary_english

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Objet du marché :')]/..").text.split('Objet du marché :')[1].strip()
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass
        
        try:
            try:
                org_phone = page_details.find_element(By.XPATH, "(//*[contains(text(),'Téléphone :')])[1]/..").text.split(':')[1]
            except:
                pass
            
            try: 
                org_email1 = page_details.find_element(By.XPATH, "(//*[contains(text(),'Courriel :')]/..)[2]").text.split(':')[1].strip()
                org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email1)[0]
            except:
                try:
                    org_email1 = page_details.find_element(By.XPATH, "(//*[contains(text(),'Courriel :')])[1]//following::span[1]").text
                    org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email1)[0]
                except:
                    try:
                        org_email1 = page_details.find_element(By.XPATH, '(//*[contains(text(),"Point(s) de contact :")])[1]//following::span[1]').text
                        org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email1)[0]
                    except:
                        pass

            try:                                                        
                contact_person1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Point(s) de contact : ")]/..').text.split(':')[1].strip()
                if '@' not in contact_person1:
                    contact_person = contact_person1
            except:
                pass

            try: 
                org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Adresse :')]//parent::li").text.split("Adresse :")[1].strip()
            except:
                pass
            
            try:
                org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse internet :")]//following::a[1]').text
            except:
                pass
            

        except Exception as e:
            logging.info("Exception in customer_details1: {}".format(type(e).__name__)) 
            pass

        try:                                                                          
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Adresse internet du profil')]//following::a[1]").text
        except Exception as e:
            logging.info("Exception in additional_tender_url1: {}".format(type(e).__name__))
            pass

        clik= WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," div > div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button")))
        page_details.execute_script("arguments[0].click();",clik)
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, "(//*[contains(text(),'Section 1')])[1]")))
        time.sleep(3)
        

        try: 
            tender_contract_start_date = page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').text.split("Date prévisionnelle de commencement des travaux :")[1].split('\n')[0].strip()
            tender_contract_start_date1= GoogleTranslator(source='auto', target='en').translate(tender_contract_start_date)
            tender_contract_start_date1 = re.findall('\w+ \d+, \d{4}',tender_contract_start_date1)[0]
            notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date1,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass   

        try:  
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Lien direct aux documents de la consultation :')]//following::td[3]").text
        except Exception as e:
            logging.info("Exception in additional_tender_url2: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '''//*[contains(text(),"Description succincte : ")]/..''').text.split(':')[1].strip()
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass


        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            # Onsite Field -ACHETEUR :

            customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Acheteur : ')]/following::span[1]").text.strip()

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, "//*[contains(text(),'Ville :')]/following::tr[1]").text
            except:
                try:
                    customer_details_data.org_city = page_details.find_element(By.XPATH, "//*[contains(text(),'Ville :')]/..").text.split(':')[1].strip()
                except Exception as e:
                    logging.info("Exception in org_city: {}".format(type(e).__name__))
                    pass  

            # Onsite Field -Téléphone :

            try:
                customer_details_data.org_phone = org_phone
            except:
                try:
                    customer_details_data.org_phone = page_details.find_element(By.XPATH, "(//*[contains(text(),'téléphone')])[1]/..").text.split(':')[1]
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

            try: 
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code Postal :")]//following::tr[1]').text
            except:
                try:
                    customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code postal :")]/..').text.split(':')[1].strip()
                except Exception as e:
                    logging.info("Exception in postal_code: {}".format(type(e).__name__))
                    pass
            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Forme juridique de l’acheteur")]//following::span[2]|//*[contains(text(),"Type de pouvoir adjudicateur : ")]/..').text.split(':')[1].strip()
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Activité du pouvoir adjudicateur")]//following::span[2]|//*[contains(text(),"Activité principale : ")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass


            try:
                customer_details_data.contact_person = contact_person
            except:
                try:
                    contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Nom du contact :")]/..').text.split(':')[1].strip()
                    if '@' not in contact_person:
                        customer_details_data.contact_person = contact_person
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass 

            # Onsite Field -Courriel :  

            try:
                customer_details_data.org_email = org_email
            except:
                try:
                    org_email1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse mail du contact :")]/..').text.split(':')[1].strip()
                    customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email1)[0]
                except:
                    try:
                        org_email1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Nom du contact :")]/..').text.split(':')[1].strip()
                        customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email1)[0]
                    except Exception as e:
                        logging.info("Exception in org_email: {}".format(type(e).__name__))
                        pass

            try:
                customer_details_data.org_address = org_address
            except:
                pass
            
            try:
                customer_details_data.org_website = org_website
            except:
                try:
                    customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresse internet :")]//following::a[1]').text
                except:
                    pass
            
            
            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Code NUTS : ")]/..').text.split(':')[1].strip()
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        # Onsite Field -None
        # Onsite Comment -for notice text click on "Voir l'annonce" and take all data in notice text
        try:
            notice_data.notice_text +=  WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-notification'))).get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass

        try:
            notice_text = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-notification'))).text
        except:
            pass

        try:
            if ' - rectificatif ' in notice_data.notice_text :
                notice_data.notice_type = 16
            else:
                notice_data.notice_type = 4
        except:
            pass

        try:
            notice_data.document_type_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Type ')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass


        try:
            dispatch_date = page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').text
            if "Date d'envoi du présent avis" in dispatch_date:
                dispatch_date = dispatch_date.split("Date d'envoi du présent avis")[1]
                dispatch_date = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
                dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
                notice_data.dispatch_date = datetime.strptime(dispatch_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
            else:
                pass
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass

        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, 'div.card-notification-info.fr-scheme-light-white.fr-p-5v.fr-mb-4w > ul > li:nth-child(4) ').text.split("PROCÉDURE : ")[1].strip()
            type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_spn_procedure.csv",type_of_procedure_actual)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

    # Onsite Field -Type de marché :
    # Onsite Comment -for notice_contract_type click on "Voir l'annonce" and Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works ',' Fournitures = Supply')

        try:
            contract_type_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),'Type de marché :')]//following::tr[1]|//*[contains(text(),"Nature du marché")]//following::span[2]|//*[contains(text(),'Type de marché :')]/..''').text.split(':')[1].strip()
            notice_data.contract_type_actual = contract_type_actual

            if "Services" in contract_type_actual:
                notice_data.notice_contract_type ='Service'
            elif "Travaux" in contract_type_actual:
                notice_data.notice_contract_type ='Works'
            elif "Fournitures" in contract_type_actual:
                notice_data.notice_contract_type ='Supply'
            else:
                pass
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        try:
            contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée du marché (en mois) :")]//following::tr[1]').text.strip()
            if contract_duration !='':
                notice_data.contract_duration  = 'Durée du marché (en mois) : '+ contract_duration
        except:
            try:
                notice_data.contract_duration = page_details.find_element(By.XPATH, '''//*[contains(text(),"Durée du marché ou délai d'exécution")]//parent::p[1]''').text.split(":")[1].split('\n')[0].strip()
            except:
                try:
                    notice_data.contract_duration = page_details.find_element(By.XPATH, '''//*[contains(text(),"Durée du marché ou délai")]//following::div[1]''').text
                except:
                    try:
                        contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Durée du marché (en mois) :")]/..').text.split(':')[1].strip()
                        notice_data.contract_duration  = 'Durée du marché (en mois) : '+ contract_duration
                    except Exception as e:
                        logging.info("Exception in notice_data.contract_duration: {}".format(type(e).__name__))
                        pass

        try:
            tender_criteria_t = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d")]//parent::p').text.split('\n')[2:]
            for single_record in tender_criteria_t:
                if single_record !='':
                    tender_criteria_data = tender_criteria()

                    tender_criteria_title = single_record.split(':')[0].strip()
                    if 'technique' in tender_criteria_title.lower():
                        tender_criteria_data.tender_criteria_title = 'technique'
                    elif 'prix' in tender_criteria_title.lower():
                        tender_criteria_data.tender_criteria_title = 'price'
                        tender_criteria_data.tender_is_price_related = True
                    elif 'planning général' in tender_criteria_title.lower():
                        tender_criteria_data.tender_criteria_title = "Planning général"
                    elif 'qualité' in tender_criteria_title.lower():
                        tender_criteria_data.tender_criteria_title = "Qualité"
                    elif 'Conditions environnementales' in tender_criteria_title.lower():
                        tender_criteria_data.tender_criteria_title = "Conditions environnementales"

                    tender_criteria_weight =single_record.split(':')[1].split('sur')[0].strip()
                    tender_criteria_weight = re.findall('\d+',tender_criteria_weight)[0]
                    tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight) 

                    if tender_criteria_data.tender_criteria_title != None:
                        tender_criteria_data.tender_criteria_cleanup()
                        notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria1: {}".format(type(e).__name__)) 
            pass

        try: 
            tender_criteria_t = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d")]//following::tr[1]').text.replace('-',' ')
            if "Sous critère" in tender_criteria_t and "n°" in tender_criteria_t:
                for each_criteria in tender_criteria_t.split('%'):
                    count_data = each_criteria.count(':')
                    if each_criteria !='':
                        tender_criteria_data = tender_criteria()

                        if count_data >= 2:
                            tender_criteria_data.tender_criteria_title = each_criteria.split(':')[1].split(':')[0].strip()
                        else:
                            tender_criteria_data.tender_criteria_title = each_criteria.split(':')[0].strip()

                        if 'Prix' in tender_criteria_data.tender_criteria_title or 'prix' in tender_criteria_data.tender_criteria_title:
                            tender_criteria_data.tender_is_price_related = True

                        each_criteria1= re.findall('\d{2}',each_criteria)[-1]
                        tender_criteria_data.tender_criteria_weight  = int(each_criteria1)

                        if tender_criteria_data.tender_criteria_title != None:
                            tender_criteria_data.tender_criteria_cleanup()
                            notice_data.tender_criteria.append(tender_criteria_data)

            elif "Sous critère" in tender_criteria_t:
                for each_criteria in tender_criteria_t.split('Sous critère')[1:]:
                    if each_criteria !='':
                        tender_criteria_data = tender_criteria()
                        if ':-' in each_criteria and ':' in each_criteria:
                            tender_criteria_data.tender_criteria_title = each_criteria.split(':')[2].split('(')[0].strip()
                        else:
                            tender_criteria_data.tender_criteria_title = each_criteria.split(':')[1].split('(')[0].strip()

                        each_criteria1= re.findall('\d{2}',each_criteria)[0]
                        tender_criteria_data.tender_criteria_weight  = int(each_criteria1) 

                        if tender_criteria_data.tender_criteria_title != None:
                            tender_criteria_data.tender_criteria_cleanup()
                            notice_data.tender_criteria.append(tender_criteria_data)

            elif "/" in tender_criteria_t:
                for each_criteria in tender_criteria_t.split('/'):
                    if 'lot' not in tender_criteria_t:
                        tender_criteria_data = tender_criteria()

                        each_criteria1= re.findall('\d+',each_criteria)[-1]
                        tender_criteria_data.tender_criteria_weight  = int(each_criteria1) 

                        tender_criteria_data.tender_criteria_title = each_criteria.split(each_criteria1)[0].strip()

                        if tender_criteria_data.tender_criteria_title != None:
                            tender_criteria_data.tender_criteria_cleanup()
                            notice_data.tender_criteria.append(tender_criteria_data)                      
            else:
                try:
                    for each_criteria in tender_criteria_t.split('%'):
                        if 'lot' not in tender_criteria_t:
                            tender_criteria_data = tender_criteria()

                            each_criteria1= re.findall('\d+',each_criteria)[-1]
                            tender_criteria_data.tender_criteria_weight  = int(each_criteria1) 

                            tender_criteria_data.tender_criteria_title = each_criteria.split(each_criteria1)[0].split(':')[0].strip()
                            if 'prix' in tender_criteria_data.tender_criteria_title.lower():
                                tender_criteria_data.tender_is_price_related = True

                            if tender_criteria_data.tender_criteria_title != None:
                                tender_criteria_data.tender_criteria_cleanup()
                                notice_data.tender_criteria.append(tender_criteria_data)
                except:
                    pass
        except:
            try:
                tender_criteria_t = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d")]//following::tr[1]').text
                for each_criteria in tender_criteria_t.split('Valeur'):
                    tender_criteria_weight = each_criteria.split('-')[1]
                    if each_criteria !='':
                        tender_criteria_data = tender_criteria()
                        each_criteria_title = each_criteria.split('-')[0]
                        if 'technique' in each_criteria_title.lower():
                            tender_criteria_data.tender_criteria_title = 'technique'
                        elif 'prix' in each_criteria_title.lower():
                            tender_criteria_data.tender_criteria_title = 'Prix'
                        elif 'planning général' in each_criteria_title.lower():
                            tender_criteria_data.tender_criteria_title = "Planning général"
                        elif 'qualité' in each_criteria_title.lower():
                            tender_criteria_data.tender_criteria_title = "Qualité"
                        elif 'Conditions environnementales' in each_criteria_title.lower():
                            tender_criteria_data.tender_criteria_title = "Conditions environnementales"

                        tender_criteria_weight = tender_criteria_weight.strip()
                        tender_criteria_data.tender_criteria_weight  = int(tender_criteria_weight) 
                        if 'prix' in each_criteria_title.lower():
                            tender_criteria_data.tender_is_price_related = True

                        if tender_criteria_data.tender_criteria_title != None:
                            tender_criteria_data.tender_criteria_cleanup()
                            notice_data.tender_criteria.append(tender_criteria_data)
            except:
                try:
                    tender_criteria_t = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d")]//following::tr[1]').text
                    for each_criteria in tender_criteria_t.split('%')[:-1]:
                        if each_criteria !='':
                            each_criteria1= re.findall('\d{2}',each_criteria)[-1]
                            tender_criteria_data = tender_criteria()
                            each_criteria_title = each_criteria.replace(each_criteria1,'').strip()
                            if 'valeur technique' in each_criteria_title.lower():
                                tender_criteria_data.tender_criteria_title = 'Valeur technique'
                            elif 'technique' in each_criteria_title.lower():
                                tender_criteria_data.tender_criteria_title = 'technique'
                            elif 'prix des prestations' in each_criteria_title.lower():
                                tender_criteria_data.tender_criteria_title = 'Prix des prestations'
                            elif 'prix' in each_criteria_title.lower():
                                tender_criteria_data.tender_criteria_title = 'Prix'
                            elif 'planning général' in each_criteria_title.lower():
                                tender_criteria_data.tender_criteria_title = "Planning général"
                            elif 'qualité' in each_criteria_title.lower():
                                tender_criteria_data.tender_criteria_title = "Qualité"
                            elif 'Conditions environnementales' in each_criteria_title.lower():
                                tender_criteria_data.tender_criteria_title = "Conditions environnementales"

                            if 'prix' in each_criteria_title.lower():
                                tender_criteria_data.tender_is_price_related = True

                            tender_criteria_data.tender_criteria_weight  = int(each_criteria1) 

                            if tender_criteria_data.tender_criteria_title != None:
                                tender_criteria_data.tender_criteria_cleanup()
                                notice_data.tender_criteria.append(tender_criteria_data)
                except Exception as e:
                    logging.info("Exception in tender_criteria3: {}".format(type(e).__name__)) 
                    pass
        try:
            tender_criteria_t = page_details.find_element(By.XPATH, '''//*[contains(text(),'Section 5 : Lots')]//following::table''').text
            for each_criteria in tender_criteria_t.split('%'):
                if 'lot' not in tender_criteria_t:
                    tender_criteria_data = tender_criteria()

                    each_criteria1= re.findall('\d+',each_criteria)[-1]
                    tender_criteria_data.tender_criteria_weight  = int(each_criteria1) 

                    tender_criteria_data.tender_criteria_title = each_criteria.split('('+each_criteria1)[0].split('-')[-1].strip()

                    if "prix" in tender_criteria_data.tender_criteria_title.lower():
                        tender_criteria_data.tender_is_price_related = True


                    if tender_criteria_data.tender_criteria_title != None:
                        tender_criteria_data.tender_criteria_cleanup()
                        notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria4: {}".format(type(e).__name__)) 
            pass
        
        try:
            tender_criteria_da = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Critères d'attribution")])[2]//following::div[1]/ul|//*[contains(text(),"Critères d'attribution :")]/..''').text
            if "%" in tender_criteria_da:
                for each_criteria in tender_criteria_da.split('%')[:]:
                    if 'lot' not in each_criteria:
                        tender_criteria_data = tender_criteria()

                        each_criteria1= re.findall('\d+',each_criteria)[-1]
                        each_criteria2= each_criteria1.split('%')[0].strip()
                        tender_criteria_data.tender_criteria_weight  = int(each_criteria2) 

                        tender_criteria_title = each_criteria.split(': '+each_criteria2)[0].strip()
                        if '-' in tender_criteria_title:
                            tender_criteria_data.tender_criteria_title = tender_criteria_title.split('-')[-1].strip()
                        else:
                            tender_criteria_data.tender_criteria_title = tender_criteria_title
                        if "prix" in tender_criteria_data.tender_criteria_title.lower():
                            tender_criteria_data.tender_is_price_related = True


                        tender_criteria_data.tender_criteria_cleanup()
                        notice_data.tender_criteria.append(tender_criteria_data)
            else:
                for each_criteria in tender_criteria_da.split('points)')[:]:
                    if 'lot' not in each_criteria:
                        tender_criteria_data = tender_criteria()

                        each_criteria1= re.findall('\d+',each_criteria)[-1]
                        tender_criteria_data.tender_criteria_weight  = int(each_criteria1) 

                        tender_criteria_title = each_criteria.split('('+each_criteria1)[0].strip()
                        if ')' in tender_criteria_title:
                            tender_criteria_data.tender_criteria_title = tender_criteria_title.split(')')[-1].strip()
                        else:
                            tender_criteria_data.tender_criteria_title = tender_criteria_title
                        if "prix" in tender_criteria_data.tender_criteria_title.lower():
                            tender_criteria_data.tender_is_price_related = True


                        tender_criteria_data.tender_criteria_cleanup()
                        notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria4: {}".format(type(e).__name__)) 
            pass

        
        try:
            tender_criteria_da = page_details.find_element(By.XPATH, '''//*[contains(text(),"Autres informations complémentaires :")]/..''').text
            for each_criteria in tender_criteria_da.split('%')[:-1]:
                if 'lot' not in each_criteria and "prix" in each_criteria.lower():
                    if "Sous-critère" not in each_criteria and "prix" in each_criteria.lower():
                        tender_criteria_data = tender_criteria()

                        each_criteria1= re.findall('\d+',each_criteria)[-1]
                        tender_criteria_data.tender_criteria_weight  = int(each_criteria1) 

                        tender_criteria_data.tender_criteria_title = each_criteria.split('-')[1].split(': '+each_criteria1)[0].strip()
                        if "prix" in tender_criteria_data.tender_criteria_title.lower():
                            tender_criteria_data.tender_is_price_related = True


                        tender_criteria_data.tender_criteria_cleanup()
                        notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria4: {}".format(type(e).__name__)) 
            pass
        
        

        # Onsite Field -Valeur estimée (H.T.) :
        # Onsite Comment -for est_amount click on "Voir l'annonce"

    #     try:
    #         notice_data.est_amount = notice_data.grossbudgetlc
    #     except Exception as e:
    #         logging.info("Exception in est_amount: {}".format(type(e).__name__))
    #         pass  

        try:
            related_tender_id = page_details.find_element(By.XPATH, '''//*[contains(text(),"Numéro de référence :")]/..''').text.split(':')[1].strip()
            if related_tender_id !='':
                notice_data.related_tender_id = related_tender_id
            else:  
                notice_data.related_tender_id = notice_text.split('entité adjudicatrice :')[1].split('\n')[0].strip()
        except:
            pass

        try:
            cpvs_data = cpvs()
            cpv_code = page_details.find_element(By.XPATH, '''//*[contains(text(),'Descripteur principal :')]/..|//*[contains(text(),"Nomenclature principale")]//following::span[1]|//*[contains(text(),"Nomenclature supplémentaire")]//following::span[1]|//*[contains(text(),"CPV - Objet principal : ")]/..''').text
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
            if cpvs_data.cpv_code != '':
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

        try:
            lst_cpv_code = []
            for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Section 5 : Lots')]//following::table"):


                # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
                # Onsite Comment -None
                try:
                    cpv_code = single_record.text.split('Code CPV principal :')[1].split('\n')[0].strip()
                    cpv_code_data = re.findall('\d{8}',cpv_code)[0]
                    lst_cpv_code.append(cpv_code_data)
                except:
                    pass
            for cpv in set(lst_cpv_code):
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code2: {}".format(type(e).__name__))
            pass


        try:
            netbudgetlc = page_details.find_element(By.XPATH, "//*[contains(text(),'Valeur estimée (H.T.) :')]//following::tr[1]").text.strip()
            netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
            notice_data.netbudgetlc = float(netbudgetlc)
            notice_data.netbudgeteuro = notice_data.netbudgetlc 
        except:
            try:    
                netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"et :")]//following::td[3]').text.strip()
                netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
                notice_data.netbudgetlc = float(netbudgetlc)
                notice_data.netbudgeteuro = notice_data.netbudgetlc 
            except:
                try:    
                    netbudgetlc = page_details.find_element(By.XPATH, '''//*[contains(text(),'Section 5 : Lots')]//following::table''').text.split("Montant maximum pour")[1].split(":")[1].split('euro')[0].strip()
                    netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
                    notice_data.netbudgetlc = float(netbudgetlc)
                    notice_data.netbudgeteuro = notice_data.netbudgetlc
                except Exception as e:
                    logging.info("Exception in notice_data.netbudgetlc1: {}".format(type(e).__name__))
                    pass
                
        try:
            netbudgetlc = page_details.find_element(By.XPATH, '''//*[contains(text(),"Valeur maximale")]/..''').text.split(":")[1].strip()
            netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
            notice_data.netbudgetlc = float(netbudgetlc)
            notice_data.netbudgeteuro = notice_data.netbudgetlc
        except:
            try:
                netbudgetlc = page_details.find_element(By.XPATH, '''//*[contains(text(),'Valeur estimée')]/..''').text.split(":")[1].strip()
                netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
                notice_data.netbudgetlc = float(netbudgetlc)
                notice_data.netbudgeteuro = notice_data.netbudgetlc
            except Exception as e:
                logging.info("Exception in notice_data.netbudgetlc2: {}".format(type(e).__name__))
                pass

        try:
            netbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'tr > td > p:nth-child(14)').text.split('montant estimé travaux de réhabilitation y compris résidentialisation : ')[1].split('euros (H.T.)')[0]
            netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
            notice_data.netbudgetlc = float(netbudgetlc)
            notice_data.netbudgeteuro = notice_data.netbudgetlc
        except:
            try:
                netbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'tr > td > p:nth-child(15)').text.split('valeur hors TVA :')[1].split('euros')[0].strip()
                netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
                netbudgetlc1 = netbudgetlc.replace(' ','')
                notice_data.netbudgetlc = float(netbudgetlc1)
                notice_data.netbudgeteuro = notice_data.netbudgetlc
            except Exception as e:
                logging.info("Exception in notice_data.netbudgetlc3: {}".format(type(e).__name__))
                pass

    # data is countinuosly change so auable to grap this data.

    # Onsite Field -Valeur estimée (H.T.) :
    # Onsite Comment -for grossbudgetlc click on "Voir l'annonce"  valeur hors TVA : 

        try:
            grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'tr > td > p:nth-child(15)').text.split('Valeur (T.T.C.) :')[1].split('euros')[0].strip()
            if ',' in grossbudgetlc:
                grossbudgetlc1 = re.sub("[^\d\.\,]", "", grossbudgetlc)
                grossbudgetlc2 = grossbudgetlc1.replace(",",".")
                notice_data.grossbudgetlc =float(grossbudgetlc2)
                notice_data.grossbudgeteuro = notice_data.grossbudgetlc
            else:
                grossbudgetlc1 = re.sub("[^\d\.\,]", "", grossbudgetlc)
                grossbudgetlc2 = grossbudgetlc1.replace(' ','')
                notice_data.grossbudgetlc =float(grossbudgetlc2)
                notice_data.grossbudgeteuro = notice_data.grossbudgetlc
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass

    # Onsite Field -Renseignements relatifs aux lots :
        try:
            lot_cpv_at_source1 = ''
            lot_number = 1
            for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Section 5 : Lots')]//following::table|(//*[contains(text(),'Section 5')])[1]//following::div[1]/ul/li|//*[contains(text(),'Section 5')]//following-sibling::div"):
                if single_record.text.count("Description du lot :") >=2:
                    pass
                else:
                    try:
                        try:
                            lot_cpv = single_record.text.split('Code CPV principal :')[1].split('\n')[0].strip()
                        except:
                            lot_cpv = single_record.text.split('Descripteur principal : ')[1].split('\n')[0].strip()
                        if lot_cpv != '':
                            lot_cpv_at_source1 += re.findall('\d{8}',lot_cpv)[0]
                            lot_cpv_at_source1 += ','
                    except:
                        pass

                    try:
                        try:
                            lot_cpv = single_record.text.split('Nomenclature principale ( cpv ):')[1].split('\n')[0].strip()
                        except:
                            lot_cpv = single_record.text.split('Nomenclature supplémentaire ( cpv ):')[1].split('\n')[0].strip()
                        if lot_cpv != '':
                            lot_cpv_at_source1 += re.findall('\d{8}',lot_cpv)[0]
                            lot_cpv_at_source1 += ','
                    except:
                        pass

                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        try:
                            lot_details_data.lot_title = single_record.text.split('Description du lot :')[1].split('\n')[0].strip()
                        except:
                            lot_details_data.lot_title = single_record.text.split('Titre :')[1].split('\n')[0].strip()

                        try:
                            lot_actual_number = lot_details_data.lot_title
                            if ":" in lot_actual_number:
                                lot_actual_number_data = lot_actual_number.split(':')[0].strip()
                                if "Lot" in lot_actual_number_data or "lot" in lot_actual_number_data:
                                    lot_details_data.lot_actual_number = lot_actual_number_data
                                else:
                                    lot_details_data.lot_actual_number = "Lot "+lot_actual_number_data
                            elif 'Lot' in lot_actual_number or 'lot' in lot_actual_number:
                                try:
                                    lot_details_data.lot_actual_number = re.findall('Lot \d+',lot_actual_number)[0]
                                except:
                                    lot_details_data.lot_actual_number = re.findall('lot \d+',lot_actual_number)[0]
                        except:
                            pass

                        try:
                            lot_details_data.lot_actual_number = single_record.text.split('Lot :')[1].split('\n')[0].strip()
                        except:
                            pass

                        try:
                            lot_details_data.lot_description = single_record.text.split('Description :')[1].split('\n')[0].strip()
                        except Exception as e:
                            logging.info("Exception in lot_description: {}".format(type(e).__name__))
                            pass

                        try:
                            single_record_netbudget = page_details.find_element(By.CSS_SELECTOR, "table:nth-child(39)  tr:nth-child(4) > td.txt").text
                            try:
                                lot_netbudget = single_record_netbudget.split('maxi')[lot_number].split('euro')[0].strip()
                                lot_netbudget_lc = re.sub("[^\d\.]", "", lot_netbudget)
                                lot_details_data.lot_netbudget = float(lot_netbudget_lc)
                                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
                            except:
                                pass
                        except:
                            pass


                        try:
                            lot_netbudget = single_record.text.split('Estimation de la valeur hors taxes du lot :')[1].split('euros')[0].strip() 
                            if lot_netbudget != '':
                                lot_netbudget_lc = re.sub("[^\d\.]", "", lot_netbudget)
                                lot_details_data.lot_netbudget = float(lot_netbudget_lc)
                                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
                            else:
                                lot_netbudget_lc_data = lot_details_data.lot_title.split("Montant maximum : ")[1].split("euro")[0].strip()
                                lot_netbudget_lc = re.sub("[^\d\.]", "", lot_netbudget_lc_data.strip())
                                lot_details_data.lot_netbudget = float(lot_netbudget_lc)
                                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
                        except:
                            try:
                                lot_netbudget = single_record.text.split('Valeur maximale de l’accord-cadre :')[1].split('\n')[0].strip()
                                lot_netbudget_lc = re.sub("[^\d\.]", "", lot_netbudget)
                                lot_details_data.lot_netbudget = float(lot_netbudget_lc)
                                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
                            except:
                                try:
                                    lot_netbudget = single_record.text.split('Valeur estimée hors TVA :')[1].split('\n')[0].strip()
                                    lot_netbudget_lc = re.sub("[^\d\.]", "", lot_netbudget)
                                    lot_details_data.lot_netbudget = float(lot_netbudget_lc)
                                    lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
                                except Exception as e:
                                    logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                                    pass


                        try:
                            lot_details_data.lot_nuts = single_record.text.split('Subdivision pays (NUTS) :')[1].split('\n')[0].strip()
                        except Exception as e:
                            logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                            pass


                        try:
                            contract_start_date = single_record.text.split('Date de début :')[1].split('\n')[0].strip()
                            contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
                            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                        except Exception as e:
                            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                            pass

                    # Onsite Field -Durée
                    # Onsite Comment -here take "MONTH" keyword also

                        try:
                            lot_details_data.contract_duration = single_record.text.split('Durée :')[1].split('\n')[0].strip()
                        except Exception as e:
                            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                            pass


                        try:
                            lot_cpvs_data = lot_cpvs()

                            # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
                            # Onsite Comment -None
                            try:
                                lot_cpv_code = single_record.text.split('Code CPV principal :')[1].split('\n')[0].strip()
                            except:
                                lot_cpv_code = single_record.text.split('Descripteur principal :')[1].split('\n')[0].strip()
                            lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0]
                            lot_cpvs_data.lot_cpvs_cleanup()
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        except Exception as e:
                            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                            pass

                        try:
                            lot_cpv_at_source = ''
                            try:
                                lot_cpv_at_source_data = single_record.text.split('Code CPV principal :')[1].split('\n')[0].strip()
                            except:
                                lot_cpv_at_source_data = single_record.text.split('Descripteur principal :')[1].split('\n')[0].strip()
                            lot_cpv_at_source += re.findall('\d{8}',lot_cpv_at_source_data)[0]
                            lot_details_data.lot_cpv_at_source = lot_cpv_at_source
                        except Exception as e:
                            logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                            pass

                        try:
                            lot_cpvs_data = lot_cpvs()

                            # Onsite Field -Abschnitt II: Gegenstand >> II.1.2) CPV-Code Hauptteil
                            # Onsite Comment -None
                            try:
                                lot_cpv_code = single_record.text.split('Nomenclature principale ( cpv ):')[1].split('\n')[0].strip()
                            except:
                                lot_cpv_code = single_record.text.split('Nomenclature supplémentaire ( cpv ):')[1].split('\n')[0].strip()

                            lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0]
                            lot_cpvs_data.lot_cpvs_cleanup()
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        except Exception as e:
                            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                            pass

                        try:
                            lot_cpv_at_source = ''
                            try:
                                lot_cpv_at_source_data = single_record.text.split('Nomenclature principale ( cpv ):')[1].split('\n')[0].strip()
                            except:
                                lot_cpv_at_source_data = single_record.text.split('Nomenclature supplémentaire ( cpv ):')[1].split('\n')[0].strip()
                            lot_cpv_at_source += re.findall('\d{8}',lot_cpv_at_source_data)[0]
                            lot_details_data.lot_cpv_at_source = lot_cpv_at_source
                        except Exception as e:
                            logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                            pass


                        try:
                            lot_details_data.contract_type = notice_data.notice_contract_type
                            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                            lot_details_data.contract_duration = notice_data.contract_duration
                        except Exception as e:
                            logging.info("Exception in contract_duration: {}".format(type(e).__name__)) 
                            pass

                        try:
                            lot_criteria_t = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d")]//following::tr[1]').text
                            if "lot" in lot_criteria_t or "Lot" in lot_criteria_t:
                                for each_criteria in lot_criteria_t.split('%')[:-1]:
                                    lot_criteria_data = lot_criteria()

                                    each_criteria1 = re.findall('\d+',each_criteria)[-1]
                                    lot_criteria_data.lot_criteria_weight  = int(each_criteria1)

                                    lot_criteria_title = each_criteria.split(each_criteria1)[0].strip()
                                    lot_criteria_data.lot_criteria_title = lot_criteria_title.split('-')[-1].split(',')[0].strip()
                                    if "Prix" in  lot_criteria_data.lot_criteria_title or "prix" in lot_criteria_data.lot_criteria_title:
                                        lot_criteria_data.lot_is_price_related = True

                                    lot_criteria_data.lot_criteria_cleanup()
                                    lot_details_data.lot_criteria.append(lot_criteria_data)
                        except:
                            try:
                                lot_criteria_da = page_details.find_element(By.XPATH, '//*[contains(text(),"Critères d’attribution")]/..').text
                                for single_record in lot_criteria_da.split('Critère :')[1:]:
                                    lot_criteria_data = lot_criteria()

                                    # Onsite Field -Type
                                    # Onsite Comment -take only value from "5.1.10 Critères d’attribution >> Type"

                                    lot_criteria_data.lot_criteria_title = single_record.split('Type :')[1].split('\n')[0].strip()
                                    if "prix" in lot_criteria_data.lot_criteria_title.lower():
                                        lot_criteria_data.lot_is_price_related = True
                                    # Onsite Field -Pondération (points, valeur exacte)
                                    # Onsite Comment -split and take only value from "5.1.10 Critères d’attribution >> Pondération (points, valeur exacte) "

                                    each_criteria1 = re.findall('\d+',single_record)[-1]
                                    lot_criteria_data.lot_criteria_weight  = int(each_criteria1)



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
        except Exception as e:
            logging.info("Exception in lots: {}".format(type(e).__name__)) 
            pass
        
        try:
            lot_number = 1  
            lots_check = page_details.find_element(By.XPATH, "//*[contains(text(),'Renseignements relatifs aux lots')]//following::ul[3]").text
            for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Renseignements relatifs aux lots')]//following::ul[1]/li"):
                lots = single_record.get_attribute('innerHTML')
                if "Lot(s)" in lots_check:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number

                    lot_details_data.lot_title = lots.split(':')[1].strip()
                    lot_details_data.lot_actual_number = lots.split(':')[0].strip()

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
        except Exception as e:
            logging.info("Exception in lots: {}".format(type(e).__name__)) 
            pass

        try:
            cpv_at_source = ''
            cpv_code = page_details.find_element(By.XPATH, '''//*[contains(text(),'Descripteur principal :')]/..|//*[contains(text(),"Nomenclature principale")]//following::span[1]|//*[contains(text(),"Nomenclature supplémentaire")]//following::span[1]|//*[contains(text(),"CPV - Objet principal : ")]/..''').text
            source = re.findall('\d{8}',cpv_code)[0]
            cpv_at_source += source
            cpv_at_source += ',' 
            cpv_at_source += lot_cpv_at_source1
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        except Exception as e:
            notice_data.cpv_at_source = lot_cpv_at_source1.rstrip(',')
            logging.info("Exception in cpv_at_source: {}".format(type(e).__name__)) 
            pass

        try:              
            attachments_data = attachments()
            attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.fr-grid-row > a').text

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.fr-grid-row > a').get_attribute('href')
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    except Exception as e:
        logging.info("Exception in notice_url2: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.publish_date) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) +str(notice_data.local_title)
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
    keywords = ['24-20525','24-21892','24-22826','24-22769','24-25240','24-25385','24-25386','24-25427','24-25496','24-25641','24-25642','24-25650','24-25156','24-25175','24-25178','24-25497','24-25499','24-25539','24-25580','24-25616','24-25617','24-25143','24-25215','24-25241','24-25355','24-25483','24-25498','24-25102','24-25184','24-25262','24-25395','24-25396','24-25592','24-25622','24-25630','24-25342','24-25348','24-25644','24-25647','24-25648','24-25222','24-25227','24-26116','24-27324','24-27932','24-28883','24-29386','24-29889','24-30198','24-29820','24-32605','24-32614','24-32114','24-32119','24-32142','24-32164','24-32337','24-32357','24-32370','24-32453','24-32460','24-32159','24-32093','24-32099','24-32109','24-32405','24-32411','24-32417','24-32418','24-32602','24-32223','24-32239','24-32604','24-32609','24-32613','24-33698','24-33757','24-33765','24-34753','24-35027','24-35512','24-35442','24-35445','24-35399','24-35249','24-35277','24-35199','24-35304','24-35205','24-35444','24-35453','24-35239','24-35257','24-35226','24-35227','24-35111','24-35077','24-35088','24-35406','24-35420','24-35106','24-35110','24-35178','24-35182','24-35154','24-35163','24-35276','24-36229','24-36225','24-36813','24-36391','24-36394','24-36396','24-36406','24-36442','24-36452','24-36815','24-36597','24-36599','24-36610','24-36614','24-36256','24-36264','24-36453','24-36578','24-36557','24-36618','24-36488','24-36672','24-37418']
    for keyword in keywords:
        url = 'https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&q.idweb=idweb:'+str(keyword)
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            page_check = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.XPATH,'//*[@id="toplist"]/li/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="toplist"]/li/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="toplist"]/li/div')))[records]
                extract_and_save_notice(tender_html_element)
        except:
            logging.info('No new record')
            pass
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
