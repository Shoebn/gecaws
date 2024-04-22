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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fi_hanki"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -the following two formats have been identified 
#format 1  
#https://www.hankintailmoitukset.fi/fi/public/procurement/92953/notice/136810/overview

#format 2
#https://www.hankintailmoitukset.fi/fi/public/procedure/28/enotice/86/ 
    notice_data.script_name = 'fi_hanki'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'FI'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FI'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -if deadline is not present then notice_type will be 7
    notice_data.notice_type = 4
    
    # Onsite Field -Ilmoitustyyppi
    # Onsite Comment -if 'Kansallinen hankintailmoitus'/ 'Kansallinen pienhankinta' keyword is present then take procurement method "0" otherwise take  "2"

    try:
        notice_data.procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table > tbody > tr > td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ilmoitustyyppi
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table > tbody > tr > td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nimi
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table > tbody > tr > td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Julkaistu
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "table.table > tbody > tr > td:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Määräaika
    # Onsite Comment -take notice_deadline for notice_type 4

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "table.table > tbody > tr > td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nimi
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table > tbody > tr > td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -take all the data from diff tabs ('div.vertbar > ul > li > a')
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -take all the data from diff tabs ('div.nav-wrapper.mt-5 > p > a') - format 2
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Ilmoituksen Hilma-numero
    # Onsite Comment -Both format

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ilmoituksen Hilma-numero")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nimi
    # Onsite Comment -if notice_no is not available then take notice_no from notice_url fro both format

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table > tbody > tr > td:nth-child(2) > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Hankinnan lyhyt kuvaus
    # Onsite Comment -format 1

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Lyhyt kuvaus")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Lyhyt kuvaus")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan kuvaus")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Hankinnan kuvaus
    # Onsite Comment -format 2

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan kuvaus")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Menettelyn luonne
    # Onsite Comment -format 1
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Menettelyn luonne")]//following::div[1]").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fi_hanki_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Menettelyn tyyppi
    # Onsite Comment -format 2
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Menettelyn tyyppi")]//following::div[1]").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fi_hanki_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)
    # Onsite Comment -format 1(use this link for ref : 'https://www.hankintailmoitukset.fi/fi/public/procurement/79997/notice/134826/overview')

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)
    # Onsite Comment -format 1(use this link for ref : 'https://www.hankintailmoitukset.fi/fi/public/procurement/79997/notice/134826/overview')

    try:
        notice_data.grossbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)
    # Onsite Comment -format 1(use this link for ref : 'https://www.hankintailmoitukset.fi/fi/public/procurement/79997/notice/134826/overview')

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Arvioitu kokonaisarvo
    # Onsite Comment -format 1(use this link for ref'https://www.hankintailmoitukset.fi/fi/public/procurement/90429/notice/134827/overview')

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Arvioitu kokonaisarvo")]//following::div[2]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Arvioitu kokonaisarvo
    # Onsite Comment -format 1(use this link for ref'https://www.hankintailmoitukset.fi/fi/public/procurement/90429/notice/134827/overview')

    try:
        notice_data.grossbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Arvioitu kokonaisarvo")]//following::div[2]').text
    except Exception as e:
        logging.info("Exception in grossbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Arvioitu kokonaisarvo
    # Onsite Comment -format 1(use this link for ref'https://www.hankintailmoitukset.fi/fi/public/procurement/90429/notice/134827/overview')

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Arvioitu kokonaisarvo")]//following::div[2]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Hankinnan tyyppi
    # Onsite Comment -format 1

    # try:
        # notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan tyyppi")]//following::div[2]').text
    # except Exception as e:
        # logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        # pass
    
    # Onsite Field -Pääasiallinen hankintalaji
    # Onsite Comment -Lyhyesti > Pääasiallinen hankintalaji  format 2

    # try:
        # notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Pääasiallinen hankintalaji")]//following::div[1]').text
    # except Exception as e:
        # logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        # pass
    
# Onsite Field -None
# Onsite Comment -click on 'Ostajaorganisaatio'tab to get the data

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#main > div'):
            customer_details_data = customer_details()
        # Onsite Field -Ostajaorganisaatio > Virallinen nimi
        # Onsite Comment -format 1

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Virallinen nimi")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Postinumero
        # Onsite Comment -format 1

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postinumero")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Postiosoite
        # Onsite Comment -format 1  split the data from 'Postiosoite' till 'Aluekoodi'

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.notice-public-organisation-contract > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Sähköpostiosoite
        # Onsite Comment -format 1

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Sähköpostiosoite")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Verkko-osoite
        # Onsite Comment -format 1

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Verkko-osoite")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Aluekoodi
        # Onsite Comment -format 1

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Aluekoodi")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Osallistuminen > Nimi
        # Onsite Comment -format 1   click on 'Osallistuminen'tab to get the data

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Nimi")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Osallistuminen > Puhelin
        # Onsite Comment -format 1   click on 'Osallistuminen'tab to get the data

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Puhelin")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lyhyesti > Organisaation virallinen nimi
        # Onsite Comment -format 2

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organisaation virallinen nimi")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Postinumero
        # Onsite Comment -format 2

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postinumero")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Postiosoite / Postinumero / Postitoimipaikka/ Maa /Aluekoodi
        # Onsite Comment -format 2      split the data from 'Postiosoite' till 'Aluekoodi'

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postiosoite")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Organisaation yhteyspisteen sähköpostiosoite
        # Onsite Comment -format 2

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Organisaation yhteyspisteen sähköpostiosoite")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ostajaorganisaatio > Verkko-osoite
        # Onsite Comment -format 2

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Verkko-osoite")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -stajaorganisaatio > Organisaation yhteyspisteen puhelinnumero
        # Onsite Comment -format 2    click on 'Osallistuminen'tab to get the data

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Organisaation yhteyspisteen puhelinnumero")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Pääasiallinen toimiala
        # Onsite Comment -format 2

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Pääasiallinen toimiala")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#main > div'):
            cpvs_data = cpvs()
        # Onsite Field -Hankintanimikkeistö
        # Onsite Comment -format 1

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankintanimikkeistö")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Hankintanimikkeistö (CPV-koodi)
        # Onsite Comment -format 2

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankintanimikkeistö (CPV-koodi)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#main > div'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Tarjousten valintaperusteet
        # Onsite Comment -format 1

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Tarjousten valintaperusteet")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tarjousten valintaperusteet
        # Onsite Comment -format 1

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Tarjousten valintaperusteet")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tarjousten vertailuperusteet
        # Onsite Comment -format 1

            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Tarjousten vertailuperusteet")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tarjousten vertailuperusteet
        # Onsite Comment -format 1

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Tarjousten vertailuperusteet")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -OSIA KOSKEVAT TIEDOT
# Onsite Comment -ref ('https://www.hankintailmoitukset.fi/fi/public/procurement/91883/notice/135037/details')

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.notice-public-lot'):
            lot_details_data = lot_details()
        # Onsite Field -OSIA KOSKEVAT TIEDOT
        # Onsite Comment -split lot_actual_no from the given selector for ex.: from "OSA 1 - TILATYYPPI 1: YHDEN SISÄÄNKÄYNNIN SISÄTILA, PIRKKOLAN JÄÄHALLI" take only "OSA 1"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.notice-public-lot > h2').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Osan nimi
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Osan nimi")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Kuvaus hankinnasta
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Kuvaus hankinnasta")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Arvioitu arvo
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Arvioitu arvo")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Aluekoodi
        # Onsite Comment -None

            try:
                lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Aluekoodi")]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Sopimuksen kesto
        # Onsite Comment -None

            try:
                lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Sopimuksen kesto")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
          
    # Onsite Field -Hankinnan tyyppi
    # Onsite Comment -format 1

            # try:
                # lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan tyyppi")]//following::div[2]').text
            # except Exception as e:
                # logging.info("Exception in contract_type: {}".format(type(e).__name__))
                # pass  
        
    # Onsite Field -Pääasiallinen hankintalaji
    # Onsite Comment -Lyhyesti > Pääasiallinen hankintalaji  format 2
    
            # try:
                # lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Pääasiallinen hankintalaji")]//following::div[1]').text
            # except Exception as e:
                # logging.info("Exception in contract_type: {}".format(type(e).__name__))
                # pass
                
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.notice-public-lot'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Lisäkoodit hankintanimikkeistö
                    # Onsite Comment -None

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Lisäkoodit hankintanimikkeistö")]//following::div[2]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.notice-public-lot'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -Tarjousten valintaperusteet
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Tarjousten valintaperusteet")]//following::div[1]').text
			
                    # Onsite Field -Tarjousten valintaperusteet
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Tarjousten valintaperusteet")]//following::div[1]').text
			
                    # Onsite Field -Tarjousten vertailuperusteet
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Tarjousten vertailuperusteet")]//following::div[1]').text
			
                    # Onsite Field -Tarjousten vertailuperusteet
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Tarjousten vertailuperusteet")]//following::div[1]').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -TOIMITTAJAN NIMI JA OSOITE
        # Onsite Comment -( ref. https://www.hankintailmoitukset.fi/fi/public/procurement/87688/notice/135272/overview ) take multiper bidders if available

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#main > div'):
                    award_details_data = award_details()
		
                    # Onsite Field -Virallinen nimi
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Virallinen nimi")]//following::div[1]').text
			
                    # Onsite Field -Postiosoite/Postinumero/Postitoimipaikka/Maa/Aluekoodi
                    # Onsite Comment -take data from 'Postiosoite' till 'Aluekoodi'

                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postiosoite")]//following::div[1]').text
			
                    # Onsite Field -Sopimuksen
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Sopimuksen")]//following::div[1]').text
			
                    # Onsite Field -osan kokonaisarvo
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"osan kokonaisarvo")]//following::div[1]').text
			
                    # Onsite Field -Tulokset > Kaikkien tässä hankintamenettelyssä tehtyjen sopimusten arvo
                    # Onsite Comment -format 2

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Kaikkien tässä hankintamenettelyssä tehtyjen sopimusten arvo")]//following::div[1]').text
			
                    # Onsite Field -Tulokset > Kaikkien tässä hankintamenettelyssä tehtyjen sopimusten arvo
                    # Onsite Comment -format 2

                    award_details_data.grossawardvalueeuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Kaikkien tässä hankintamenettelyssä tehtyjen sopimusten arvo")]//following::div[1]').text
			
                    # Onsite Field -osan kokonaisarvo
                    # Onsite Comment -None

                    award_details_data.grossawardvalueeuro = page_details.find_element(By.XPATH, '//*[contains(text(),"osan kokonaisarvo")]//following::div[1]').text
			
                    # Onsite Field -Sopimuksen
                    # Onsite Comment -None

                    award_details_data.grossawardvalueeuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Sopimuksen")]//following::div[1]').text
			
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
    
# Onsite Field -LIITTEET JA LINKIT
# Onsite Comment -(use this link for ref :  'https://www.hankintailmoitukset.fi/fi/public/procurement/91776/notice/134837/overview')

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > table'):
            attachments_data = attachments()
        # Onsite Field -LIITTEET JA LINKIT
        # Onsite Comment -take file_type in textform

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(8) > table > tbody > tr > td > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -LIITTEET JA LINKIT
        # Onsite Comment -take file_name in textform

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(8) > table > tbody > tr > td > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -LIITTEET JA LINKIT
        # Onsite Comment -take file_size if available

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(8) > table > tbody > tr > td > a').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -LIITTEET JA LINKIT
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(8) > table > tbody > tr > td > a').get_attribute('href')
            
        
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
    urls = ['https://www.hankintailmoitukset.fi/fi/search'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,50):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/main/div/div/div[2]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/div/div[2]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/div/div[2]/div/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/main/div/div/div[2]/div/table/tbody/tr'),page_check))
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
    