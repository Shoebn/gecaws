from gec_common.gecclass import *
import logging
import re
import csv
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
SCRIPT_NAME = "mfa_ungm_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -to load the more reocrds add 3-4 second sleep time
    notice_data.script_name = 'us_ungm_ca'
    
    notice_data.main_language = 'EN'
    
    notice_data.currency = 'USD'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    notice_data.document_type_description = 'ContractAward'
    
    # Onsite Field -Beneficiary country or territory
    # Onsite Comment -None
    
    try:
        performance_country_data = performance_country()
        p_country = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(6)').text
        performance_country_data.performance_country = fn.procedure_mapping("assets/us_ungm_countrycode.csv",p_country)
        notice_data.performance_country.append(performance_country_data)
    except:
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'US'
        notice_data.performance_country.append(performance_country_data)
    
    try:
        notice_data.source_of_funds = 'International agencies'
        funding_agencies_data = funding_agencies()
        funding_agency = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4)').text
        funding_agencies_data.funding_agency = fn.procedure_mapping("assets/us_ungm_funding.csv",funding_agency)
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Reference
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#centre > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -if the description is not available then take local_title as notice_summary_english

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract value (USD)
    # Onsite Comment -click on 'General' to get the data

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract value (USD)")]//following::span[1]').text
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract value (USD)
    # Onsite Comment -click on 'General' to get the data

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract value (USD)")]//following::span[1]').text
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -click on "Contacts > Show detail" in detail page to get more customer details

   
# Onsite Field -None
# Onsite Comment -None
    try:              
        lot_details_data = lot_details()
        # Onsite Field -Title
        # Onsite Comment -None
        lot_details_data.lot_title = notice_data.notice_title
        lot_details_data.lot_number = 1
       
        # Onsite Field -Contract value (USD)
        # Onsite Comment -click on 'General' to get the data

        lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
        
         # Onsite Field -Description
        # Onsite Comment -if the description is not available then take local_title as lot_ description

        try:
            lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
            if 'Lot' in lot_details_data.lot_description:
                lot_details_data.lot_actual_number = lot_details_data.lot_description.split('-')[0]
        except Exception as e:
            lot_details_data.lot_description = notice_data.local_title
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
        # Onsite Field -None
        # Onsite Comment -None

        try:
            award_details_data = award_details()

            # Onsite Field -Supplier
            # Onsite Comment -None

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow> div:nth-child(2)').text
            
            award_details_data.grossawardvaluelc = notice_data.grossbudgetlc
            # Onsite Field -Award date
            # Onsite Comment -None

            award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow> div:nth-child(3)').text
            award_date = re.findall('\d+-\w+-\d{4}',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date,'%d-%b-%Y').strftime('%Y/%m/%d')
            
            notice_data.publish_date =  award_details_data.award_date

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

    try:              
        customer_details_data = customer_details()
        # Onsite Field -UN organization
        # Onsite Comment -None

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow> div:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Beneficiary country or territory
        # Onsite Comment -None

        customer_details_data.org_country = performance_country_data.performance_country
#         import pdb;pdb.set_trace()
        # Onsite Field -First name
        # Onsite Comment -'//*[contains(text(),"Last name")]//following::span[1]' Last name    take both the selector in contact_person
        try:
            contact_click = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#Contacts')))
            page_details.execute_script("arguments[0].click();",contact_click)
            
            expand =  page_details.find_element(By.CSS_SELECTOR, '#Contacts-tab > p:nth-child(1) > input.btnExpandAll').click()
            time.sleep(2)
        except:
            pass
        
        try:
            customer_details_data.contact_person = WebDriverWait(page_details, 40).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"First name")]//following::span[1]'))).text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Telephone number
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone number")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact email
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact email")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Fax number
        # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax number")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
    urls = ['https://www.ungm.org/Public/ContractAward'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        scheight = .1

        while scheight < 9.9:
            page_main.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
            scheight += .01

        time.sleep(2)

        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tblContractAwards"]/div[2]/div'))).text
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblContractAwards"]/div[2]/div')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblContractAwards"]/div[2]/div')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
