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
SCRIPT_NAME = "mfa_undp_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'mfa_undp_spn'
    
    # Onsite Field -UNDP Country
    # Onsite Comment -Note:File_name=mfa_undp_spn_countrycode.csv

    try:
        notice_data.performance_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td.content tr > td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note:If in this "td.content tr > td:nth-child(7)" selector have this keyword "RFQ - Request for quotation" take notice_type "4" , "EOI - Expression of interest" take notice_type "5" , "ITB - Invitation to bid" take notice_type "4" , "RFP - Request for proposal" take notice_type "4" , "IC - Individual contractor" take notice_type "4" , "ITP - Invitation to pre-qualify" take notice_type "5" , "RFI - Request for Information" take notice_type "5" , "CP-QB-FBS - Call for Proposal – Quality Based Fixed Budget" take notice_type "4" , "Innovation Challenge" take notice_type "4" , "Other" take notice_type "4".
    notice_data.notice_type = 4
    
    # Onsite Field -Ref No
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.content tr > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.content tr > td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Process
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td.content tr > td:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Deadline
    # Onsite Comment -Note:Grab time also

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.content tr > td:nth-child(8)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Posted
    # Onsite Comment -Note:Grab time also

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.content tr > td:nth-child(9)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.content tr > td:nth-child(4) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'td.content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Period of assignment/services
    # Onsite Comment -Note:Splite after "Period of assignment/services" this keyword

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Period of assignment/services")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(10) > td').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Note:Split between "Description of the Assignment: " and "Period of assignment"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(10) > td').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass        
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in None.find_elements(By.None, 'None'):
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 'United Nations Development Programme'
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.source_of_funds = '7586854'
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td.content'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'United Nations Development Programme'
            customer_details_data.org_parent_id = '7586854'
        # Onsite Field -UNDP Office
        # Onsite Comment -None

            try:
                customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td.content tr > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact :
        # Onsite Comment -Note:Don't take in "<a>' tag data

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact :
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -UNDP Country
        # Onsite Comment -Note:File_name=mfa_undp_spn_countrycode.csv

            try:
                customer_details_data.org_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td.content tr > td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
#Format 1 For Attachments


# Onsite Field -None
# Onsite Comment -Note:Click on "//*[contains(text(),"Documents")]//following::a[1]" this Xpath in detail_page than grab the data
#Ref_url=https://procurement-notices.undp.org/view_negotiation.cfm?nego_id=15987
    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.od-ItemsScopeItemContent-list.od-ItemContent-list'):
            attachments_data = attachments()
        # Onsite Field -OriginalFileName
        # Onsite Comment -Note:Don't take a file extention

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'div.ms-DetailsRow-fields.fields-162 > div:nth-child(4) > div').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -OriginalFileName
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = page_details1.find_element(By.CSS_SELECTOR, 'div.ms-DetailsRow-fields.fields-162 > div:nth-child(4) > div').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'span.signalFieldValue_b9e74371 > button').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    


#Format 2 For Attachments


# Onsite Field -Name
# Onsite Comment -None
# Ref_url=https://procurement-notices.undp.org/view_notice.cfm?notice_id=98159
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td.content'):
            attachments_data = attachments()
        # Onsite Field -Documents
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Documents")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documents
        # Onsite Comment -Note:take only file extention

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Documents")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documents
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Documents")]//following::a[1]').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://procurement-notices.undp.org/index.cfm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr'),page_check))
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