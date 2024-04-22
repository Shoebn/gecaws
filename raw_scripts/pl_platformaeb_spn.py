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
SCRIPT_NAME = "pl_platformaeb_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'pl_platformaeb_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'PLN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Id
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.x-grid-row td.x-grid-cell.x-grid-cell-gridcolumn-1014').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Awarding procedure no
    # Onsite Comment -if notice_no is not available in "Id" then split the notice_no from "Awarding procedure no"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.x-grid-cell.x-grid-cell-gridcolumn-1016').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Name
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.x-grid-cell.x-grid-cell-gridcolumn-1017 > div').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of purchase order
    # Onsite Comment -Replace following keywords with given respective keywords ('Service =Service', 'Construction work  = Works' , 'Delivery = Supply')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.x-grid-cell.x-grid-cell-gridcolumn-1025').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Awarding procedure status
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x-grid-cell-gridcolumn-1027').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Creation date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr td.x-grid-cell.x-grid-cell-gridcolumn-1032.x-grid-cell-last").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Stage closing date:
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr> td.x-grid-cell.x-grid-cell-gridcolumn-1029").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Name
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.x-grid-cell.x-grid-cell-gridcolumn-1017 > div a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -there are two tabs available to grab data as follows 1)Awarding procedure settings  2)Sponsor's attachments
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ext-comp-1010-body').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'tr> td.x-grid-cell.x-grid-cell-gridcolumn-1029').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description of awarding procedure:
    # Onsite Comment -split the data after "Description of awarding procedure:"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description of awarding procedure:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div > #ext-comp-1011'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'PL'
            customer_details_data.org_language = 'PL'
        # Onsite Field -Sponsor's company
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'td.x-grid-cell.x-grid-cell-gridcolumn-1019').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Ordering party
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'td.x-grid-cell.x-grid-cell-gridcolumn-1020').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Awarding procedure status
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, 'td.x-grid-cell.x-grid-cell-gridcolumn-1021').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Awarding procedure item >> Description of an awarding procedure item and evaluation criteria
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div #fieldset-1035'):
            lot_details_data = lot_details()
        # Onsite Field -Awarding procedure item description
        # Onsite Comment -click on "+" button to open lot details,  ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/422649/zapytanie-o-cene-rfq-na-modernizacje-systemu-kontroli-dostepu-skd-wraz-z-wizualizacja-zdarzen-systemu-kontroli-dostepu-oraz-systemu-sygnalizacji-pozaru-ssp"

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarding procedure item description")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quantity
        # Onsite Comment -click on "+" button to open lot details,  ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/422649/zapytanie-o-cene-rfq-na-modernizacje-systemu-kontroli-dostepu-skd-wraz-z-wizualizacja-zdarzen-systemu-kontroli-dostepu-oraz-systemu-sygnalizacji-pozaru-ssp"

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.XPATH, '//*[contains(text(),"Quantity")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Unit
        # Onsite Comment -click on "+" button to open lot details,  ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/422649/zapytanie-o-cene-rfq-na-modernizacje-systemu-kontroli-dostepu-skd-wraz-z-wizualizacja-zdarzen-systemu-kontroli-dostepu-oraz-systemu-sygnalizacji-pozaru-ssp"

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.XPATH, '(//*[contains(text(),"Unit")])[3]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Type of purchase order
        # Onsite Comment -click on "+" button to open lot details,  ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/422649/zapytanie-o-cene-rfq-na-modernizacje-systemu-kontroli-dostepu-skd-wraz-z-wizualizacja-zdarzen-systemu-kontroli-dostepu-oraz-systemu-sygnalizacji-pozaru-ssp"

            try:
                lot_details_data.contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.x-grid-cell.x-grid-cell-gridcolumn-1025').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -detail_page >> "Sponser's Attachments"  tab
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div #gridview-1072'):
            attachments_data = attachments()
        # Onsite Field -"Sponser's Attachments"  tab  >> Name
        # Onsite Comment -ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/417035/dostawa-do-ec-siekierki-10-szt-wziernikow-fi-150mm-wg-rys-3-322-01-1"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'tr> td.x-grid-cell.x-grid-cell-gridcolumn-1062 > div').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -"Sponser's Attachments"  tab  >> Size
        # Onsite Comment -ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/417035/dostawa-do-ec-siekierki-10-szt-wziernikow-fi-150mm-wg-rys-3-322-01-1"

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'tr > td.x-grid-cell.x-grid-cell-gridcolumn-1063').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -detail_page >> "Sponser's Attachments"  tab
        # Onsite Comment -ref_url "https://platforma.eb2b.com.pl/open-preview-auction.html/417035/dostawa-do-ec-siekierki-10-szt-wziernikow-fi-150mm-wg-rys-3-322-01-1"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'tr > td.x-grid-cell.x-grid-cell-gridcolumn-1060 > div > img').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -"Sponser's Attachments"  tab  >> Download files >> Download all sponsor's attachments
        # Onsite Comment -ref_url : "https://platforma.eb2b.com.pl/open-preview-auction.html/417035/dostawa-do-ec-siekierki-10-szt-wziernikow-fi-150mm-wg-rys-3-322-01-1"

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#menuitem-1086 a').get_attribute('href')
            
        
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://platforma.eb2b.com.pl/open-auctions.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="gridview-1033"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="gridview-1033"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="gridview-1033"]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="gridview-1033"]/table/tbody/tr'),page_check))
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