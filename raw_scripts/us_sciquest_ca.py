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




# bidder_name ia blank but notice_type will be 7


# Open the site than Go to "Sort by" Dropdown button than select "Open date descending" than grab the data




NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_sciquest_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'us_sciquest_ca'
    
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
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Open
    # Onsite Comment -Note:Grab time also

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr td:nth-child(2) div:nth-child(1) > div > div > div:nth-child(1) > div:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    # Onsite Field -Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2) div:nth-child(2) > div > div > div:nth-child(2) > div:nth-child(2) > div').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -Type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2) div:nth-child(2) > div > div > div:nth-child(1) > div:nth-child(2) > div').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass    
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_url = 'https://bids.sciquest.com/apps/Router/PublicEvent?tab=PHX_NAV_SourcingAward&CustomerOrg=StateOfMontana&SourcingPublicSite_FilterWorkGroup_PublicSite=%5B%5D&SourcingPublicSite_FILTER_BY_BUSINESS_UNIT=undefined&SourcingPublicSite_FILTER_BY_BUSINESS_UNIT_buDisplayName=&SimpleSearch_Keyword=&tmstmp=1706702678219'
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableWrapper tbody > tr').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.tableWrapper tbody > tr'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'MONTANA ACQUISITION & CONTRACTING SYSTEM (EMACS)'
            customer_details_data.org_parent_id = '7448389'
        # Onsite Field -Contact
        # Onsite Comment -Note:Take only text...Don't take "<a>" tag.....EX,"Bob Hlynosky bob.hlynosky@mso.umt.edu" take only "Bob Hlynosky"

            try:
                customer_details_data.contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2) div:nth-child(2) > div > div > div:nth-child(3) > div:nth-child(2) > div').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact
        # Onsite Comment -None

            try:
                customer_details_data.org_email = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2) div:nth-child(2) > div > div > div:nth-child(3) div > a').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.tableWrapper tbody > tr'):
            attachments_data = attachments()
            attachments_data.file_name = 'Tender document'
        # Onsite Field -Details
        # Onsite Comment -None

            attachments_data.external_url = tender_html_element.find_element(By.ID, 'SourcingPublicSite_BUTTON_PDF_VIEW').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass



# Format 2


# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.tableWrapper tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -Award Documents
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2) div:nth-child(2) > div > div > div:nth-child(5) > div:nth-child(2) > div a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2) div:nth-child(2) > div > div > div:nth-child(5) > div:nth-child(2) > div a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr td:nth-child(2) div:nth-child(2) > div > div > div:nth-child(5) > div:nth-child(2) > div a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://bids.sciquest.com/apps/Router/PublicEvent?tab=PHX_NAV_SourcingAward&CustomerOrg=StateOfMontana&SourcingPublicSite_FilterWorkGroup_PublicSite=%5B%5D&SourcingPublicSite_FILTER_BY_BUSINESS_UNIT=undefined&SourcingPublicSite_FILTER_BY_BUSINESS_UNIT_buDisplayName=&SimpleSearch_Keyword=&tmstmp=1706702678219"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/div/div/div[2]/form/div[4]/div[2]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/div/div/div[2]/form/div[4]/div[2]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/div/div/div[2]/form/div[4]/div[2]/div/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div/div/div/div[2]/form/div[4]/div[2]/div/table/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)





























