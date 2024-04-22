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
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_planetbids_ca"
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
    notice_data.script_name = 'us_planetbids_ca'
    
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
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Posted
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr.row-highlight > td:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Project Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.row-highlight > td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Invitation #
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.row-highlight > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Stage
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.row-highlight > td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr.row-highlight').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -in detail_page split the data from tabs as follows "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ) , "Line Items" (selector : "#detail-navigation li.bidLineItems") , "Documents" (selector : "#detail-navigation li.bidDocs") , Addenda/Emails (selector : "li.bidAddendaAndEmails")	,  Awards ( selector : ul > li.bidAwards)
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.bid-detail-wrapper').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Scope of Services
    # Onsite Comment -split the data between "Scope of Services" and "Other Details" field

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid information >>  Bid Detail >>  Estimated Bid Value
    # Onsite Comment -if the cost is like "Range between $15 Million and $20 Million" then take only 2nd value i.e "$20 Million" it will be multiplied by 1000000 = 2000000" , split the data after "Estimated Bid Value" , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/102080"

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Detail")]//following::div[70]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid information >>  Bid Detail >>  Estimated Bid Value
    # Onsite Comment -if the cost is like "Range between $15 Million and $20 Million" then take only 2nd value i.e "$20 Million" it will be multiplied by 1000000 = 2000000" , split the data after "Estimated Bid Value" , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/102080"

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Detail")]//following::div[70]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid information >>  Bid Detail >> Categories
    # Onsite Comment -in detail_page split the data from tab as follows "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" )

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Detail")]//following::div[39]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    


# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in None.find_elements(By.None, 'None'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'PLANETBIDS'
        # Onsite Field -Bid Detail >> Address
        # Onsite Comment -go to "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ), split the data between "Address" and "County" field

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(14)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Bid Detail >> County
        # Onsite Comment -go to "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ), split the data after "County"

            try:
                customer_details_data.org_country = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(15)').text
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'EN'
        # Onsite Field -Contact Information >> Contact Info
        # Onsite Comment -go to "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ), split the data between "Contact Info" and "contact number" , for ex."Vanessa Delgado 619-236-6248" , here take only "Vanessa Delgado"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Info")]//following::div[1]//div[2]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Information >> Contact Info
        # Onsite Comment -go to "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ), split only number from "Contact Info" field, for ex."Vanessa Delgado 619-236-6248" , here take only "619-236-6248"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Info")]//following::div[1]//div[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Information >> Contact Info
        # Onsite Comment -go to "Bid information" (selector: "#detail-navigation > ul > li.bidInformation" ), split only email from "Contact Info" field, grab only second line for ex. "CDelgado@sandiego.gov"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Info")]//following::div[1]//div[2]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    



# Onsite Field -None
# Onsite Comment -Go to "Line Items" tab ( selector : #detail-navigation  li.bidLineItems) for lot_details , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/110887#"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.bid-line-items'):
            lot_details_data = lot_details()
        # Onsite Field -Item Code
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.ember-dragula > table > tbody > tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.ember-dragula > table > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -UOM
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'div.ember-dragula > table > tbody > tr > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Qty
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'div.ember-dragula > table > tbody > tr > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Unit Price
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div.ember-dragula > table > tbody > tr > td:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

               # Onsite Field -None
        # Onsite Comment -Go to "Awards" tab  ( selector : ul > li.bidAwards) for award details

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ember3121 > div.awarded-info-txt > div:nth-child(2)'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -Go to "Awards" tab  ( selector : ul > li.bidAwards) for award details  , split only bidder_name for ex."The project has been awarded to Tevora Business Solutions, Inc." , here take only "Tevora Business Solutions, Inc." , ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/107142#"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div.awarded-info-txt > div:nth-child(2)').text
			
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
# Onsite Comment -for attachments go to "Documents" tab ( selector : #detail-navigation  li.bidDocs )

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.bid-docs'):
            attachments_data = attachments()
        # Onsite Field -Title
        # Onsite Comment -for attachments go to "Documents" tab ( selector : #detail-navigation  li.bidDocs )

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'tr  td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File Name
        # Onsite Comment -for attachments go to "Documents" tab ( selector : #detail-navigation  li.bidDocs )   ,  split only file_type, for ex."RFP FS-24-01 Finance Audit Consulting Services_FINAL.pdf" , here take only "pdf"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'tr  td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Size
        # Onsite Comment -for attachments go to "Documents" tab ( selector : #detail-navigation  li.bidDocs )

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'tr  td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Download
        # Onsite Comment -for attachments go to "Documents" tab ( selector : #detail-navigation  li.bidDocs ),   Download attachments from "Download" button

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'tr  td:nth-child(5) > div a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


# Onsite Field -Addenda
# Onsite Comment -for attachments go to "Addenda/Emails" tab (selector : "#detail-navigation > ul > li.bidAddendaAndEmails")

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.is-bid-cancelled > div > div.ember-view'):
            attachments_data = attachments()
        # Onsite Field -Addenda
        # Onsite Comment -for attachments go to "Addenda/Emails" tab (selector : "#detail-navigation > ul > li.bidAddendaAndEmails")   ,     you have to open tabs for file_name           ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/107221#"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div > div.set-body.set-addendum-body > p').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
            # Onsite Field -Addenda
            # Onsite Comment -for attachments go to "Addenda/Emails" tab (selector : "#detail-navigation > ul > li.bidAddendaAndEmails")   ,     you have to open tabs for attachments        ref_url : "https://pbsystem.planetbids.com/portal/17950/bo/bo-detail/107221#"
            
            external_url = page_details.find_element(By.CSS_SELECTOR, 'div.set-body.set-addendum-body > div > button').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
    urls = ["https://pbsystem.planetbids.com/portal/17950/bo/bo-search"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody tr.row-highlight'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody tr.row-highlight')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody tr.row-highlight')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tbody tr.row-highlight'),page_check))
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
