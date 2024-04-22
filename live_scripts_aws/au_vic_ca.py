from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_vic_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options

#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_vic_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'au_vic_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'AUD'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    notice_data.document_type_description = 'Recently Awarded Contracts'
    
    try:
        publish_date = date.today()
        publish_date = publish_date.strftime('%Y/%m/%d')
        publish_date = re.findall('\d{4}/\d+/\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date : {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Number
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no : {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Start Date 
    # Onsite Comment -None 1 Jan 2024
    try:
        tender_contract_start_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        tender_contract_start_date_month = re.findall('\d+ \w{3}',tender_contract_start_date)[0]
        tender_contract_start_date_year = re.findall('\d{4}',tender_contract_start_date)[0]
        tender_contract_start_date = tender_contract_start_date_month+' '+tender_contract_start_date_year
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date, '%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Expiry Date
    try:
        tender_contract_end_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        tender_contract_end_date_month = re.findall('\d+ \w{3}',tender_contract_end_date)[0]
        tender_contract_end_date_year = re.findall('\d{4}',tender_contract_end_date)[0]
        tender_contract_end_date1 = tender_contract_end_date_month+' '+tender_contract_end_date_year
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date1, '%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass    
    
    # Onsite Field -Total Value
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','').strip())
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass 
    
    # Onsite Field -Title
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
  
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try: 
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
        notice_data.notice_summary_english =notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -UNSPSC
    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC")]//following::div[1]').text
        for data in notice_data.category.split('\n'):
            category_name = data.split('-')[0].strip().lower()
            cpv_codes_list = fn.CPV_mapping("assets/au_vic_ca_unspscpv.csv",category_name)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = each_cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Public Body
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Public Body")]//following::div[1]').text
        
        # Onsite Field -Contact Person
        # Onsite Comment -Note:Take a first line for contact person
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::div[1]').text.split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact Person
        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > a').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact Person
        # Onsite Comment -Note:Splte after this "Office:" keyword
        try:
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::div[1]').text
            if 'Phone' in org_phone:
                customer_details_data.org_phone = org_phone.split('Phone:')[1].strip()
            elif 'Office' in org_phone:
                customer_details_data.org_phone = org_phone.split('Office:')[1].strip()
            elif 'Mobile' in org_phone:
                customer_details_data.org_phone = org_phone.split('Mobile:')[1].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -Title
        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

        award_details_data = award_details()

        # Onsite Field -Supplier Information
        award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Supplier Information")]//following::b[1]|//*[contains(text(),"Unregistered Suppliers")]//following::span').text

        try:
            award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Supplier Information")]//following::tbody[1]/tr[1]/td[2]/table[1]|(//*[contains(text(),"Unregistered Suppliers")]//following::table/tbody)[2]').text
        except:
            pass

        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
        
        if lot_details_data.award_details != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenders.vic.gov.au/contract/search?preset=recentlyAwarded"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/div/div/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div/div/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div/div/div[2]/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/main/div/div/div[2]/table/tbody/tr'),page_check))
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
