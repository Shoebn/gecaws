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


# ---------------------------------------------------------------------------------------------------------------------

# -- Note : 
#         1) Page_details are not avaialble in source
#         2) for lot details go to "Awarding procedure item" and click on "+" for more lot_details
#         3) some tender details don't have attachments, while others include attachment details.


# ---------------------------------------------------------------------------------------------------------------------

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pl_platformaeb_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'pl_platformaeb_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'EN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'PLN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Awarding procedure no
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.x-grid-cell.x-grid-cell-gridcolumn-1015').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Name
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.x-grid-cell.x-grid-cell-gridcolumn-1016 > div').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publication date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td.x-grid-cell.x-grid-cell-gridcolumn-1019").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -when you click on notice url it will pass into page main

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.x-grid-cell.x-grid-cell-actioncolumn-1013.x-action-col-cell.x-grid-cell-first > div > img').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.x-window-body > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div #ext-comp-1011'):
            customer_details_data = customer_details()
            customer_details_data.org_language = 'EN'
            customer_details_data.org_country = 'PL'
        # Onsite Field -Sponser's company
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.x-grid-cell.x-grid-cell-gridcolumn-1017').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ordering party
        # Onsite Comment -None

            try:
                customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.x-grid-cell.x-grid-cell-gridcolumn-1018').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Awarding procedure item
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#auctionpreviewproductsgrid-1644-body'):
            lot_details_data = lot_details()
        # Onsite Field -Awarding procedure item
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_main.find_element(By.CSS_SELECTOR, 'td > div > div > span').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quantity
        # Onsite Comment -click on "+" button to open lot details,

            try:
                lot_details_data.lot_quantity = page_main.find_element(By.XPATH, '//*[contains(text(),"Quantity")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Unit
        # Onsite Comment -click on "+" button to open lot details,

            try:
                lot_details_data.lot_quantity_uom = page_main.find_element(By.XPATH, '//*[contains(text(),"Unit")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Bids to the awarding procedure
        # Onsite Comment -note : in the award_details kidnly take only "Rank position: 1" data  , split the first line  below data after "Bidder's data"

            try:
                for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table.publish-offer-table:nth-child(1)'):
                    award_details_data = award_details()
		
                    # Onsite Field -Bidder's data
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Bidder's data")]//following::td[1]').text
			
                    # Onsite Field -Bidder's data
                    # Onsite Comment -None

                    award_details_data.address = page_main.find_element(By.XPATH, '//*[contains(text(),"Bidder's data")]//following::td[2]').text
			
                    # Onsite Field -split the numeric data after "Total"
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = None.find_element(By.XPATH, '//*[contains(text(),"Total")]//following::td[1]').text
			
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
    
# Onsite Field -None
# Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.

    try:              
        for single_record in page_main.find_elements(By.XPATH, '//*[contains(text(),"Attachments to publication")]//following::td[1]'):
            attachments_data = attachments()
        # Onsite Field -Name
        # Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.

            try:
                attachments_data.file_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Attachments to publication")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Size
        # Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.

            try:
                attachments_data.file_size = page_main.find_element(By.XPATH, '//*[contains(text(),"Attachments to publication")]//following::td[3]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachments to publication
        # Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.

            attachments_data.external_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Attachments to publication")]//following::div[1]').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://platforma.eb2b.com.pl/auction-result-publication.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="gridview-1021"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="gridview-1021"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="gridview-1021"]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="gridview-1021"]/table/tbody/tr'),page_check))
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