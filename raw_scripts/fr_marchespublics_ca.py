
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
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_marchespublics_ca"
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
    notice_data.script_name = 'fr_marchespublics_ca'
    
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
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-2 > div > div:nth-child(2) > div.date").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation > div:nth-child(1) > div  > div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -1.here "https://marchespublics596280.fr/?page=Entreprise.EntrepriseDetailsConsultation&id=506973&orgAcronyme=20206" take "506973" in notice_no.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.actions > ul.list-unstyled > li:nth-child(1) > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Services=Service','Travaux=Works','Fournitures=Supply')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet :
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation > div:nth-child(2) > div > span:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
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
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.m-b-10').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Détail de l'annonce :
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
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
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marchespublics_ca_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.identification_consultation'):
            customer_details_data = customer_details()
        # Onsite Field -Organisme :
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation > div:nth-child(3) > div > span:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.here "(59) Nord" take only "Nord"

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation  > div:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'FR'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)


        # Onsite Field -None
        # Onsite Comment -1.split between "Correspondant :" and " Adresse internet du profil d'acheteur :".

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split between "Principale(s) Activité(s) du pouvoir adjudicateur :" and "."

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split between "Code NUTS :" and "."

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

# Onsite Field -None
# Onsite Comment -ref_url:"https://marchespublics596280.fr/?page=Entreprise.EntrepriseDetailsConsultation&id=556781&orgAcronyme=3C029"

    try:              
        for single_record in page_details.find_elements(By.ID, '#collapseBodyInfo'):
            cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -1.click on "+" sign after the "div.panel-heading > h1" in page_details.	2.if "Code CPV :(Code principal)" written as like above cpv should be blank .. and if this filed having numeric value than onlypass the cpv..
            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Code CPV :")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
                
        # Onsite Field -None
        # Onsite Comment -1.split between "CPV - Objet principal :" and "."
            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
        

# Onsite Field -None
# Onsite Comment -1.ref_url:"https://marchespublics596280.fr/?page=Entreprise.EntrepriseDetailsConsultation&id=556781&orgAcronyme=3C029" 	2.split between "Offre économiquement la plus avantageuse appréciée en fonction des critères énoncés ci-dessous avec leur pondération." and "Type de procédure :".

    try:              
        for single_record in page_details.find_elements(By.ID, '#collapseBodyInfo'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -None
        # Onsite Comment -1.here "prix des prestations : 70 %; - valeur technique : 30 %" take only "prix des prestations".

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.here "prix des prestations : 70 %; - valeur technique : 30 %" take only "70".

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.here "prix des prestations : 70 %; - valeur technique : 30 %" take only "valeur technique".

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.here "prix des prestations : 70 %; - valeur technique : 30 %" take only "30".

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
        

# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'identification_consultation'):
            lot_details_data = lot_details()
        # Onsite Field -Objet
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.identification_consultation > div:nth-child(2) > div > span:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref_url:"https://marchespublics596280.fr/?page=Entreprise.EntrepriseDetailsConsultation&id=556781&orgAcronyme=3C029"


            try:
                for single_record in page_details.find_elements(By.ID, '#collapseBodyInfo'):
                    award_details_data = award_details()
	
			
                    # Onsite Field -None
                    # Onsite Comment -1.split between "Nom du titulaire / organisme : " and "Date d'attribution du marché :".		2.here "Société Idonéis – 2 rampe Saint-Marcel – 02000 LAON" take only "Société Idonéis".

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.split between "Nom du titulaire / organisme : " and "Date d'attribution du marché :".

                    award_details_data.address = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.split between "Date d'attribution du marché : " and "Nombre total d'offres reçues : ".

                    award_details_data.award_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
			
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
        
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text()," Avis de publicité")]//following::a[3]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -None
    # Onsite Comment -1.split between "Valeur totale finale (HT) : " and "Attribution du marché :".

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split between "Valeur totale finale (HT) : " and "Attribution du marché :".

    try:
        notice_data.netbudgetlc = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split between "Valeur totale finale (HT) : " and "Attribution du marché :".

    try:
        notice_data.netbudgeteuro = page_details.find_element(By.XPATH, '''//*[contains(text(),"Détail de l'annonce :")]//following::span[1]''').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.ID, '#ctl0_CONTENU_PAGE_panelOnglet1'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text()," Avis de publicité")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text()," Avis de publicité")]//following::a[1]').get_attribute('href')
            
        
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://marchespublics596280.fr/?page=Entreprise.EntrepriseAdvancedSearch&AllAnn"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div'),page_check))
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