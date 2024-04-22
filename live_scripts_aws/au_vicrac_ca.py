from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_vicrac_ca"
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


#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_vicrac_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'au_vicrac_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'AUD'
   
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
  
    notice_data.notice_type = 7
    
    notice_data.document_type_description = 'Awarded'      

    # Onsite Field -RFx Number Status & Type
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender-code-state > span > b').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > span > div > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date >> Opened
    # Onsite Comment -None Tue, 03 October 2023 5:45 pm

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.tender-date > span > span.opening_date").text
        publish_date = re.findall('\d+ \w+ \d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Details    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, "td > span > div > div:nth-child(3)").text
        cpv_regex = re.compile(r'\d{8}')
        cpv_code_list = cpv_regex.findall(notice_data.category)
        for cpv_code_li in cpv_code_list:
            cpv_codes = fn.CPV_mapping("assets/au_vicrac_ca.csv",cpv_code_li)
            for cpv in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass 
    
    # Onsite Field -Details
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > span > div > div:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')   
        
    # Onsite Field -Description
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, '#tenderDescription > div:nth-child(2)').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass           

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Details
    # Onsite Comment -Note:Splite after "Issued by:" this keyword

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td > span > div > div:nth-child(2)').text.split('Issued by:')[1].strip()

    # Onsite Field -Enquiries
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Enquiries")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Enquiries
        # Onsite Comment -Note:Splite after "Phone" or "Office" or "Mobile"this keyword data.
        #Ref_url=https://www.tenders.vic.gov.au/tender/view?id=259960 , https://www.tenders.vic.gov.au/tender/view?id=251803 , https://www.tenders.vic.gov.au/tender/view?id=251355
        try:
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Enquiries")]//following::div[1]').text
            if 'Phone' in org_phone:
                customer_details_data.org_phone = org_phone.split('Phone:')[1].split('\n')[0].strip()
            elif 'Office' in org_phone:
                customer_details_data.org_phone = org_phone.split('Office:')[1].split('\n')[0].strip()
            elif 'Mobile' in org_phone:
                customer_details_data.org_phone = org_phone.split('Mobile:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Enquiries
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Enquiries")]//following::a[2]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > a').get_attribute("href") 
        fn.load_page(page_details1,notice_url,80)
        logging.info(notice_url)
    except Exception as e:
        logging.info("Exception in notice_url2: {}".format(type(e).__name__))

    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'body > main').get_attribute("outerHTML")                     
    except:
        pass 

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
    # Onsite Field -Details
        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > span > div > div:nth-child(1)').text
        
    # Onsite Field -Results >> This Tender was awarded
    # Onsite Comment -Note:Click on "div:nth-child(2) > div > a" on page  detail and grab the data

        try:
            award_details_data = award_details()

            # Onsite Field -Supplier Information
            award_details_data.bidder_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Supplier Information")]//following::b[1]').text

            award_details_data.address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Supplier Information")]//following::tbody[1]/tr[1]/td[2]/table[1]').text
            
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass  
        
        if lot_details_data.award_details != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
page_details1 = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenders.vic.gov.au/tender/search?preset=awarded"] 
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/main/div/div/div[2]/table/tbody/tr'),page_check))
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
    page_details1.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)    
