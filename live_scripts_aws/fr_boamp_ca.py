from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_boamp_ca"
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
        notice_data.notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Avis n°
    # Onsite Comment -None

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-grid-row > div.fr-checkbox-group > label').text
        notice_data.notice_no = re.findall('\d+-\d+',notice_no)[0]
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
        notice_data.type_of_procedure_actual = GoogleTranslator(source='fr', target='en').translate(type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_ca_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass
    # Onsite Field -Voir l’annonce
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-container> div > a').get_attribute("href")  
    except:
        pass
    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Section 1 ')]"))).text
        logging.info(notice_data.notice_url)
        
        try:
            summery=page_details.find_element(By.XPATH,'//*[contains(text(),"Objet du marché :")]//parent::li').text
        except:
            pass
     
    # Onsite Field -None
    # Onsite Comment -for notice text click on "Voir l'annonce" and take all data in notice txt

        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' #toplist > div > div > div > div:nth-child(4) > div > div.fr-grid-row.fr-col-12.fr-col-sm-6.ng-scope > button')))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(5)

        try:
            WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,' #odsResultEnumerator-t2u1idq > div > div > div > div:nth-child(7)')))
        except:
            pass

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass


    #     Onsite Field -Objet du marché :
    #     Onsite Comment -if "Objet du marché :" field is not available in detail page then take local_title as notice_summary_english

        try:
            notice_data.local_description = summery
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except:
            try:
                notice_data.local_description  = page_details.find_element(By.XPATH, "//*[contains(text(),'Description succincte du marché :')]//parent::div").text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate( notice_data.local_description)
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass

        # Onsite Field -Type de marché :
        # Onsite Comment -for notice_contract_type click on "Voir l'annonce" and  Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works ',' Fournitures = Supply')

        try:
            notice_data.contract_type_actual = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split("Type de marché :")[1].split('\n')[0]
            if "Services" in notice_data.contract_type_actual:
                notice_data.notice_contract_type="Service"
            elif "Travaux" in notice_data.contract_type_actual:
                notice_data.notice_contract_type="Work"
            elif "Fournitures" in notice_data.contract_type_actual:
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


        try:
            notice_data.related_tender_id = page_details.find_element(By.XPATH, "(//*[contains(text(),'Annonce n°')])[1]//following::span[2]").text
        except:
            try:
                notice_data.related_tender_id = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split("Références de publication rectificative, annonce no")[1].split(",")[0].strip()
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass

    # Onsite Field -ACHETEUR :
    # Onsite Comment -None

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            # Onsite Field -ACHETEUR :
            # Onsite Comment -None

            customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Acheteur : ')]//following::span[1]").text

            # Onsite Field -Courriel :
            # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split('Courriel :')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
            try:
                customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split('Ville : ')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split('Code postal : ')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split('Téléphone : ')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split('Adresse : ')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
            try:
                customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split('Télécopieur : ')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass  
            
            try:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text.split('Adresse internet : ')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass  
                

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        try:
            text1 = page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text
            cpv_code = re.findall('Code CPV principal - Descripteur principal : (\d+)',text1)[0]
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
            notice_data.class_at_source = "CPV"
            notice_data.cpv_at_source = cpv_code
        except:
            pass
        
        try:
            if "Critères d'attribution" in page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text:
                single_record = page_details.find_element(By.XPATH, '''//*[contains(text(),"Critères d'attribution :")]//parent::div''').text
                for lot in single_record.split('%'):
                    reg=re.finditer('(?P<title>.*?):\s*(?P<weight>\d+)',lot)
                    for match in reg:
                        tender_criteria_data = tender_criteria()
                        tender_criteria_data.tender_criteria_title = match.group('title').strip()
                        tender_criteria_data.tender_criteria_weight = int(match.group('weight'))
                        if 'prix' in tender_criteria_data.tender_criteria_title.lower() or 'pris ' in tender_criteria_data.tender_criteria_title.lower():
                            tender_criteria_data.tender_is_price_related = True
                        tender_criteria_data.tender_criteria_cleanup()
                        notice_data.tender_criteria.append(tender_criteria_data)
        except:
            pass                   
                    

        try:
            lot_number = 1
            lots =  page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').text.split("Renseignements relatifs à l'attribution du marché et/ou des lots :")[1]
            lot_name='marché no'
            
            if 'rousseau' in lots and 'montant maximum annuel' in lots:
                try:
                    lots1 =  page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').text.split("Renseignements relatifs à l'attribution du marché et/ou des lots :")[1]
                    split_data = lots1.split('lot no1 : ')[1].split('Lot 2 :')

                    lot1_data = split_data[0].strip()
                    lot2_data = split_data[1].strip()

                    lot1_data=lot1_data.split(' montant maximum annuel de')[1].split('euro')[0]
                    lot1_data=lot1_data.replace(' ','')
                    lot2_data=lot2_data.split(' montant maximum annuel de')[1].split('euro')[0]
                    lot2_data=lot2_data.replace(' ','')

                    data=page_details.find_element(By.CSS_SELECTOR, "div.card-notification").text
                    lots1 = fn.get_string_between(data,'Description succincte du marché :','Mots descripteurs :')
                    lot_number = 1
                    for i in lots1.split('Lot')[1:]:
                        lot_title=i.split(':')[1].split('-')[0]

                        lot_details_data = lot_details()

                        lot_details_data.lot_number=lot_number
                        lot_details_data.lot_actual_number='Lot' + str(lot_details_data.lot_number)
                        lot_details_data.lot_title = lot_title

                        award_details_data = award_details()
                        award_details_data.bidder_name='codes rousseau'

                        if lot_number==1:
                            lot1_data = split_data[0].strip()
                            lot1_data=lot1_data.split(' montant maximum annuel de')[1].split('euro')[0]
                            lot1_data=lot1_data.replace(' ','')
                            award_details_data.netawardvaluelc = float(lot1_data)


                        if lot_number==2:
                            lot2_data = split_data[1].strip()
                            lot2_data=lot2_data.split(' montant maximum annuel de')[1].split('euro')[0]
                            lot2_data=lot2_data.replace(' ','')
                            award_details_data.netawardvaluelc = float(lot2_data)

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data) 

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number +=1
                except:
                    pass

            elif 'Lot no' in lots:
                lot_number = 1
                for single_record in lots.split('Lot no')[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type

                        try:
                            lot_actual_number =single_record.split(':')[0].strip()
                            lot_details_data.lot_actual_number = 'Lot no'+str(lot_actual_number)
                        except:
                            pass

                        lot_details_data.lot_title =single_record.split(':')[1].split('Attribué :')[0]
                        lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)
               
                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split('Attributaire ')[1].split('Lot')[0].strip()

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
            
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass

            elif "Périmètre d'intervention" in lots[1:]:

                lot_number = 1
                for single_record in lots.split("Périmètre d'intervention"):
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type

                        try:
                            lot_actual_number = single_record.split(':')[0].strip()
                            lot_details_data.lot_actual_number = "Périmètre d'intervention "+str(lot_actual_number)
                        except:
                            pass

                        try:
                            lot_details_data.lot_title = single_record.split(':')[1].split("Attributaire ")[0]
                            lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)
                        except:
                            pass

                        try:
                            award_details_data = award_details()
                            award_details_data.bidder_name = single_record.split('Nom du Titulaire :')[1].split('Adresse :')[0].strip()
                            award_details_data.address = single_record.split('Adresse :')[1].split('Montant du marché ')[0].strip()
                            try:   
                                award_date = single_record.split("Date d'attribution :")[1].split('Nom du Titulaire :')[0].strip()
                                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                            except:
                                pass
                            award_details_data.award_details_cleanup()
                            lot_details_data.award_details.append(award_details_data)
                        except:
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
                        elif lot_details_data.lot_title is not None and lot_details_data.award_details != []:
                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number += 1
                    except:
                        pass
                    
                    
            elif 'LOT 1 -' in lots:

                lot_number = 1
                for single_record in lots.split('LOT')[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type

                        try:
                            lot_actual_number =single_record.split('LOT')[0].strip()
                            lot_details_data.lot_actual_number = 'Lot N° :'+ str(lot_actual_number)
                        except:
                            pass

                        lot_details_data.lot_title =single_record.split('-')[1].split(" ;")[0]
                        lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)


                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass

            elif lot_name.lower() in lots:

                lot_number = 1
                for single_record in lots.split("marché no")[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type
                        try:
                            lot_details_data.lot_title =notice_data.notice_title
                            notice_data.is_lot_default = True
                            lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)
                        except:
                            pass
                        award_details_data = award_details()
                        
                        award_details_data.bidder_name = single_record.split('montant Ht : ')[0].strip()
                        award_details_data.bidder_name = re.findall('(\S+.*),',award_details_data.bidder_name)[0]
                        award_details_data.bidder_name = award_details_data.bidder_name.split(':')[1].strip()
                        
                        try:
                            award_date = lots.split('marché no : ')[0].split("date d'attribution :")[1]
                            month, day, two_digit_year = map(int, award_date.split('/'))
                            award_date = 2000 + two_digit_year
                            award_date = datetime(year=award_date, month=month, day=day)
                            award_details_data.award_date = award_date.strftime('%Y/%m/%d')
                        except:
                            pass

                        try:
                            netawardvalueeuro = single_record.split('montant Ht : ')[1].split('Euro')[0]
                            if 'à ' in netawardvalueeuro:
                                netawardvalueeuro = single_record.split('montant Ht : ')[1].split('Euro')[0].split('à ')[1]
                            else:
                                netawardvalueeuro = netawardvalueeuro
                            netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                            netawardvalueeuro = netawardvalueeuro.replace(',','.')
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                            award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                        except:
                            pass


                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass

            elif "marché/lot:" in lots:

                lot_number = 1
                for single_record in lots.split('marché/lot:')[1:]:

                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title

                        award_details_data = award_details()

                        try:
                            award_details_data.bidder_name = single_record.split('nom du titulaire:')[1].split('Date')[0].strip()
                        except:
                            award_details_data.bidder_name = single_record.split('noms des titulaires: ')[1].split('\n')[0]

                        try:
                            award_date = single_record.split('noms des titulaires: ')[0].strip()
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass


            elif "Attribution du LOT " in lots:

                lot_number = 1
                for single_record in lots.split("LOT")[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type

                        try:
                            lot_actual_number = single_record.split(':')[0].strip()
                            lot_details_data.lot_actual_number = "LOT"+str(lot_actual_number)
                        except:
                            pass

                        award_details_data = award_details()

                        award_details_data.bidder_name = single_record.split('itulaire du lot :')[1].split("Date d'attribution")[0].strip()


                        try:
                            award_date = single_record.split("Date d'attribution : ")[1].split('Montant du')[0].strip()
                            award_date = GoogleTranslator(source='fr', target='en').translate(award_date)
                            award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
                            logging.info(award_details_data.award_date)
                        except:
                            pass

                        try:
                            netawardvalueeuro = single_record.split('niveau des offres')[1].split('euro')[0]

                            netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                            netawardvalueeuro = netawardvalueeuro.replace(',','.')
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                            award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_title =single_record.split('lot')[1].split(",")[0]
                        lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass

            elif "Date d'attribution" in lots and "Nombre d'offres" in lots:

                lot_number = 1
                for single_record in lots.split("Nombre d'offres reçues ")[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_title = notice_data.notice_title
                        notice_data.is_lot_default = True

                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split('Marché n° :')[1].split(',')[0]

                        try:
                            award_date = single_record.split(" Date d'attribution : ")[1].split(' Marché n° :')[0].strip()
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%y').strftime('%Y/%m/%d')
                        except:
                            pass

                        try:
                            award_details_data.address = single_record.split('Marché n° : ')[1].split('Montant Ht ')[0]
                        except:
                            pass

                        try:
                            netawardvalueeuro = single_record.split('Montant Ht ')[1].split('Euros')[0]
                            netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                            netawardvalueeuro= netawardvalueeuro.replace(',','.').replace(' ','')
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                            award_details_data.netawardvaluelc  = award_details_data.netawardvalueeuro 
                        except: 
                            try:
                                netawardvalueeuro = single_record.split('Montant Ht de ')[1].split('à')[1].split('Euros')[0]
                                netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                                netawardvalueeuro = netawardvalueeuro.replace(',','.').replace(' ','')
                                award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                                award_details_data.netawardvaluelc  = award_details_data.netawardvalueeuro
                            except:
                                pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass

            elif "titulaire du marché:" in lots:

                lot_number = 1
                for single_record in lots.split("titulaire du marché:")[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type
                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split("Montant du marché :-")[0].strip()
                        try:
                            netawardvalueeuro= single_record.split('montant forfaitaire de')[1].split('euro')[0]
                            netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                            netawardvalueeuro= netawardvalueeuro.replace(',','.')
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                        except:
                            pass

                        award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_title =single_record.split('lot')[1].split(",")[0]
                        lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass

            elif 'titulaire ' in lots and 'Lot' in lots:
                lot_number=1
                for single_record in lots.split('Lot')[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number= lot_number
                        lot_details_data.lot_title = single_record.split(':')[0]
                        lot_details_data.lot_title_english = GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)

                        lot_details_data.lot_actual_number = 'Lot' + str(lot_details_data.lot_number)

                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split("titulaire ")[1].split('(')[0].strip()

                        try:
                            award_details_data.address = single_record.split('(')[1].split(')')[0].strip()
                        except:
                            pass
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass

            elif "Lot" in lots and 'Attributaire ' in lots:
                lot_number=1
                for single_record in lots.split("Lot")[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type

                        lot_details_data.lot_title =single_record.split("Attributair")[0]

                        lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)
                        lot_title_english = lot_details_data.lot_title_english.split(':')[0]
                        lot_details_data.lot_actual_number = 'Lot' + str(lot_title_english)
                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split("Attributaire ")[1].split(',')[0].strip()
                        award_details_data.address = single_record.split("Attributaire")[1].split('Marché')[0].replace(award_details_data.bidder_name,'').strip()

                        try:
                            netawardvaluelc  = single_record.split('Montant : ')[1].split('euro')[0]
                            netawardvaluelc  =  re.sub("[^\d\.\,]","", netawardvaluelc )
                            try:
                                netawardvaluelc = netawardvaluelc .replace('.','').replace(',','.')
                            except:
                                netawardvaluelc = netawardvaluelc .replace('','').replace(',','.')                               
                            award_details_data.netawardvaluelc  =float(netawardvaluelc )
                            award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass
                    
            elif "Date d'attribution" in lots and 'Marché n°' in lots:
                for single_record in lots.split("Date d'attribution")[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title

                        award_details_data = award_details()

                        award_details_data.bidder_name = single_record.split("Marché n°")[1].split(',')[0].strip()

                        try:
                            award_details_data.address = single_record.split("Marché n°")[1].split('Montant ')[0].strip()
                        except:
                            pass
                        try:
                            award_date = single_record.split("Marché n°")[0].strip()
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                        except:
                            pass
                        try:
                            netawardvalueeuro = single_record.split('Montant Ht :')[1].split('Euros')[0]
                            netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                            netawardvalueeuro  = netawardvalueeuro.replace(' ','').replace(',','.')
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                            award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass
                        
            elif 'Lot N°' in lots:
                lot_number = 1
                for single_record in lots.split('Lot N°')[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type

                        try:
                            lot_actual_number =single_record.split('-')[0].strip()
                            lot_details_data.lot_actual_number = 'Lot N° :'+ str(lot_actual_number)
                        except:
                            pass
                        try:
                            lot_details_data.lot_title =single_record.split('-')[1].split("Date")[0]
                        except:
                            lot_details_data.lot_title =single_record.split('-')[1].split("Lot")[0]

                        lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)

                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split('Marché n°')[1].split(',')[0].strip()

                        try:
                            award_details_data.address = single_record.split('Marché n°')[1].split(' Montant')[0].strip()
                        except:
                            pass

                        try:
                            netawardvalueeuro = single_record.split('Montant Ht ')[1].split('Euros')[0]
                            netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                            netawardvalueeuro= netawardvalueeuro.replace(',','.').replace(' ','')
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                            award_details_data.netawardvaluelc  = award_details_data.netawardvalueeuro 
                        except: 
                            try:
                                netawardvalueeuro = single_record.split('Montant Ht de ')[1].split('à')[0]
                                netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                                netawardvalueeuro= netawardvalueeuro.replace(',','.').replace(' ','')
                                award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                                award_details_data.netawardvaluelc  = award_details_data.netawardvalueeuro
                            except:
                                pass
                        try:
                            award_date = single_record.split("Date d'attribution : ")[1].split('Marché n° :')[0].strip()
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%y').strftime('%Y/%m/%d')
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1 
                    except:
                        pass

            elif 'Lot' in lots:
                lot_number = 1
                data1=lots.title()
                try:
                    for single in data1.split('Lot')[1:]:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type

                        lot_details_data.lot_number=lot_number

                        lot_details_data.lot_actual_number= 'lot' + str(lot_details_data.lot_number)
                        lot_details_data.lot_title =notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title

                        award_details_data = award_details()
                        
                        award_details_data.bidder_name = single.split(':')[1].split(',')[0]
                        try:
                            award_details_data.address = single.split(',')[1].split(':')[0]
                        except:
                            pass
                        
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                except:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type

                        lot_details_data.lot_number=lot_number

                        lot_details_data.lot_actual_number= 'lot' + str(lot_details_data.lot_number)

                        lot_details_data.lot_title = lots.split(':')[1].split(':')[0].strip()

                        award_details_data = award_details()

                        award_details_data.bidder_name = lots.split('entreprise(s) -')[1].split('(')[0]
                        try:
                            award_details_data.netawardvalueeuro = float(lots.split('Montant : ')[1].split('euros')[0])
                        except:
                            pass

                        try:
                            award_date = lots.split('Notifié le ')[1].split('Montant')[0].strip()
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                    except:
                        pass
                    
            elif 'Le marché est ' in lots:
                lot_number = 1 
                for single_record in lots.split('Le marché est attribué à la ')[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title
                        lot_details_data.lot_number=lot_number

                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split(':')[1].split('\n')[0]

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass
                        
            elif 'Nom du titulaire : ' in lots:
                for single_record in lots.split('Nom du titulaire : ')[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title

                        award_details_data = award_details()

                        award_details_data.bidder_name = single_record.split("marché attribué")[0].strip()

                        try:
                            award_date = single_record.split("Date d'attribution du marché : ")[1].strip()
                            award_date = GoogleTranslator(source='fr', target='en').translate(award_date)
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                        except:
                            pass
                        try:
                            netawardvalueeuro = single_record.split('marché attribué H.T. :')[1].split('euros')[0]
                            netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                            netawardvalueeuro  = netawardvalueeuro.replace(' ','')
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                            award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                        except:
                            pass
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass
                    
            elif 'Titulaire' in lots :
                if 'Le présent marché,' in lots:
                    for single_record in lots.split('Le présent marché,')[1:]:

                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title

                        award_details_data = award_details()
                        try:
                            award_details_data.bidder_name = single_record.split("Titulaire : ")[1].split(',')[0].strip()
                        except:
                            pass
                        award_details_data.address = single_record.split("Titulaire : ")[1].split('(')[0].strip()
                        try:
                            award_date = single_record.split(",")[0].strip()
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                        except:
                            pass
                        try:
                            netawardvalueeuro = single_record.split('marché attribué H.T. :')[1].split('euros')[0]
                            netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                            netawardvalueeuro  = netawardvalueeuro.replace(' ','')
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)

                            award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                else:
                    for single_record in lots.split('Titulaire ')[1:]:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title

                        award_details_data = award_details()

                        award_details_data.bidder_name = single_record.split(',')[0].strip()
                        try:
                            award_details_data.address = single_record.split('date d')[0].strip()
                        except:
                            pass

                        try:
                            award_date = single_record.split("date d'attribution :")[1].split("Montant")[0].strip()
                            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                        except:
                            pass
                        try:
                            netawardvalueeuro = single_record.split('Montant : ')[1].split('€HT')[0]
                            netawardvalueeuro =  re.findall("\d+", netawardvalueeuro)[0]
                            award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                            award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                        except:
                            pass

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1

            elif 'Siret' in lots:

                lot_number = 1
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type

                lot_details_data.lot_title =notice_data.local_title
                notice_data.is_lot_default = True
                lot_details_data.lot_title_english =notice_data.notice_title
                
                award_details_data = award_details()
                award_details_data.bidder_name = lots.split('Toulouse')[0]

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
        
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1

        except Exception as e:
            logging.info("Exception in lot: {}".format(type(e).__name__)) 
            pass

        try:
            lots =  page_details.find_element(By.CSS_SELECTOR, 'div.card-notification').text
            if "Numéro du marché ou du lot" in lots:

                lot_number = 1
                for single_record in lots.split('Numéro du marché ou du lot')[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_title = single_record.split('Nom du titulaire ')[0]
                        lot_details_data.lot_title_english = notice_data.notice_title

                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split('Nom du titulaire / organisme :')[1].split('Montant final')[0].strip()

                        award_date = single_record.split("Date d'attribution du marché : ")[1].split('.')[0].strip()

                        award_date = GoogleTranslator(source='fr', target='en').translate(award_date)

                        award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')


                        logging.info(award_details_data.award_date)
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass

            elif "Nom du titulaire / organisme :" in lots or 'Attribution(s) du marché' in lots:

                lot_number = 1
                if 'Lot(s)' in lots:
                    lot_number = 1
                    for single_record in lots.split('Attribution(s) du marché')[1:]:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_actual_number = single_record.split('Lot(s)')[1].split("-")[0]
                        lot_details_data.lot_title = single_record.split('Lot(s)')[1].split("\n")[0]

                for single_record in lots.split('Nom du titulaire / organisme :')[1:]:

                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number

                    try:
                        lot_details_data.lot_title = notice_data.notice_title
                        notice_data.is_lot_default = True
                    except:
                        pass

                    award_details_data = award_details()

                    award_details_data.bidder_name = single_record.split("\n")[0].strip()
                    try:
                        award_details_data.address = single_record.split("Adresse :")[1].split('\n')[0].strip()
                    except:
                        pass
                    try:
                        netawardvaluelc = single_record.split("Montant (H.T.) : ")[1].split('\n')[0].strip()
                        award_details_data.netawardvaluelc = float(re.findall('\d+',netawardvaluelc)[0])
                        award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                    except:
                        pass

                    try:
                        award_date = single_record.split("Date d'attribution du marché : ")[1].split('\n')[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                    except:
                        pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1

            elif 'Attributaire' in lots:
                lot_number = 1
                for single_record in lots.split('Attributaire : ')[1:]:
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                        lot_details_data.lot_title_english = notice_data.notice_title

                        award_details_data = award_details()
                        award_details_data.bidder_name = single_record.split('HoudemontMontant')[0]

                        netawardvalueeuro = single_record.split(' HoudemontMontant :')[1].split('euro')[0]
                        netawardvalueeuro =  re.sub("[^\d\.\,]","", netawardvalueeuro)
                        netawardvalueeuro  = netawardvalueeuro(',','').replace(' ','').strip()
                        award_details_data.netawardvalueeuro =float(netawardvalueeuro)
                        award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro

                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass
        except:
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

    except:
        pass     

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.publish_date) +str(notice_data.local_title)
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
    urls = ['https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&refine.type_avis=10&refine.famille=MAPA&refine.famille=FNS'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,50): #50
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
