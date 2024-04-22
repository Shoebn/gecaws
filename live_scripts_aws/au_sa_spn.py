from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_sa_spn"
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
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_sa_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'au_sa_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'AUD'
    
    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note: if following keyword is present in detail page "Expression of Interest" take notice type -"5" if following keyword is present in detail page "Prequalification" take notice type -"6"
    
    
    # Onsite Field -Code & Status
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender-code-state > b').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > div > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date >> Closing
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.tender-date > span.closing_date").text
        notice_deadline = re.findall('\d+ \w+, \d{4}',notice_deadline)[0]
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    # Onsite Field -Details
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > div > div:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_text_data= page_details.find_element(By.CSS_SELECTOR, 'body > main > div').text
        if "Expression of Interest" in notice_text_data:
            notice_data.notice_type = 5
        elif "Prequalification" in notice_text_data:
            notice_data.notice_type = 6
        else:
            notice_data.notice_type = 4
    except:
        pass
            
    
    # Onsite Field -Category
    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Category")]//following::div[1]').text
        cpv_codes = fn.CPV_mapping("assets/au_sa_spn_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Number")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    try:
        notice_data.notice_summary_english =notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > main > div'):
            customer_details_data = customer_details()
        # Onsite Field -Details >> Issued by:
        # Onsite Comment -Note:Splite after "Issued by:" this keyword
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td > div > div:nth-child(2) > span').text.split('Issued by: ')[1]

        # Onsite Field -Enquiries
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Enquiries")]//following::li[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Enquiries
        # Onsite Comment -Note:Splite after "Phone" or "Office" this keyword data.There two words but onsite only one word available and secound word is ignore
        #Ref_url=https://www.tenders.sa.gov.au/tender/view?id=260658 , https://www.tenders.sa.gov.au/tender/view?id=261254
            
            try:
                org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Enquiries")]//following::div[1]').text
                org_phone_words = ['Office:','Phone:','Mobile:']
                for i in org_phone_words:
                    if i in org_phone:
                        customer_details_data.org_phone = org_phone.split(i)[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Enquiries
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Enquiries")]//following::div[1]/div/div/ul/li[last()]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'
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
    urls = ["https://www.tenders.sa.gov.au/tender/search?preset=open"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/div/div/div[2]/div/div[2]/div/div[2]/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div/div/div[2]/div/div[2]/div/div[2]/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div/div/div[2]/div/div[2]/div/div[2]/div[2]/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/main/div/div/div[2]/div/div[2]/div/div[2]/div[2]/table/tbody/tr'),page_check))
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
