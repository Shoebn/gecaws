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
SCRIPT_NAME = "bt_egp_ca"
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
    notice_data.script_name = 'bt_egp_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'BTN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Tender ID, Ref No., Title & Advertisement Date
    # Onsite Comment -split only notice_no  for ex."15763, VEhicle maintenance", here take only "15763"  ,    split the data before comma

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3) > a > p').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender ID, Ref No., Title & Advertisement Date
    # Onsite Comment -split only related_id  for ex."16176, NCOA/ADM/23-24/804", here take only "NCOA/ADM/23-24/804" , take the data after comma

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3) > a > p').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass


    # Onsite Field -Value (In Nu.)
    # Onsite Comment -None

    try:
        notice_data.est_amount = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable  tr > td:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Value (In Nu.)
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable  tr > td:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender ID, Ref No., Title & Advertisement Date
    # Onsite Comment -split only publish_date for ex."Toyota Hilux (VIGO/REVO) less 13-Sep-2023 23:00", here split only "13-Sep-2023"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)> span > span.morecontent").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Tender ID, Ref No., Title & Advertisement Date
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable > tbody > tr> td:nth-child(3) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    # Onsite Field -Tender Package Description:
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Package Description:")]//following::td[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tender ID, Ref No., Title & Advertisement Date
    # Onsite Comment -if notice_no is not available in "Tender ID, Ref No., Title & Advertisement Date" section then pass notice_no from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable > tbody > tr> td:nth-child(3) > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    


    # Onsite Field -Contract Award for:
    # Onsite Comment -Replace following keywords with given respective keywords ('Services = service' , 'Goods = supply' , 'Works   = Works')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Award for:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Award for:
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Award for:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Package Description:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Package Description:
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Package Description:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#resultTable > tbody'):
            customer_details_data = customer_details()
        # Onsite Field -Hierarchy Node
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable  tr> td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procuring Agency, Procurement Method
        # Onsite Comment -remove procurement_method from selector  for ex. "National Centre for Organic Agriculture OTM"   , here split only "National Centre for Organic Agriculture"

            try:
                customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable  tr> td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'EN'
            customer_details_data.org_country = 'BT'
        # Onsite Field -Procuring Agency Dzongkhag / District:
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Procuring Agency Dzongkhag / District")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass


        # Onsite Field -AGENCY DETAILS >> Name of Authorized Officer:
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Name of Authorized Officer:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body  table:nth-child(6)'):
            funding_agencies_data = funding_agencies()
        # Onsite Field -Development Partner (if applicable):
        # Onsite Comment -"Funding agency" name as "World Bank (internal id: 1012)" / "Austrian Development Agency (internal id: 7307798)" /  "ADB  (internal id:  106)" in field name "T.FUNDING_AGENCIES::TEXT"

            try:
                funding_agencies_data.funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Development Partner (if applicable):")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in funding_agency: {}".format(type(e).__name__))
                pass
        
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
   
        
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body  table:nth-child(8)'):
            lot_details_data = lot_details()
        # Onsite Field -Tender Lot No. and Description:
        # Onsite Comment -take only lot_detail , ref_url : "https://www.egp.gov.bt/resources/common/ViewContracts.jsp?contractNo=9789,%3Cbr%3E%3C/a%3E%20MoESD/Pro-21/2023-24/462.&pkgLotId=24595&tenderid=16417&userId=10077"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"1. Tender Lot No. and Description:")]//following::tr/td[2]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Date of Contract Signing:
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewContracts.jsp?contractNo=10038,%3Cbr%3E%3C/a%3E%20BT-MoAF-317977-GO-RFQ&pkgLotId=24307&tenderid=16244&userId=5351"

            try:
                lot_details_data.contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of Contract Signing:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Proposed Date of Contract Completion:
        # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewContracts.jsp?contractNo=10038,%3Cbr%3E%3C/a%3E%20BT-MoAF-317977-GO-RFQ&pkgLotId=24307&tenderid=16244&userId=5351"

            try:
                lot_details_data.contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Proposed Date of Contract Completion:")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -INFORMATION ON AWARD
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body  table:nth-child(10)'):
                    award_details_data = award_details()
		
                    # Onsite Field -Company Name of Bidder/Consultant:
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Company Name of Bidder/Consultant:")]//following::td[1]').text
			
                    # Onsite Field -INFORMATION ON AWARD >>   Contract Value (Nu.):
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Value (Nu.):")]//following::td[1]').text

                    # Onsite Field -Date of Notification of Award
                    # Onsite Comment -None

                    award_details_data.award_date = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable  tr td:nth-child(5)').text
			
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.egp.gov.bt/resources/common/AdvContractListing.jsp"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="resultTable"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultTable"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultTable"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="resultTable"]/tbody/tr'),page_check))
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
    