#after opening the url click on "CONTRACTS = //*[contains(text(),'CONTRACTS')]" to get data.
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_worldbank_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_worldbank_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.main_language = 'EN'
  
    notice_data.currency = 'USD'
    
    notice_data.script_name = 'mfa_worldbank_ca'
   
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Project Title
    # Onsite Comment -None
    try:
        notice_data.project_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass

    # Onsite Field -Procurement Method
    # Onsite Comment -None
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Amount (US$)
    # Onsite Comment -None
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc =  notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    # Onsite Field -Country
    # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)
    
    try:
        country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        performance_country_data = performance_country()
        performance_country_1 = country
        performance_country_data.performance_country = fn.procedure_mapping("assets/mfa_worldbank_ca_countrycode.csv",performance_country_1)
        if performance_country_data.performance_country == None:
            performance_country_data.performance_country = 'US'
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Signing Date
    # Onsite Comment -None 21-Nov-2023

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\d+-\w{3}-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'contractor-details').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract No")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Borrower Contract Reference")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.replace following keywords with given keywords("Civil Works=Works","Consultant Services=Consultancy","Goods=Supply","Non-consulting Services=Non consultancy").
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Group")]//following::p[1]').text
        if 'Civil Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type  ='Works'
        elif 'Consultant Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type  ='Consultancy'
        elif 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type  ='Supply'
        elif 'Non-consulting Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type  ='Non consultancy'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = 'The World Bank'
        customer_details_data.org_parent_id = '1012'
        # Onsite Field -Country
        # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)

        try:
            country1 = country
            customer_details_data.org_country =fn.procedure_mapping("assets/mfa_worldbank_ca_countrycode.csv",country1)
            if customer_details_data.org_country == None:
                customer_details_data.org_country = 'US'
        except Exception as e:
            logging.info("Exception in org_country: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -Team Leader
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Team Leader")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.contract_type = notice_data.notice_contract_type
        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True

        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div.row.full-row-white-components > div > div > div > div > div > table > tbody > tr')[1:]:
                award_details_data = award_details()

                award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text
                
                bidder_country = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                award_details_data.bidder_country =fn.procedure_mapping("assets/mfa_worldbank_ca_countrycode.csv",bidder_country)
                if award_details_data.bidder_country == None:
                    award_details_data.bidder_country = 'US'
                    
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
    urls = ["https://projects.worldbank.org/en/projects-operations/procurement?srce=both"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        contract = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[contains(text(),'CONTRACTS')]")))
        page_main.execute_script("arguments[0].click();",contract)
        time.sleep(5)  

        try:
            for page_no in range(2,30):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.c14v1-body.c14v1-body-text.project-opt-table.responsive-table > div > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.c14v1-body.c14v1-body-text.project-opt-table.responsive-table > div > table > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.c14v1-body.c14v1-body-text.project-opt-table.responsive-table > div > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.c14v1-body.c14v1-body-text.project-opt-table.responsive-table > div > table > tbody > tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
