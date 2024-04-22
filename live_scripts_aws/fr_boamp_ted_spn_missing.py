from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_boamp_ted_spn"
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
        deadline_date = tender_html_element.find_element(By.CSS_SELECTOR, "h2 > p.fr-mb-1w > span ").text
        deadline_date = GoogleTranslator(source='fr', target='en').translate(deadline_date)
        deadline_date = deadline_date.replace('.','').replace('at','')
        deadline_date = re.findall('\d+/\d+/\d{4}  \d+:\d{2} [ap][m]', deadline_date)[0]
        notice_data.notice_deadline = datetime.strptime(deadline_date,'%m/%d/%Y  %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')         
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' p > a').get_attribute("href")
    except:
        pass
    
    try: 
        fn.load_page(page_details,notice_data.notice_url,80)
        try:
            WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Nom et adresse officiels de')]"))).text
        except:
             WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Adresse : ')]"))).text
        logging.info(notice_data.notice_url)

        try:
            text1 = page_details.find_element(By.CSS_SELECTOR,'#toplist > div > div > div > div:nth-child(6) > div > div > div > ul').text
            address = text1.split('Adresse : ')[1].split('\n')[0]
            try:
                add_url= text1.split("Adresse internet du profil d'acheteur :")[1].split('\n')[0]
            except:
                pass
            try:
                telephone = text1.split("Téléphone : ")[1].split('\n')[0]
            except:
                pass
            try:
                contact_person =  text1.split("Point(s) de contact : ")[1].split('\n')[0]
            except:
                pass
            try:
                email = text1.split("Courriel : ")[1].split('\n')[0]
            except:
                pass
        except:
            pass
        

        clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.fr-btn.fr-my-1w.ng-binding'))).click()
        time.sleep(3)
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Section 1')]")))

        try:
            notice_data.notice_text += WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="toplist"]/div/div/div'))).get_attribute("outerHTML") 
            notice_text = page_details.find_element(By.XPATH, '//*[@id="toplist"]/div/div/div').text
        except:
            pass
        
        
        if 'NOM ET ADRESSES' in notice_text:
            try:
                customer_details_data = customer_details()
                customer_details_data.org_name = page_details.find_element(By.XPATH,"//*[contains(text(),'Nom et adresse officiels de ')]//following::span[1]").get_attribute('innerHTML')
                try:
                    customer_main_activity=fn.get_string_between(notice_text,"ACTIVITÉ PRINCIPALE","Section II : ")
                    if 'Autre activité : ' in customer_main_activity:
                        customer_details_data.customer_main_activity = customer_main_activity.split('Autre activité : ')[1]
                    else:
                        customer_details_data.customer_main_activity = customer_main_activity
                except Exception as e:
                    logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                    pass 
                
                try:
                    type_of_authority_code = fn.get_string_between(notice_text,'TYPE DE POUVOIR ADJUDICATEUR','I.5) ACTIVITÉ PRINCIPALE')
                    if 'Autre type :' in type_of_authority_code:
                        customer_details_data.type_of_authority_code = type_of_authority_code.split('Autre type :')[1]
                    else:
                        customer_details_data.type_of_authority_code = type_of_authority_code
                except:
                    pass
                
                try:
                    if 'Téléphone :' in notice_text:
                        customer_details_data.org_address = fn.get_string_between(notice_text,'Adresse :','Téléphone :')
                    if 'Courriel :' in notice_text:
                        customer_details_data.org_address = fn.get_string_between(notice_text,'Adresse :','Courriel :')
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass            

                try:
                    customer_details_data.org_website= page_details.find_element(By.XPATH,"(//*[contains(text(),'Adresse internet')]//following-sibling::span[2])[1]").text
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass        

                try:
                    org_email = page_details.find_element(By.XPATH,"//*[contains(text(),'Courriel ')]//following::span[1]").get_attribute('innerHTML')
                    email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
                    customer_details_data.org_email = email_regex.findall(org_email)[0]
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass 

                try:
                    customer_details_data.org_phone= page_details.find_element(By.XPATH,' //*[contains(text(),"Téléphone :")]//following::span[1]').get_attribute('innerHTML')
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass      

                try:
                    customer_details_data.customer_nuts = fn.get_string_between(notice_text,"Lieu d'exécution","Lieu principal d'exécution :").split(':')[1]
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


            try:
                notice_data.document_type_description = notice_text.split("TYPE D'AVIS :")[1].split('\n')[0].strip()  
            except Exception as e:
                logging.info("Exception in document_type_description: {}".format(type(e).__name__))
                pass 

            try:
                notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'label.fr-my-0.fr-text--lg.fr-text--regular.ng-binding').text.split('Avis n° ')[1]     
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass   

            try:
                notice_data.local_description = notice_text.split('Description succincte :')[1].split('\n')[0]
                notice_data.notice_summary_english = GoogleTranslator(source='fr', target='en').translate(notice_data.local_description)
            except:
                pass

            try:
                notice_data.local_title = page_details.find_element(By.CSS_SELECTOR,"span.fr-my-0.fr-h4.ng-binding").text
                notice_data.notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title)
            except Exception as e:
                logging.info("Exception in local_title: {}".format(type(e).__name__))
                pass
            try:
                notice_data.additional_tender_url  = page_details.find_element(By.XPATH,"//*[contains(text(),'Soumission des offres et des demandes de participation par voie électronique :')]//following::a[1]").get_attribute('innerHTML')
            except Exception as e:
                logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
                pass

            try:
                notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procédure : ")]//following::span[1]').text
                type_of_procedure_actual = GoogleTranslator(source='fr', target='en').translate(notice_data.type_of_procedure_actual)
                notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_spn_procedure.csv",type_of_procedure_actual)
            except Exception as e:
                logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
                pass

            try:
                publish_date = page_details.find_element(By.CSS_SELECTOR, "#toplist > div > div > div > h2 > div > div > div.fr-grid-row.fr-col-12.fr-col-sm-4 > span").text
                publish_date = GoogleTranslator(source='fr', target='en').translate(publish_date)
                publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            try:
                notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Type de marché')]//following::td[3]").text
                if 'Fournitures' in notice_contract_type:
                    notice_data.notice_contract_type="Supply"
                if 'Services' in notice_contract_type:
                    notice_data.notice_contract_type="Service"
                if 'Travaux' in notice_contract_type:
                     notice_data.notice_contract_type="Works"
                notice_data.contract_type_actual =  notice_contract_type
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
                notice_data.class_at_source = "CPV" 
                cpvs_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Code CPV ')]//following::tr[1]").text
                cpv_regex = re.compile(r'\d{8}')
                cpvs_data = cpv_regex.findall(cpvs_code)
                for cpv in cpvs_data:
                    cpv_at_source = ''
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv
                    notice_data.cpvs.append(cpvs_data)            
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass

            try:
                cpv_at_source = ''
                if 'Ce marché est divisé en lots : non' in notice_text:
                    cpvs_code = page_details.find_element(By.CSS_SELECTOR, " tbody > tr > td > table:nth-child(19) > tbody").text
                    cpv_regex = re.compile(r'\d{8}')
                    all_cpv = cpv_regex.findall(cpvs_code)
                    for cpv in all_cpv:
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = cpv
                        notice_data.cpvs.append(cpvs_data)
                    for each_cpv in all_cpv:
                        cpv_at_source += each_cpv
                        cpv_at_source += ','
                        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
                else:
                    pass
            except:
                pass

            try:
                notice_data.class_at_source = "CPV" 
                for singlerecord in page_details.find_elements(By.XPATH, "//*[contains(text(),'Code CPV ')]//following::tr[1]"):
                    cpv_at_source += singlerecord.text.split(':')[1].strip()
                    cpv_at_source += ','
                notice_data.cpv_at_source = cpv_at_source.rstrip(',')
                logging.info(notice_data.cpv_at_source)
            except:
                pass


            try:
                netbudgetlc=page_details.find_element(By.XPATH, "//*[contains(text(),'Valeur totale estimée : ')]//following::tr[1]").text.split(':')[1]
                netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
                notice_data.netbudgetlc =float(netbudgetlc.replace(' ','').strip())
                notice_data.est_amount= notice_data.netbudgetlc  
            except Exception as e:
                logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
                pass

            try:
                notice_data.netbudgeteuro = notice_data.netbudgetlc
            except Exception as e:
                logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
                pass

            try:
                contract_duration=page_details.find_element(By.XPATH, "//*[contains(text(),'Durée du marché')]//following::tr[1]").text
                notice_data.contract_duration = GoogleTranslator(source='auto', target='en').translate(contract_duration)
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass   

            try:
                notice_data.related_tender_id=page_details.find_element(By.XPATH, "//*[contains(text(),'Intitulé :')]//following::tr[1]").text.split(':')[1].strip()
            except:
                pass
            lot_title = ''
            try:
                lot_number = 1
                for lot in page_details.find_elements(By.XPATH, '//*[contains(text(),"Information sur les lots :")]//following::tbody'):
                    lot = lot.text
                    if 'Intitulé' in lot or 'Lot nº :' in lot or 'Code CPV principal : ' in lot:
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
                                lot_details_data.contract_type=notice_data.notice_contract_type
                                lot_details_data.lot_contract_type_actual = notice_contract_type
                            except Exception as e:
                                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                                pass    

                            try:
                                lot_details_data.lot_description = lot.split('Description des prestations : ')[1].split('\n')[0].strip()
                                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                            except Exception as e:
                                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                                pass 

                            try:
                                contract_duration = notice_text.split('Durée en mois : ')[1].split('\n')[0]
                                contract_duration = 'Durée en mois : ' +  contract_duration
                                lot_details_data.contract_duration= GoogleTranslator(source='auto', target='en').translate(contract_duration)
                            except Exception as e:
                                logging.info("Exception in  contract_duration: {}".format(type(e).__name__))
                                pass 

                            try:
                                 lot_details_data.contract_number=fn.get_string_between(notice_text,'Référence de TED : ','- annonce')
                            except Exception as e:
                                logging.info("Exception in contract_number: {}".format(type(e).__name__))
                                pass    

                            try:
                                contract_start_date= notice_data.contract_duration 
                                contract_start_date1=GoogleTranslator(source='fr', target='en').translate(contract_start_date).split(":")[1].split('-')[0].strip()
                                lot_details_data.contract_start_date = datetime.strptime(contract_start_date1,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
                                contract_end_date1=GoogleTranslator(source='fr', target='en').translate(contract_start_date).split(":")[-1].split('\n')[0].strip()
                                lot_details_data.contract_end_date = datetime.strptime(contract_end_date1,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
                            except:
                                pass


                            try:
                                lot_netbudget_lc = lot.split('Valeur hors TVA :')[1].split('euros')[0].replace(' ','').replace(',','.').strip()

                                if lot_netbudget_lc != '':
                                    lot_details_data.lot_netbudget_lc=float(lot_netbudget_lc)
                                else:
                                    lot_netbudget_lc = lot.split('maximum annuel : ')[1].split('euros')[0].replace(' ','')

                                    lot_details_data.lot_netbudget_lc=float(lot_netbudget_lc)
                            except Exception as e:
                                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                                pass    

                            try:
                                lot_details_data.lot_netbudget=lot_details_data.lot_netbudget_lc
                            except Exception as e:
                                logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                                pass   

                            try:
                                lot_details_data.lot_nuts = fn.get_string_between(notice_text,"Lieu d'exécution","Lieu principal d'exécution :").split(':')[1]
                            except Exception as e:
                                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                                pass 

                            try:
                                for lott in lot.split('Code CPV principal : ')[1:]:
                                    lot_cpvs_data = lot_cpvs()
                                    lot_cpvs_data.lot_cpv_code = lott.split('\n')[0].strip()
                                    if lot_cpvs_data.lot_cpv_code != "":
                                        lot_cpvs_data.lot_cpvs_cleanup()
                                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                            except Exception as e:
                                logging.info("Exception in lot_cpv_code: {}".format(type(e).__name__))
                                pass 

                            try:
                                lot_cpv_at_source = ''
                                for singlerecord in lot.split('Code CPV principal : ')[1:]:
                                    lot_cpv_at_source += singlerecord.split('\n')[0].strip()
                                    lot_cpv_at_source += ','
                                lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                                logging.info(lot_details_data.lot_cpv_at_source)
                                notice_data.cpv_at_source += ','
                                notice_data.cpv_at_source += lot_details_data.lot_cpv_at_source
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
                                        else:
                                            lot_criteria_data.lot_criteria_title = 'technique'


                                        lot_criteria_data.lot_criteria_weight = l.split('/ Pondération :')[1].strip()
                                        lot_criteria_data.lot_criteria_weight = int(lot_criteria_data.lot_criteria_weight)

                                        if 'Prix' in l or 'PRIX' in l or 'prix' in l:
                                            lot_criteria_data.lot_is_price_related = True

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
                if lot_title == '':
                    try:
                        tender_criteria_title = notice_text.split("Critères d'attribution")[1].split("II.2.6) Valeur estimée")[0].strip()
                        for l in tender_criteria_title.split('\n'):
                            if 'Pondération' in l or 'VALEUR TECHNIQUE' in l:
                                tender_criteria_data = tender_criteria()
                                tender_criteria_title = l.split('/ Pondération')[0].strip()
                                if 'valeur technique' in tender_criteria_title.lower():
                                    tender_criteria_data.tender_criteria_title = 'Valeur technique'
                                elif 'technique' in tender_criteria_title.lower():
                                    tender_criteria_data.tender_criteria_title = 'technique'
                                elif 'prix des prestations' in tender_criteria_title.lower():
                                    tender_criteria_data.tender_criteria_title = 'Prix des prestations'
                                elif 'prix' in tender_criteria_title.lower():
                                    tender_criteria_data.tender_criteria_title = 'Prix'
                                else:
                                    tender_criteria_data.tender_criteria_title = 'technique'


                                tender_criteria_data.tender_criteria_weight = int(l.split('/ Pondération :')[1].strip())
                                if 'Prix' in l or 'PRIX' in l or 'prix' in l:
                                    tender_criteria_data.tender_is_price_related = True
                                else:
                                    tender_criteria_data.tender_is_price_related = False

                                tender_criteria_data.tender_criteria_cleanup()
                                notice_data.tender_criteria.append(tender_criteria_data)
                    except Exception as e:
                        logging.info("Exception in tender_criteria: {}".format(type(e).__name__))
                        pass
            except:
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
            
        elif 'Adresse :' in text1:
            try:
                notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'a').text
                notice_data.notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title)
            except:
                pass
            try:
                notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'h2 > div > div > div.fr-grid-row.fr-col-12.fr-col-sm-8 > div > label').text.split('Avis n° ')[1]
            except:
                pass
            try:
                notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'div.card-notification-info.fr-scheme-light-white.fr-p-5v.fr-mb-4w > ul > li:nth-child(3) > span.ng-binding').text 
            except Exception as e:
                logging.info("Exception in document_type_description: {}".format(type(e).__name__))
                pass 
            try:
                notice_data.type_of_procedure_actual =  tender_html_element.find_element(By.CSS_SELECTOR,'div.card-notification-info.fr-scheme-light-white.fr-p-5v.fr-mb-4w > ul > li:nth-child(4) > span.ng-binding').text 
                type_of_procedure_actual = GoogleTranslator(source='fr', target='en').translate(notice_data.type_of_procedure_actual)
                notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_spn_procedure.csv",type_of_procedure_actual)
            except Exception as e:
                logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
                pass
            try:
                publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.fr-grid-row.fr-col-12.fr-col-sm-4").text
                publish_date = GoogleTranslator(source='fr', target='en').translate(publish_date)
                publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            try:
                notice_data.additional_tender_url = add_url
            except:
                pass
            
            try:
                customer_details_data = customer_details()

                customer_details_data.org_name = page_details.find_element(By.XPATH,"//*[contains(text(),'Acheteur : ')]//following::span[1]").text

                try:
                    customer_details_data.customer_main_activity=page_details.find_element(By.XPATH,'//*[contains(text(),"Activité du pouvoir adjudicateur")]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                    pass 
                try:
                    customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH,'//*[contains(text(),"Forme juridique de l’acheteur")]//following::span[2]').text
                except:
                    pass
                try:
                    customer_details_data.org_address = address
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass            
                try:
                    customer_details_data.org_website= page_details.find_element(By.XPATH,'''(//*[contains(text(),'Adresse internet')]//following-sibling::span[2])[1]''').text
                except Exception as e:
                    logging.info("Exception in org_description: {}".format(type(e).__name__))
                    pass    
                try:
                    customer_details_data.contact_person= contact_person
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass     

                try:
                    customer_details_data.org_email = email
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass 

                try:
                    customer_details_data.org_phone= telephone
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass  

                try:
                    customer_details_data.postal_code= page_details.find_element(By.XPATH,'(//*[contains(text(),"Code postal")])[1]//following::span[2]').text
                except Exception as e:
                    logging.info("Exception in postal_code: {}".format(type(e).__name__))
                    pass  

                try:
                    customer_details_data.customer_nuts =  page_details.find_element(By.XPATH,'(//*[contains(text(),"Subdivision pays (NUTS)")])[1]//following::span[3]').text
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

            try:
                dispatch_date = notice_text.split("Date d'envoi du présent avis à la publication :")[1].split('\n')[0]
                dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
                notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
                pass 
            
            try:
                notice_data.related_tender_id=page_details.find_element(By.XPATH,'//*[contains(text(),"Référence de TED")]//following::a[1]').text
            except:
                pass
            
            try:
                notice_data.local_description = page_details.find_element(By.XPATH,'(//*[contains(text(),"Description")])[1]//following::span[2]').text
                notice_data.notice_summary_english = GoogleTranslator(source='fr', target='en').translate(notice_data.local_description)
            except:
                pass

            try:
                netbudgetlc=notice_text.split('Valeur estimée hors TVA : ')[1].split('\n')[0]
                netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
                notice_data.netbudgetlc =float(netbudgetlc.replace(',','').strip())
                notice_data.est_amount= notice_data.netbudgetlc  
            except Exception as e:
                logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
                pass

            try:
                notice_data.netbudgeteuro = notice_data.netbudgetlc
            except Exception as e:
                logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
                pass

            try:
                notice_contract_type = page_details.find_element(By.XPATH, "(//*[contains(text(),'Nature du marché')])[1]//following::span[2]").text
                if 'Fournitures' in notice_contract_type:
                    notice_data.notice_contract_type="Supply"
                if 'Services' in notice_contract_type:
                    notice_data.notice_contract_type="Service"
                if 'Travaux' in notice_contract_type:
                     notice_data.notice_contract_type="Works"
                if 'Marché de travaux' in notice_contract_type:
                    notice_data.notice_contract_type="Works"
                notice_data.contract_type_actual =  notice_contract_type
            except Exception as e:
                logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                pass

            notice_data.class_at_source = "CPV" 
            try:
                cpv1  =fn.get_string_between(notice_text,'2.1.1 Objet','2.1.')
                cpv_regex = re.compile(r'\d{8}')
                cpvs_data = cpv_regex.findall(cpv1)
                for cpv in cpvs_data:
                    cpv_at_source = ''
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv
                    notice_data.cpvs.append(cpvs_data) 
                    notice_data.cpv_at_source = cpv +','
                notice_data.cpv_at_source = notice_data.cpv_at_source.rstrip(',')
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass

            try:
                notice_data.category = page_details.find_element(By.XPATH, "(//*[contains(text(),'Nomenclature principale')])[1]//following::span[6]").text
            except:
                pass

            try:
                netbudgetlc = page_details.find_element(By.XPATH, "(//*[contains(text(),'Valeur maximale de l’accord-cadre')])[1]//following::span[2]").text
                netbudgetlc = netbudgetlc.replace(',','')
                notice_data.netbudgetlc = float(netbudgetlc)
                notice_data.netbudgeteuro = notice_data.netbudgetlc
            except:
                pass

            try:
                lot_number = 1
                for lot in page_details.find_elements(By.XPATH, "//*[contains(text(),'Section 5')]//following-sibling::div"):
                    lot = lot.text
                    if 'Lot' in lot or 'lot' in lot or 'LOT' in lot:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number

                        lot_details_data.lot_title =lot.split('Titre :')[1].split('\n')[0]
                        lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)
                        try:
                            lot_details_data.lot_actual_number =lot.split('5.1')[1].split(':')[1].split('\n')[0]
                        except Exception as e:
                            logging.info("Exception in lot_actual: {}".format(type(e).__name__))
                            pass 

                        try:
                            lot_details_data.contract_type=notice_data.notice_contract_type
                            lot_details_data.lot_contract_type_actual = notice_contract_type
                        except Exception as e:
                            logging.info("Exception in contract_type: {}".format(type(e).__name__))
                            pass    

                        try:
                            lot_details_data.lot_description = lot.split('Description : ')[1].split('\n')[0]
                            lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                        except Exception as e:
                            logging.info("Exception in lot_description: {}".format(type(e).__name__))
                            pass 

                        try:
                            contract_duration = notice_text.split('Durée : ')[1].split('\n')[0]
                            contract_duration = 'Durée : ' +  contract_duration
                            lot_details_data.contract_duration= GoogleTranslator(source='auto', target='en').translate(contract_duration)
                        except Exception as e:
                            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                            pass 


                        try:
                            lot_details_data.lot_netbudget_lc = lot.split('Valeur estimée hors TVA :')[1].split('EUR')[0]
                            lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget_lc.replace(',','').strip()
                            lot_details_data.lot_netbudget_lc = float(lot_details_data.lot_netbudget_lc)
                            lot_details_data.lot_netbudget=lot_details_data.lot_netbudget_lc
                        except Exception as e:
                            logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
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


                        try:
                            lot_details_data.contract_start_date = lot.split('Date de début : ')[1].split('\n')[0]
                            lot_details_data.contract_start_date = datetime.strptime(lot_details_data.contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            pass


                        lot_details_data.lot_class_codes_at_source="CPV"
                        try:
                            for lot1 in page_details.find_elements(By.XPATH, "//*[contains(text(),'Critères d’attribution')]//following-sibling::div"):
                                lot1=lot1.text
                                lot_criteria_data = lot_criteria()

                                lot_criteria_data.lot_criteria_title = lot1.split('Type : ')[1].split('\n')[0].strip()

                                if 'Prix' in lot_criteria_data.lot_criteria_title:
                                    lot_criteria_data.lot_is_price_related = True

                                lot_criteria_data.lot_criteria_weight = lot1.split('Pondération (pourcentage, valeur exacte) :')[1].split('\n')[0].strip()
                                lot_criteria_data.lot_criteria_weight = int(lot_criteria_data.lot_criteria_weight)

                                lot_criteria_data.lot_criteria_cleanup()
                                lot_details_data.lot_criteria.append(lot_criteria_data) 
                        except:
                            pass

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__))
                pass   

            try:               

                attachments_data = attachments()

                attachments_data.file_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Obtenir un extrait de l’avis')]").text
                attachments_data.external_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Obtenir un extrait de l’avis')]").get_attribute("href")
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
        
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) +  str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
    keywords = ['24-16975','24-22667','24-22703','24-22692','24-22666','24-22683','24-24388','24-24394','24-24459','24-24465','24-24477','24-24526','24-24549','24-24555','24-24626','24-24631','24-24684','24-24689','24-24716','24-24762','24-24766','24-24776','24-24804','24-24845','24-24850','24-24377','24-24383','24-24496','24-24511','24-24588','24-24714','24-24755','24-24823','24-24825','24-24862','24-24375','24-24456','24-24503','24-24514','24-24515','24-24824','24-26191','24-28358','24-28376','24-28361','24-28362','24-28377','24-28371','24-28375','24-28363','24-28368','24-28379','24-28604','24-31813','24-31823','24-31825','24-31865','24-31890','24-31866','24-31904','24-35004','24-35036','24-34611','24-34621','24-35031','24-34799','24-34819','24-34760','24-34762','24-34743','24-34719','24-34727','24-34939','24-34942','24-35029','24-35030','24-35024','24-35023']
    for keyword in keywords:
        url = 'https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&q.idweb=idweb:'+str(keyword)
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            page_check = WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-notification.fr-callout.fr-py-4w.fr-px-3w.fr-px-md-6w.fr-mb-4w.ng-scope'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card-notification.fr-callout.fr-py-4w.fr-px-3w.fr-px-md-6w.fr-mb-4w.ng-scope')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.card-notification.fr-callout.fr-py-4w.fr-px-3w.fr-px-md-6w.fr-mb-4w.ng-scope')))[records]
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
