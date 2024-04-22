from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_vic_spn"
log_config.log(SCRIPT_NAME)
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
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_vic_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
 
    notice_data.script_name = 'au_vic_spn'
 
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'AUD'

    notice_data.procurement_method = 2

    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -Note:If in this "td.tender-code-state > span" selector have this keywod "Expression of Interest" thke notice type -"5" and "Request for Tender"/"Request for Quotation"/"Request for Tender"/"Draft For Comment" take notice type -"4" and "Advanced Tender Notice" take notice type -"3" and  and "Unadvertised Closed Tender" take notice type -"16"
    notice_data.notice_type = 4
    
    # Onsite Field -RFx Number Status & Type
    # Onsite Comment -None
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender-code-state > span').text
        if 'Expression of Interest' in notice_type:
            notice_data.notice_type = 5
        elif 'Request for Tender' in notice_type or 'Request for Quotation' in notice_type or 'Draft For Comment'in notice_type:
            notice_data.notice_type = 4
        elif 'Advanced Tender Notice' in notice_type:
            notice_data.notice_type = 3
        elif 'Unadvertised Closed Tender' in notice_type:
            notice_data.notice_type = 16
        else:
            pass
    except:
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender-code-state > span > b').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > span > div > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date >> Opened
    # Onsite Comment -None
    try:
        p_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.tender-date > span > span.opening_date").text
        publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+',p_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Date >> Closing
    # Onsite Comment -None

    try:
        deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.tender-date > span > span.closing_date").text
        notice_deadline = re.findall('\d+ \w+ \d{4} \d+:\d+',deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    # Onsite Comment -None
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, "td > span > div > div:nth-child(3)").text
        cpv_at_source_regex = re.compile(r'\d{8}')
        cpv_list = cpv_at_source_regex.findall(notice_data.category)
        for code in cpv_list:
            cpv_codes_list = fn.CPV_mapping("assets/au_vic_spn_unspscpv.csv",code)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = each_cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Current Tenders'      
    
    # Onsite Field -Details
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > span > div > div:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, '#tenderDescription > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -Note:Splite bteween this "Description" or "Specification Documents"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, '#tenderDescription > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try: 
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Issued By")]/.').text.split('Issued By')[1].strip()
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#opportunityContacts > div:nth-child(2) > div > div > ul'):
    # Onsite Field -Details
    # Onsite Comment -Note:Splite after "Issued by:" this keyword

            

    # Onsite Field -Enquiries
    # Onsite Comment -None

            try:
                customer_details_data.contact_person = single_record.find_element(By.CSS_SELECTOR, 'li:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

    # Onsite Field -Enquiries
    # Onsite Comment -Note:Splite after "Phone" or "Office" or "Mobile"this keyword data.
    #Ref_url=https://www.tenders.vic.gov.au/tender/view?id=261315 , https://www.tenders.vic.gov.au/tender/view?id=261382
            try:
                if 'Phone:' in single_record.text:
                    customer_details_data.org_phone = single_record.text.split('Phone:')[1].split('\n')[0].strip()
                elif 'Office:' in single_record.text:
                    customer_details_data.org_phone = single_record.text.split('Office:')[1].split('\n')[0].strip()
                elif 'Mobile:' in single_record.text:
                    customer_details_data.org_phone = single_record.text.split('Mobile:')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

    # Onsite Field -Enquiries
    # Onsite Comment -None

            try:
                org_email = single_record.text
                email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
                customer_details_data.org_email = email_regex.findall(org_email)[0]
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenders.vic.gov.au/tender/search?preset=open&page="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/div/div/div[3]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div/div/div[3]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div/div/div[3]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/main/div/div/div[3]/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break 
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
