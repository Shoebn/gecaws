#after opening the url click on "CONTRACTS = //*[contains(text(),'CONTRACTS')]" to get data.


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
SCRIPT_NAME = "mfa_worldbank_ca"
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
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'USD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
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
        notice_data.est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    # Onsite Field -Amount (US$)
    # Onsite Comment -None
    try:
        notice_data.grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    


    # Onsite Field -Country
    # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)
    try:
        notice_data.performance_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_ca_countrycode.csv",notice_data.notice_data.performance_country)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Signing Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
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
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'contractor-details').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract No")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Borrower Contract Reference")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -1.replace following keywords with given keywords("Civil Works=Works","Consultant Services=Consultancy","Goods=Supply","Non-consulting Services=Non consultancy").
    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Group")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Group")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'contractor-details'):
            customer_details_data = customer_details()
        # Onsite Field -Country
        # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)

            try:
                customer_details_data.org_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
		        cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_ca_countrycode.csv",notice_data.notice_data.performance_country)
        	    for cpv_code in cpv_codes:
            		cpvs_data = cpvs()
           		    cpvs_data.cpv_code = cpv_code
            		cpvs_data.cpvs_cleanup()
            		notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'EN'
            customer_details_data.org_name = 'The World Bank'
            customer_details_data.org_parent_id = '1012'
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
# Onsite Field -None
# Onsite Comment -
    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'table > tbody > tr'):
            lot_details_data = lot_details()

        # Onsite Field -Description
        # Onsite Comment -None
            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

        # Onsite Field -
        # Onsite Comment -None
            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Group")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -
        # Onsite Comment -None
            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Group")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'contractor-details > div.row.full-row-white-components'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -None
                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Contractor Name")]//following::td[1]').text
			
                    # Onsite Field -None
                    # Onsite Comment -# Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)
                    award_details_data.bidder_country = page_details.find_element(By.XPATH, '//*[contains(text(),"Contractor Country")]//following::td[2]').text
                    cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_ca_countrycode.csv",award_details_data.bidder_country)
                    for cpv_code in cpv_codes:
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = cpv_code
                        cpvs_data.cpvs_cleanup()
                        notice_data.cpvs.append(cpvs_data)
			
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
    urls = ["https://projects.worldbank.org/en/projects-operations/procurement?srce=both"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[2]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[2]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[2]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[2]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr'),page_check))
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