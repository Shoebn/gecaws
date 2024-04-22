#after opening the url in "Type d'annonce" select "Annonce d'attribution=Award Announcement". Then click on "Lancer la recherche".
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []

#for cpv
#Case 1 : Tender CPV given, but lot CPV not given, than it will not be repeated in Lots.
#Case 2: Tender CPV not given, lots CPV Given. it will be repeated in Tender CPV comma separated.
#Case 3: Tender CPV given, lot CPV also given, In this case also lot CPVs will be repeated in Tender CPV comma separated. But in this make sure that Tender CPV should be first followed by lot CPVs.


from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_marchespublics_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_marchespublics_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'fr_marchespublics_ca'
    notice_data.main_language = 'FR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    notice_data.currency = 'EUD'
    notice_data.notice_type = 7
    
    try:
        publish_date_en = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-2 > div > div:nth-child(2) > div.date").text.replace('\n',' ')
        publish_date_en = GoogleTranslator(source='fr', target='en').translate(publish_date_en)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date_en)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    
    # Onsite Field -None
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Services=Service','Travaux=Works','Fournitures=Supply')

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text
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
    
    # Onsite Field -Objet :
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation > div:nth-child(2) > div > span:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.actions > ul.list-unstyled > li:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:                                                                        
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation > div > div  > div:nth-child(1)').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('id=')[-1].split('&')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -1.here "https://marchespublics596280.fr/?page=Entreprise.EntrepriseDetailsConsultation&id=506973&orgAcronyme=20206" take "506973" in notice_no.
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.m-b-10').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
        notice_data.notice_summary_english = GoogleTranslator(source='fr', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type d'annonce :
    # Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '''//*[contains(text(),"Type d'annonce :")]//following::span[1]''').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procédure :
    # Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),"Procédure :")]//following::span[1]''').text
        type_of_procedure = GoogleTranslator(source='fr', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marchespublics_ca_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
    # Onsite Field -Organisme :
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation > div:nth-child(3) > div > span:nth-child(2)').text

    # Onsite Field -None
    # Onsite Comment -1.here "(59) Nord" take only "Nord"

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation  > div:nth-child(4)').text.split(")")[1].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -1.split between "Correspondant :" and " Adresse internet du profil d'acheteur :".

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split('Correspondant :')[1].split("Adresse internet du profil d'acheteur :")[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -None
    # Onsite Comment -1.split between "Principale(s) Activité(s) du pouvoir adjudicateur :" and "."

        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split("Principale(s) Activité(s) du pouvoir adjudicateur :")[1].split('.')[0].strip()
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -None
    # Onsite Comment -1.split between "Code NUTS :" and "."

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split('Code NUTS :')[1].split('.')[0].strip()
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -ref_url:"https://marchespublics596280.fr/?page=Entreprise.EntrepriseDetailsConsultation&id=556781&orgAcronyme=3C029"

    try:              
        cpvs_data = cpvs()
    # Onsite Field -None
    # Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details.	2.if "Code CPV :(Code principal)" written as like above cpv should be blank .. and if this filed having numeric value than onlypass the cpv..

        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV :")]//following::span[1]').text.split("(")[1].split(")")[0].strip()
        if cpv_code.isdigit():
            cpvs_data.cpv_code = cpv_code
        else:
            cpvs_data.cpv_code = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split('CPV - Objet principal :')[1].split('-')[0].strip()

        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
        
# Onsite Field -None
# Onsite Comment -1.ref_url:"https://marchespublics596280.fr/?page=Entreprise.EntrepriseDetailsConsultation&id=556781&orgAcronyme=3C029" 	2.split between "Offre économiquement la plus avantageuse appréciée en fonction des critères énoncés ci-dessous avec leur pondération." and "Type de procédure :".

    try:              
        criteria = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split('pondération.')[1].split(".")[0].strip()
        for single_record in criteria.split('%'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -None
        # Onsite Comment -1.here "prix des prestations : 70 %; - valeur technique : 30 %" take only "prix des prestations".

            tender_criteria_data.tender_criteria_title = single_record.split('-')[1].split(':')[0].strip()
            if "prix" in tender_criteria_data.tender_criteria_title:
                tender_criteria_data.tender_is_price_related = True

        # Onsite Field -None
        # Onsite Comment -1.here "prix des prestations : 70 %; - valeur technique : 30 %" take only "70".

            tender_criteria_weight = single_record.split(':')[1].strip()
            tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text()," Avis de publicité")]//following::a[3]').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -None
    # Onsite Comment -1.split between "Valeur totale finale (HT) : " and "Attribution du marché :".

    try:
        est_amount = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split('Valeur totale finale (HT) :')[1].split("€")[0].strip()
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace(' ','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
    # Onsite Field -Objet
    # Onsite Comment -None

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
        lot_details_data.contract_type = notice_data.notice_contract_type
        # Onsite Field -None
        # Onsite Comment -ref_url:"https://marchespublics596280.fr/?page=Entreprise.EntrepriseDetailsConsultation&id=556781&orgAcronyme=3C029"

        try:
            award_details_data = award_details()

            # Onsite Field -None
            # Onsite Comment -1.split between "Nom du titulaire / organisme : " and "Date d'attribution du marché :".		2.here "Société Idonéis – 2 rampe Saint-Marcel – 02000 LAON" take only "Société Idonéis".

            award_details_data.bidder_name = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split('Nom du titulaire / organisme :')[1].split('–')[0].strip()

            # Onsite Field -None
            # Onsite Comment -1.split between "Nom du titulaire / organisme : " and "Date d'attribution du marché :".
            try:
                award_details_data.address = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split('Nom du titulaire / organisme :')[1].split("Date d'attribution du marché :")[0].strip()
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass
            # Onsite Field -None November 15, 2023
            # Onsite Comment -1.split between "Date d'attribution du marché : " and "Nombre total d'offres reçues : ".
            try:
                award_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text.split("Date d'attribution du marché :")[1].split("Nombre total d'offres reçues :")[0].strip()
                award_date_en = GoogleTranslator(source='fr', target='en').translate(award_date)
                award_date = re.findall('\w+ \d+, \d{4}',award_date_en)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        if lot_details_data.award_details !=[]:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
        
    try:              
        attachments_data = attachments()

        attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text()," Avis de publicité")]//following::a[1]').text

        attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text()," Avis de publicité")]//following::a[1]').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
    urls = ["https://marchespublics596280.fr/?page=Entreprise.EntrepriseAdvancedSearch&AllAnn"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#ctl0_CONTENU_PAGE_AdvancedSearch_annonceType')) 
        pp_btn.select_by_index(2) 
        time.sleep(2)
        
        scheight = .1
        while scheight < 9.9:
            page_main.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
            clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'''//*[@id="ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche"]'''))).click()
            break
        time.sleep(2)
        
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'''//*[@id="ctl0_CONTENU_PAGE_resultSearch_PagerBottom_ctl2"]''')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div[2]'),page_check))
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
