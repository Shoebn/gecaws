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
SCRIPT_NAME = "au_nsw"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------

# to explore  details   1) Go to URL : https://suppliers.buy.nsw.gov.au/opportunity/search?types=Tenders 

#                       2)  Go to "Opportunity types" Drop down ( selector : "#expand-opportunity-types > button" ) 


#                       3) select "Expression of Interest" and "Tenders" checkboxes  

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'au_nsw'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -if you see document_type_description is  "expression of interest" then  take notice_type = 5
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'AUD'
    
    # Onsite Field -Closes
    # Onsite Comment -split only date-month-year for ex."Closes: 4-Sep-2023 10:00" , here split only "4-Sep-2023"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "li > p:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li > h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFT ID
    # Onsite Comment -split only notice_no for ex."RFT ID: DCJ202316" , here split only "DCJ202316"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#search-results  li > ul > li').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFT type
    # Onsite Comment -split the following data from "RFT type" field

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'li dl > dd:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -See details
    # Onsite Comment -inspect url for detail_page, ref_url for detail_page : "https://www.tenders.nsw.gov.au/wsroc/?event=public.rft.show&RFTUUID=0EB933A1-AD8F-CBFA-B8C51978C5EC468F"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div > a:nth-child(2)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Details")]//following::p').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Details
    # Onsite Comment -excluding the "Local_title /  Local_description "all fields should be in English, split the data between "Tender Details" and "Location" field, ref_url : "https://www.tenders.nsw.gov.au/health/?event=public.rft.show&RFTUUID=1176DF5A-A33C-B230-A160FA641728F93B"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Details")]//following::p').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.info'):
            customer_details_data = customer_details()


            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'

        # Onsite Field -Agency
        # Onsite Comment -None

            try:
                customer_details_data.org_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Agency")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Person
        # Onsite Comment -split the first line data as a "contact person" from this xpath, ref_url : "https://www.tenders.nsw.gov.au/health/?event=public.rft.show&RFTUUID=1176DF5A-A33C-B230-A160FA641728F93B"

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Phone:
        # Onsite Comment -split the second data from this xpath, take only number for ex. "Phone: 02 9273 3919" here split only "02 9273 3919",     ref_url : "https://www.tenders.nsw.gov.au/dcs/?event=public.rft.show&RFTUUID=7C928DED-B737-0A51-585B4D8F7B8E2E0D"

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Person
        # Onsite Comment -split the last data from this xpath, split only email for ex. "kris.wallis1@tafensw.edu.au",     ref_url : "https://www.tenders.nsw.gov.au/dcs/?event=public.rft.show&RFTUUID=7C928DED-B737-0A51-585B4D8F7B8E2E0D"

            try:
                customer_details_data.org_email = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::div[1]/a').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Agency Address
        # Onsite Comment -split org_address from detail_page if available, ref_url for detail_page : "https://www.tenders.nsw.gov.au/doe/?event=public.rft.show&RFTUUID=0F424D88-F333-68D6-7AA6D2DC47EB3268"

            try:
                customer_details_data.org_address = single_record.find_element(By.XPATH, '//*[contains(text(),"Agency Address")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
 
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#search-results > ul > li'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -split the data from tender_html_page

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li > h3').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender Details
        # Onsite Comment -split the data between "Tender Details" and "Location" field, ref_url : "https://www.tenders.nsw.gov.au/health/?event=public.rft.show&RFTUUID=1176DF5A-A33C-B230-A160FA641728F93B"

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Details")]//following::p').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -in the detail_page click on "Download a softcopy - free" ( selector : "//*[contains(text(),"softcopy")]" ) hyperlink and then add credentails ("email" : "akanksha.a@dgmarket.com", "password" : "Sierrajaytom@1"), after that detail_page_1 will be open ( ref_url for detail_page1 : "https://www.tenders.nsw.gov.au/dcs/?event=public.RFT.viewDocuments&rftuuid=7C928DED-B737-0A51-585B4D8F7B8E2E0D") and grab documents on that page

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '.col-sm-pull-4 >  div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -in the detail_page click on "Download a softcopy - free" ( selector : "//*[contains(text(),"softcopy")]" ) hyperlink and then add credentails ("email" : "akanksha.a@dgmarket.com", "password" : "Sierrajaytom@1"), after that detail_page_1 will be open, split only file_type For ex. "RFQ TELCO22722 part_A_including SOW_final.docx ( 1.92 MB)", here split only "docx"

            try:
                attachments_data.file_type = page_details1.find_element(By.CSS_SELECTOR, 'div.col-sm-8  div > p > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -in the detail_page click on "Download a softcopy - free" ( selector : "//*[contains(text(),"softcopy")]" ) hyperlink and then add credentails ("email" : "akanksha.a@dgmarket.com", "password" : "Sierrajaytom@1"), after that detail_page_1 will be open, split only file_name For ex. "RFQ TELCO22722 part_A_including SOW_final.docx ( 1.92 MB)", here split only "RFQ TELCO22722 part_A_including SOW_final"

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'div.col-sm-8  div > p > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -in the detail_page click on "Download a softcopy - free" ( selector : "//*[contains(text(),"softcopy")]" ) hyperlink and then add credentails ("email" : "akanksha.a@dgmarket.com", "password" : "Sierrajaytom@1"), after that detail_page_1 will be open, split only file_size For ex. "RFQ TELCO22722 part_A_including SOW_final.docx ( 1.92 MB)", here split only "1.92 MB"

            try:
                attachments_data.file_size = page_details1.find_element(By.CSS_SELECTOR, 'div.col-sm-8  div > p > a').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -in the detail_page click on "Download a softcopy - free" ( selector : "//*[contains(text(),"softcopy")]" ) hyperlink and then add credentails ("email" : "akanksha.a@dgmarket.com", "password" : "Sierrajaytom@1"), after that detail_page_1 will be open and when you click on document it will be download

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'div.col-sm-8  div > p > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://suppliers.buy.nsw.gov.au/opportunity/search?types=Tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,7):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="search-results"]/ul/li[1]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search-results"]/ul/li[1]')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search-results"]/ul/li[1]')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="search-results"]/ul/li[1]'),page_check))
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)