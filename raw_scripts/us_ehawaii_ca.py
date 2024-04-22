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
SCRIPT_NAME = "us_ehawaii_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------

# Note : when you click on table row it will pass into detail_page ,  for Navigate to the detail_page click on the "tr.ng-star-inserted" field if the  message is appear that  
#        "You are leaving HANDS and proceeding to the HIePRO State of Hawaii eProcurement website." or any other  popup for 
#        another website is displayed, then click on the "Cancel" button  (note : do not click on "tr > td:nth-child(5) a"   for detail_page)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'us_ehawaii_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'USD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Solicitation #
    # Onsite Comment -if notice_no is not available in "Solicitation #" then split the number from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -Replace the  following keywords with given respective keywords ('Services = service' , 'Goods = supply' , 'Goods & Services   = service' , 'Construction = Works' , 'Health and Human Services = service' , 'Professional Services = service' , 'Hybrid (combo of 2 or more categories) = service')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(8)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(8)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
        
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = '"Contract Awards"'

    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.publish_date = 'take a publish_date as a  threshold date'
    
    # Onsite Field -None
    # Onsite Comment -when you click on table row it will pass into detail_page ,  for Navigate to the detail_page click on the "tr.ng-star-inserted" field if the  message is appear that  "You are leaving HANDS and proceeding to the HIePRO State of Hawaii eProcurement website." or any other  popup for another website is displayed, then click on the "Cancel" button  (note : do not click on "tr > td:nth-child(5) a"   for detail_page)

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.ng-star-inserted').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -in the notice_text there are multiple tabs available ,  like General Information , Contact Information,  Committee Information
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div > tabset').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -split the data from detail_page

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'tr > td:nth-child(7)'):
            customer_details_data = customer_details()
        # Onsite Field -Department
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'

            
        # Onsite Field -Island
        # Onsite Comment -None

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(9)').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass


            # Onsite Field - Contact Person
        # Onsite Comment -go to "Contact Information" tab  and grab the data from "Contact Person" field , ref_url : "https://hands.ehawaii.gov/hands/awards/award-details/175983"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Phone
        # Onsite Comment -go to "Contact Information" tab  and grab the data from " Phone" field , ref_url : "https://hands.ehawaii.gov/hands/awards/award-details/175983"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass


        # Onsite Field - E-mail
        # Onsite Comment -go to "Contact Information" tab and grab the data from "Email" field

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tab.active.tab-pane > fieldset:nth-child(1)'):
            lot_details_data = lot_details()
        # Onsite Field -Title
        # Onsite Comment -take a lot_title as a local_title

            try:
                lot_details_data.lot_title = None.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'tr > td:nth-child(6)'):
                    award_details_data = award_details()
		
                    # Onsite Field -Date Awarded
                    # Onsite Comment -None

                    award_details_data.award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1)').text
			
                    # Onsite Field -Date Awarded
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text
			
                    # Onsite Field -Awardee
                    # Onsite Comment -None

                    award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(5)').text
			
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
    
    # Onsite Field -contract start date
    # Onsite Comment -None

    try:
        notice_data.tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Start Date")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract End Date
    # Onsite Comment -None

    try:
        notice_data.tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract End Date")]//following::td[2]').text
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Total Contract Value
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Total Contract Value")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Attachment(s)
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'fieldset:nth-child(1) > table > tbody > tr:nth-child(13)'):
            attachments_data = attachments()
        # Onsite Field -Attachment(s)
        # Onsite Comment -split only file name for exmaple "Award letter.PDF" , here take only "Award letter"

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Attachment(s)")]//following::td//span//a[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachment(s)
        # Onsite Comment -split only file type  for exmaple "Award letter.PDF" , here take only "PDF"

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Attachment(s)")]//following::td//span//a[1]').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachment(s)
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Attachment(s)")]//following::td//span//a[1]').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ["https://hands.ehawaii.gov/hands/awards"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="search_results"]/div/div[3]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search_results"]/div/div[3]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search_results"]/div/div[3]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="search_results"]/div/div[3]/table/tbody/tr'),page_check))
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