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
SCRIPT_NAME = "ca_bcbid_spn"
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
    notice_data.script_name = 'ca_bcbid_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'CAD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Opportunity ID
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Opportunity Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Issue Date and Time(Pacific Time)
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#body_x_grid_grd > tbody > tr > td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date and Time(Pacific Time)
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#body_x_grid_grd > tbody > tr > td:nth-child(7)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Opportunity ID
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.wrapper').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Summary Details
    # Onsite Comment -if Summary Details not available then take local_title.

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Summary Details')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Summary Details')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated Contract Duration (in months)
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),'Estimated Contract Duration (in months)')]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -1.take customer_details after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details.

    try:              
        for single_record in page_details1.find_elements(By.XPATH, '//*[@id="body_x_tabc_rfpAdditional RFx Info"]'):
            customer_details_data = customer_details()
        # Onsite Field -Organization (Issued by)
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(11)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'CA'
            customer_details_data.org_language = 'EN'
        # Onsite Field -None
        # Onsite Comment -1.take contact_person after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.in contact_person take only names. eg., here "Nimmi	Takkar	Nimmi.Takkar@gov.bc.ca" take "Nimmi	Takkar" in contact_person. remove space. 				3.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175260".

            try:
                customer_details_data.contact_person = page_details1.find_element(By.CSS_SELECTOR, '#body_x_tabc_rfpAdditional\ RFx\ Info_prxrfpAdditional\ RFx\ Info_x_grid_rfp_200524212531_grd > tbody').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.take org_email after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.in org_email take only email id. eg., here "Nimmi	Takkar	Nimmi.Takkar@gov.bc.ca" take "Nimmi.Takkar@gov.bc.ca" in org_email. 				3.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175260".

            try:
                customer_details_data.org_email = page_details1.find_element(By.CSS_SELECTOR, '#body_x_tabc_rfpAdditional\ RFx\ Info_prxrfpAdditional\ RFx\ Info_x_grid_rfp_200524212531_grd > tbody').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Regions
        # Onsite Comment -1.take org_state after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176263"

            try:
                customer_details_data.org_state = page_details1.find_element(By.XPATH, '//*[contains(text(),'Regions')]//following::div[2]').text
            except Exception as e:
                logging.info("Exception in org_state: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postal Code
        # Onsite Comment -1.take postal_code after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176263"

            try:
                customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),'Postal Code')]//following::div').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Office Street Address
        # Onsite Comment -1.take org_address after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176263"

            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),'Office Street Address')]//following::div').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Official Contact Details
        # Onsite Comment -1.split org_phone between "Phone: " and "Fax: ".	2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176356".

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),'Official Contact Details')]//following::div').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Official Contact Details
        # Onsite Comment -1.split org_fax after "Fax: ".		2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176356".

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),'Official Contact Details')]//following::div').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#body_x_grid_phcgrid'):
            lot_details_data = lot_details()
        # Onsite Field -Opportunity Description
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Opportunity Description
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#body_x_tabc_rfp_ext_prxrfp_ext_x_placeholder_rfp_160831232112 > tbody > tr:nth-child(2) > td > div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175258"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#body_x_tabc_rfp_ext_prxrfp_ext_x_prxDoc_x_grid_grd > tbody > tr > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175258"

            try:
                attachments_data.file_description = page_details.find_element(By.CLASS_NAME, 'li-file-upload  file_uploaded').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175258" 			2.split file_type. eg., here "Appendix C_Submission Declaration Form.docx" take ".docx" in file_type.

            try:
                attachments_data.file_type = page_details.find_element(By.CLASS_NAME, 'li-file-upload  file_uploaded').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175258"

            attachments_data.external_url = page_details.find_element(By.CLASS_NAME, 'li-file-upload  file_uploaded').get_attribute('href')
            
        
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
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,15):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="body_x_grid_grd"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="body_x_grid_grd"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="body_x_grid_grd"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="body_x_grid_grd"]/tbody/tr'),page_check))
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