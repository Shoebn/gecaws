#refer this page detail url for fields "https://centraledesmarches.com/marches-publics/Douai-cedex-Commune-de-Douai-Accords-cadres-de-maintenance-d-espaces-verts/6838902"
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_cenedesmarch"
log_config.log(SCRIPT_NAME)
import re
import jsons
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
SCRIPT_NAME = "fr_cenedesmarch"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'fr_cenedesmarch'
    notice_data.main_language = 'FR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.entete').text
        notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title).replace('\n',' ').replace('\n ','')
        notice_data.notice_title = notice_title.replace('  ','')
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date de publication : split data fromDate de publication 'Date de publication'  till   'Publié dans'
    # Onsite Comment -skip first 5-6 records and then take publication date of remaining data

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.infoslegales").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "span.x-clear").text
        notice_deadline = re.findall('\d+/\d+/\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Voir le détail
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.liens > a').get_attribute("href")
        # notice_data.notice_url="https://centraledesmarches.com/marches-publics/Angers-Prefecture-Secretariat-General-Commun-Maine-et-Loire-Travaux-de-refection-d-etancheite-des-toitures-terrasses/7760264"
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Voir le détail
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content > div.wrapper').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass  
    
    try:
        res = page_details.find_element(By.CSS_SELECTOR, '#details').text
    except:
        pass
    
     # Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
    # Onsite Comment -split data from " Type de marché" till " Description succincte"

    try:
        notice_contract_type = res.split('Type de marché :')[1].split('\n')[0].strip()
        if 'travaux' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
                                                              
    # Onsite Field -split data from 'Type de procédure' till 'Conditions de participation'
    # Onsite Comment -ref url "https://centraledesmarches.com/marches-publics/In-Li-Revalorisation-et-renovation-thermique-en-milieu-occupe-d-une-residence-de-60-logements-a-Charenton-le-Pont-94/7794771"

    try:
        notice_data.type_of_procedure_actual = fn.get_string_between(res,'Type de procédure :','Conditions de participation :').strip()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_cenedesmarch_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
    # Onsite Comment -None
    
    try:
        notice_data.local_description = fn.get_string_between(res,'II.1.4) Description succincte :','II.1.5) Valeur totale estimée :').strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
    # Onsite Comment -take following  data from the selector  # //*[contains(text(),"IV.3) Date d'envoi du présent avis")]

    try:
        dispatch_date = res.split("DATE D'ENVOI DU PRÉSENT AVIS")[1].split('\n')[0].strip()
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        try:
            dispatch_date = re.findall('\d+ \w+ \d{4}',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%B/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -grab data from the keyword "Durée en mois : "
    # Onsite Comment -None

    try:
        contract_duration = res.split("Durée en")[1].split('\n')[0].strip()
        contract_duration1 = re.findall('\w+ : \d+',contract_duration)
        for item in contract_duration1:
            notice_data.contract_duration = item
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    # Onsite Field -take following data
    # Onsite Comment -None

    try:
        grossbudgetlc = res.split("Valeur totale du marché (hors TVA) :")[1].split('euros')[0].strip()
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace(' ','').replace(',','.').strip())
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
      
# Onsite Field -ref url "https://centraledesmarches.com/marches-publics/In-Li-Revalorisation-et-renovation-thermique-en-milieu-occupe-d-une-residence-de-60-logements-a-Charenton-le-Pont-94/7794771"
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.maitreouvrage > div.libelle').text
        

    # Onsite Field -ref url " https://centraledesmarches.com/marches-publics/In-Li-Revalorisation-et-renovation-thermique-en-milieu-occupe-d-une-residence-de-60-logements-a-Charenton-le-Pont-94/7794771"
    # Onsite Comment -spit data from "Code Postal : " to "Groupement de commandes"

        try:
            customer_details_data.postal_code = res.split("Code Postal :")[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -ref url "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
    # Onsite Comment -spit data from "Nom et adresses: " to "Tél  "

        try:
            customer_details_data.org_address = res.split('Nom et adresses :')[1].split('Tél :')[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -just take NUTS from following data

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Code NUTS")]').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

    # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
    # Onsite Comment -take following  data from the selector... split data from 'Tél' to 'courriel'

        try:  
            
            if 'Téléphone :' in res and 'Courriel' in res:
                customer_details_data.org_phone = res.split('Téléphone :')[1].split(', courriel :')[0].strip()
            elif 'Tél :' in res and 'courriel' in res:
                customer_details_data.org_phone = res.split('Tél :')[1].split(', courriel :')[0].strip()
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -ref url ="https://centraledesmarches.com/marches-publics/EHPAD-Les-Monts-Argentes-Cession-des-parcelles-AH-n-90-et-91-impasse-de-la-Madone-lieu-dit-Buisson-Char/7794968"
    # Onsite Comment -take following  data from the selector... split data from 'courriel' to  'adresse'

        try:
            org_email = res.split('courriel')[1].split('adresse')[0].strip()
            customer_details_data.org_email = fn.get_email(org_email)
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -ref url "https://centraledesmarches.com/marches-publics/In-Li-Revalorisation-et-renovation-thermique-en-milieu-occupe-d-une-residence-de-60-logements-a-Charenton-le-Pont-94/7794771"
    # Onsite Comment -spit data from "Ville: " to "Code Postal "

        try:
            customer_details_data.org_city = res.split('Ville : ')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'FR'
        customer_details_data.org_country = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
# Onsite Comment -None
    try:
        lot_number = 1
        lots = page_details.find_element(By.CSS_SELECTOR, '#content > div.wrapper').text.split('II.2) Description')
        for lot in lots:
            if 'Lot' in lot:
                lot_details_data = lot_details()
        # Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
        # Onsite Comment -split data from " Type de marché" till " Description succincte"

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_description = notice_data.notice_summary_english
                if '' in lot_details_data.lot_description or None in lot_details_data.lot_description:
                    lot_details_data.lot_description = notice_data.notice_title
            # Onsite Field -None
            # Onsite Comment -just take lot title  II.2.1) Intitulé :

                try:
                    lot_title = lot.split(' Intitulé :')[1].split('\n')[0].strip()
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                    lot_details_data.lot_actual_number = lot.split(' Intitulé :')[1].split('\n')[1].split('\n')[0].strip()
                except:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True

                try:
                    lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
                except Exception as e:
                    logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_nuts = lot.split('Code NUTS :')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass
                
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Communaute-d-Agglomeration-Chauny-Tergnier-La-Fere-Concession-du-service-public-d-eau-potable/7794863"
# Onsite Comment -None

    try:
        cpvs_code = res.split('Code(s) CPV additionnel(s)')
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:
        data=page_details.find_element(By.CSS_SELECTOR, '#details').text
        if 'Sélection des offres sur les critères :' in data:
            tender_data = data.split('Sélection des offres sur les critères :')[1].split('10. Conditions de participation :')[0]
            t_data = tender_data.split('\n')[1:-1]
            for records in t_data:
                tender_criteria_data = tender_criteria()
                
                criteria_title = records.split(':')[1].split("(")[0].strip()
                tender_criteria_data.tender_criteria_title=GoogleTranslator(source='auto', target='en').translate(criteria_title)
                
        # Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Angers-Prefecture-Secretariat-General-Commun-Maine-et-Loire-Travaux-de-refection-d-etancheite-des-toitures-terrasses/7760264"
        # Onsite Comment -split data from "Sélection des offres sur les critères :"  to  " Conditions de participation"

#         # Onsite Field -ref url = "https://centraledesmarches.com/marches-publics/Angers-Prefecture-Secretariat-General-Commun-Maine-et-Loire-Travaux-de-refection-d-etancheite-des-toitures-terrasses/7760264"
#         # Onsite Comment -split data from "Sélection des offres sur les critères :"  to  " Conditions de participation"

                try:
                    tender_criteria_weight = records.split('(')[1].split('%')[0].strip()
                    tender_criteria_data.tender_criteria_weight =int(tender_criteria_weight)
                except Exception as e:
                    logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                    pass

                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:
        funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"européenne")]//following::td[3]').text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency or 'YES' in funding_agency or 'Yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
        else:
            pass
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ['https://centraledesmarches.com/marches-publics/liste-avancee?sort=date_publication+desc&rem_rmc_id=1&page=1'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/div[3]/div/div[2]/section'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[3]/div/div[2]/section')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[3]/div/div[2]/section')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[4]/div[3]/div/div[2]/section'),page_check))
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
    
