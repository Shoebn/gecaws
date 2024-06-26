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


# Note:Open the site than go to "Search Criteria" and click on "Ad Status" dropdown than Click on "CLOSED" checkbox than click on "Search" button than grab the data



NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_myfloridamarpl_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'us_myfloridamarpl_ca'
    
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
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.mat-cell.cdk-cell.cdk-column-title.mat-column-title.ng-star-inserted').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Agency Advertisement Number
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td.mat-cell.cdk-cell.cdk-column-agencyAdvertisementNumber.mat-column-agencyAdvertisementNumber.ng-star-inserted').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass    
    
    # Onsite Field -Number
    # Onsite Comment -Note:If notice_no is blank than take from notice_url in page_main

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.mat-cell.cdk-cell.cdk-column-adNumber.mat-column-adNumber.ng-star-inserted').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ad Type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td.mat-cell.cdk-cell.cdk-column-type.mat-column-type.ng-star-inserted').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Number
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.mat-cell.cdk-cell.cdk-column-adNumber.mat-column-adNumber.ng-star-inserted > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -Note:along with notice text (page main) also take data from tender_html_element (main page) ---- give "/html/body/mfmp-root/mfmp-bids-public-search-dashboard/main/mfmp-search-layout/mat-drawer-container/mat-drawer-content/mfmp-bid-table/table/tbody/tr" of main pg
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'mfmp-bids-view > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Published Date/Time:
    # Onsite Comment -Note:Splite afdter "Published Date/Time:" this keyword...Grab time also

    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),"Published Date/Time:")]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
# Onsite Field -Please direct all questions to:
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'section.space'):
            customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.mat-cell.cdk-cell.cdk-column-agency.mat-column-agency.ng-star-inserted').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Please direct all questions to: >> Name:
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Name:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Please direct all questions to: >> Phone:
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Phone:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Please direct all questions to: >> Address:
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Address:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Please direct all questions to: >> Email:
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::a[1]').text
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
    
# Onsite Field -Commodity Codes
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'mfmp-bid-detail > section > mfmp-commodity-codes-list > table'):
            cpvs_data = cpvs()
        # Onsite Field -Commodity Codes >> Code
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_main.find_element(By.CSS_SELECTOR, 'td.mat-cell.cdk-cell.cdk-column-code.mat-column-code.ng-star-inserted').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Downloadable Files for Advertisement
# Onsite Comment -None
# Ref_url=https://vendor.myfloridamarketplace.com/search/bids/detail/6535
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'mfmp-bid-detail > section > table'):
            attachments_data = attachments()
        # Onsite Field -Downloadable Files for Advertisement >> Description
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'mfmp-bid-detail > section > table tr > td.mat-cell.cdk-cell.cdk-column-description.mat-column-description').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Downloadable Files for Advertisement >> Description
        # Onsite Comment -None

            attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, 'mfmp-bid-detail > section > table tr > td.mat-cell.cdk-cell.cdk-column-description.mat-column-description a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

# Format 2
    

# Onsite Field -Downloadable Files for Advertisement
# Onsite Comment -Note:In page_main Click on "mfmp-bid-detail > div > button" this button than grab the data...If this button is not present than skip
# Ref_url=https://vendor.myfloridamarketplace.com/search/bids/detail/206
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'mfmp-bid-detail > section > table'):
            attachments_data = attachments()
        # Onsite Field -Downloadable Files for Advertisement >> Description
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'mfmp-bid-detail > section > table tr > td.mat-cell.cdk-cell.cdk-column-description.mat-column-description').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Downloadable Files for Advertisement >> Description
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'mfmp-bid-detail > section > table tr > td.mat-cell.cdk-cell.cdk-column-description.mat-column-description a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass    

    # Onsite Field -Commodity Codes >> Description
    # Onsite Comment -None
    try:
        notice_data.category = page_main.find_element(By.CSS_SELECTOR, "mfmp-commodity-codes-list tr > td.mat-cell.cdk-cell.cdk-column-description.mat-column-description.ng-star-inserted").text
        cpv_codes = fn.CPV_mapping("assets/us_myfloridamarpl_ca_cpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://vendor.myfloridamarketplace.com/search/bids"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/mfmp-root/mfmp-bids-public-search-dashboard/main/mfmp-search-layout/mat-drawer-container/mat-drawer-content/mfmp-bid-table/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/mfmp-root/mfmp-bids-public-search-dashboard/main/mfmp-search-layout/mat-drawer-container/mat-drawer-content/mfmp-bid-table/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/mfmp-root/mfmp-bids-public-search-dashboard/main/mfmp-search-layout/mat-drawer-container/mat-drawer-content/mfmp-bid-table/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/mfmp-root/mfmp-bids-public-search-dashboard/main/mfmp-search-layout/mat-drawer-container/mat-drawer-content/mfmp-bid-table/table/tbody/tr'),page_check))
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
