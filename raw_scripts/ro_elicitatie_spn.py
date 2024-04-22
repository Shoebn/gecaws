#NOTE : click on "DATA PUBLICARE"/"PUBLICATION DATE" select previous and current date >>>> "FILTREAZA"

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
SCRIPT_NAME = "ro_elicitatie_spn"
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
    notice_data.script_name = 'ro_elicitatie_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'RON'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'RO'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RO'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -NUMAR ANUNT
    # Onsite Comment -split notice_no from notice_url if notice no is not present

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-1.margin-top-10 > div:nth-child(1) > strong').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DENUMIRE CONTRACT
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.padding-right-0 > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DATA PUBLICARE
    # Onsite Comment -grab the time which is present after date

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-1.margin-top-10 > div:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data limita depunere
    # Onsite Comment -grab the time which is present after date

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3) > strong").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Modalitatea de atribuire
    # Onsite Comment -just take data which is after "Modalitatea de atribuire:" till "CPV"

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9 div > div:nth-child(2) > strong:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipul contractului
    # Onsite Comment -map it with ........."Lucrari=Works","Furnizare=Supply","Servicii=Service"

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > strong:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipul contractului
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > strong:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.padding-right-0 > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#container-sizing').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -CPV
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > strong:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Descriere succinta
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Descriere succinta")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Descriere succinta")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valoarea totala estimata:
    # Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/simplified-notice/v2/view/100197356"

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Valoarea totala")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valoarea totala estimata:
    # Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/simplified-notice/v2/view/100197356"

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valoarea totala")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Adresa profilului cumparatorului
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresa profilului cumparatorului")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -if it is given as " financed by European Union funds: No  " than pass the "None " ------else if is written " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency
    # Onsite Comment -None

    try:
        notice_data.funding_agencies = page_details.find_element(By.XPATH, '//*[contains(text()," Informatii despre fondurile Uniunii Europene")]//following::span[2]').text
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))


# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#container-sizing'):
            customer_details_data = customer_details()
        # Onsite Field -Tara
        # Onsite Comment -None

            try:
                customer_details_data.org_country = page_details.find_element(By.XPATH, '//*[contains(text(),"Tara")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'RO'
        # Onsite Field -Autoritate contractanta
        # Onsite Comment -take data which is after "Autoritate contractanta"

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9 div > div:nth-child(2) > div').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Denumire si adrese
        # Onsite Comment -Note: splite data between  Adresa till E-mail

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-mail
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telefon
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Denumire si adrese
        # Onsite Comment -Note:Splite after Fax

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Localitate
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Localitate:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Cod postal
        # Onsite Comment -ref url - "https://www.e-licitatie.ro/pub/notices/simplified-notice/v2/view/100197354"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Cod postal:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Cod NUTS
        # Onsite Comment -None

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Cod NUTS")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Adresa web a sediului principal al autoritatii/entitatii contractante(URL)
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Adresa web a sediului principal al autoritatii/entitatii contractante(URL)")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        

        # Onsite Field -Activitate principala
        # Onsite Comment -None

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Activitate principala")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass

        # Onsite Field -Tipul autoritatii contractante
        # Onsite Comment -None

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipul autoritatii contractante")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass



# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#section-1 > div.widget-body > ng-transclude > div:nth-child(2)'):
            custom_tags_data = custom_tags()
        # Onsite Field -Cod fiscal
        # Onsite Comment -None

            try:
                custom_tags_data.tender_custom_tag_company_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Cod fiscal")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in tender_custom_tag_company_id: {}".format(type(e).__name__))
                pass
        
            custom_tags_data.custom_tags_cleanup()
            notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in custom_tags: {}".format(type(e).__name__)) 
        pass


# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.u-items-list__content > div'):
            cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > strong:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass


# Onsite Field -None
# Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/simplified-notice/v2/view/100197353"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table > tbody > tr'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Criterii de atribuire >>>> DESCRIERE
        # Onsite Comment -None

            try:
                tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-5.ng-binding').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Criterii de atribuire >> PONDERE
        # Onsite Comment -or use following path "//*[contains(text(),"Pondere")]//following::div/div/div[3]/div[1]"


            try:
                tender_criteria_data.tender_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-3 > div').text
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass


#Onsite Field -VEZI PROCEDURA
# Onsite Comment -take lots data by clicking on "VEZI PROCEDURA" from tender_html_element >>>> click on "Lista de loturi" from page_detail  ...........ref url "https://www.e-licitatie.ro/pub/procedure/view/100250427/"

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.u-items-list__item__value > a'):
            lot_details_data = lot_details()
        # Onsite Field -NR SI DENUMIRE LOT
        # Onsite Comment -split the actual number from the title

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, ' div.col-md-6 > h2').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -NR SI DENUMIRE LOT
        # Onsite Comment -Note:Cicking on "Lista de loturi" dropdownlist and grap the data

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'd div.col-md-6 > h2').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -CPV code
        # Onsite Comment -None

            try:
                lot_details_data.lot_cpv_at_source = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-6 > div > div > div > strong').text
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -VALOARE ESTIMATA LOT
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div.c-items-list__content > div > div > div > div:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Data atribuire
        # Onsite Comment -

            try:
                lot_details_data.lot_award_date = page_details.find_element(By.XPATH, '#procedure-tk  strong > span').text
            except Exception as e:
                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                pass


        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.c-items-list__content > div > div'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -CPV code
                    # Onsite Comment -None

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-6 > div > div > div > strong').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
   



    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title) 
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
    urls = ["https://www.e-licitatie.ro/pub/notices/contract-notices/list/0/0"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,70):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[9]/div[2]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[9]/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[9]/div[2]/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="container-sizing"]/div[9]/div[2]/div'),page_check))
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
    