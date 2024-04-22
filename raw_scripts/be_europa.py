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
SCRIPT_NAME = "be_europa"
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
    notice_data.script_name = 'be_europa'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -Places of delivery or performance
    # Onsite Comment -if performance_country is not available in "Places of delivery or performance" field then paas "Belgium" country

    try:
        notice_data.performance_country = page_details.find_element(By.XPATH, '//*[contains(text(),"Places of delivery or performance")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'eui-card-header-title').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'eui-card-header-subtitle > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'eui-card-header-right-content > div > eui-chip').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Publication date
    # Onsite Comment -for publish_Date click on "div.eui-card-header__expander"  button and grab data from "Publication date "

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(1) > div:nth-child(4) > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline date
    # Onsite Comment -for Deadline date  click on "div.eui-card-header__expander"  button and grab data from "Deadline date"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "for Deadline date  click on "div.eui-card-header__expander"  button and grab data from "Deadline date"").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract type
    # Onsite Comment -for notice_contract_type  click on "div.eui-card-header__expander"  button and grab data from "Contract type"  ,    Replace following keywords with given respective keywords  ('Services = service' , 'Supplies = supply' , 'Works = Works')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr  mat-card-content > div > div:nth-child(2) > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract type
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'tr  mat-card-content > div > div:nth-child(2) > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'eui-card-header-title a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'eui-page-column:nth-child(2) > div > eui-page-column-body').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::mat-card-content[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::mat-card-content[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = '"CPV"'
    
# Onsite Field -Main CPV code
# Onsite Comment -ref_url : "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/tender-details/14766en?grants=false&forthcoming=false&closed=false&pageNumber=3"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(1) > eui-card > mat-card > eui-card-content'):
            cpvs_data = cpvs()
        # Onsite Field -Main CPV code
        # Onsite Comment -ref_url : "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/tender-details/14766en?grants=false&forthcoming=false&closed=false&pageNumber=3"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -EUROPEAN UNION (EU)

    try:              
        for single_record in None.find_elements(By.None, 'None'):
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = '1344862'
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in None.find_elements(By.None, 'None'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'EUROPEAN UNION (EU)'
        # Onsite Field -None
        # Onsite Comment -if performance_country is not available in "Places of delivery or performance" field then paas "Belgium" country , ref_url : "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/tender-details/14766en?grants=false&forthcoming=false&closed=false&pageNumber=3"

            try:
                customer_details_data.org_country = page_details.find_element(By.XPATH, '//*[contains(text(),"Places of delivery or performance")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'EN'
            customer_details_data.org_parent_id = '7314301'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'eui-page-column:nth-child(2) > div > eui-page-column-body'):
            lot_details_data = lot_details()
        # Onsite Field -Lots
        # Onsite Comment -split only actual_number for ex."AO-06A50/2015/M013 — Framework contract for works with maintenance services in the field of centralised technical management for European Parliament buildings in Brussels" , here split only "AO-06A50/2015/M013"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div> div > strong').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lots
        # Onsite Comment -split only lot_title  for ex."AO-06A50/2015/M013 — Framework contract for works with maintenance services in the field of centralised technical management for European Parliament buildings in Brussels" , here split only "Framework contract for works with maintenance services in the field of centralised technical management for European Parliament buildings in Brussels"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div> div > strong').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
        # Onsite Field -Additional CPV code
        # Onsite Comment -ref_url : "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/tender-details/14766en?grants=false&forthcoming=false&closed=false&pageNumber=3"

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Additional CPV code")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -Call for tenders' details
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Additional CPV code")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = [" https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-search?grants=false&forthcoming=false&closed=false"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td'),page_check))
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