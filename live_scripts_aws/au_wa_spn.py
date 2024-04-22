from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_wa_spn"
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

#Note:Open the site than click on search button

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_wa_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'au_wa_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'AUD'
   
    notice_data.main_language = 'EN'
   
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.left.top > b').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    # Onsite Comment -Note:Take a text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Date >> closing
    # Onsite Comment -None 31 Dec, 2025 2:30 PM

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.nowrap.top.sorting_1 > span.SUMMARY_CLOSINGDATE").text
        notice_deadline = re.findall('\d+ \w{3}, \d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    # Onsite Comment -Note:Select the after this "tr > td.left.top span" selected keyword
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td.left.top span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a:nth-child(1)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#hcontent > div.pcontent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Details
        # Onsite Comment -Note: split data after "Issued by" till "UNSPSC:"

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span').text.split('Issued by')[1].split('\n')[0].strip()
        # Onsite Field -Enquiries >> Person
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Person')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        # Onsite Field -Enquiries >> Phone
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Phone')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Enquiries >> Email
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Email')]//following::a[1]").text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Tender >> Region/s
        try:
            customer_details_data.org_state = page_details.find_element(By.XPATH, "//*[contains(text(),'Region/s')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -UNSPSC
    try:
        notice_data.category = page_details.find_element(By.XPATH, "(//*[contains(text(),'UNSPSC')])[2]//following::td[1]").text
        category = notice_data.category.split('- (')[0].strip()
        cpv_codes = fn.CPV_mapping("assets/au_wa_spn_unspscpv.csv",category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_url = page_details.find_element(By.CSS_SELECTOR, 'a#RESPONDENT').get_attribute("href")                     
        fn.load_page(page_details1,notice_url,80)
        time.sleep(5)
        logging.info(notice_url)
    except Exception as e:
        logging.info("Exception in notice_url1: {}".format(type(e).__name__))
        
    try:
        attch = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#hcontent > div.pcontent > div > form > table > tbody > tr > td:nth-child(1) > input')))
        page_details1.execute_script("arguments[0].click();",attch)
        time.sleep(5)
    except:
        pass
    
# Onsite Field -Download Documents  
# Onsite Comment -Note:First goto "#RESPONDENT" this page than click on "Download for Information Only" then click on "Download Document"

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#requestButton'):
            attachments_data = attachments()
            attachments_data.file_name = 'Tender Document'

            attachments_data.external_url = single_record.click()
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])  
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.attachments_cleanup()
            
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)
page_details1 = Doc_Download.page_details 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenders.wa.gov.au/watenders/tender/search/tender-search.do?CSRFNONCE=773A253C4503240385E2B935C04CFBFB&action=display-advanced-tender-search"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#btnAdvSarch')))
            page_main.execute_script("arguments[0].click();",search)
            time.sleep(10)
        except:
            pass

        try:
            for page_no in range(2,20):                                                                
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tenderSearchResultsTable"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tenderSearchResultsTable"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tenderSearchResultsTable"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tenderSearchResultsTable"]/tbody/tr'),page_check))
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
    page_details1.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
