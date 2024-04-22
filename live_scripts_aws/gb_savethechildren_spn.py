from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gb_savethechildren_spn"
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
SCRIPT_NAME = "gb_savethechildren_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'gb_savethechildren_spn'
    
    # Onsite Field -None
    # Onsite Comment -Note:csv file is pulled name as "gb_savethechildren_spn_countrycode.csv" for mapping.

    
    try:
        performance_country_data = performance_country()
        p_country = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row.meta > div:nth-child(2) > p:nth-child(1) > span').text.title().strip()
        if "," in p_country:
            p_country = p_country.split(",")[0]
            performance_country_data.performance_country = fn.procedure_mapping("assets/gb_savethechildren_spn_countrycode.csv",p_country)
        elif "Türkiye" in p_country:
            performance_country_data.performance_country = 'TR'
        else:
            performance_country_data.performance_country = fn.procedure_mapping("assets/gb_savethechildren_spn_countrycode.csv",p_country)
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:
        performance_country_data.performance_country = 'GB'
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-title > a > div > h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row.meta > div:nth-child(1) > p:nth-child(1) > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.row.meta > div:nth-child(1) > p:nth-child(2) > span").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.row.meta > div:nth-child(1) > p:nth-child(3) > span").text
        notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, "div.row.meta > div:nth-child(2) > p:nth-child(2) > span").text.strip()
        cpv_codes = fn.procedure_mapping("assets/gb_savethechildren_spn_cpv.csv",notice_data.category)
        cpv_codes = re.findall('\d{8}',cpv_codes)

        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    

    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.card-excerpt').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass    
    

    notice_data.document_type_description = 'TENDERS'
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-title > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.container.py-5 > div > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        pop_up = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ' div.stc-popup-modal-close'))).click()
    except:
        pass


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Save the Children'
        customer_details_data.org_parent_id = '6522400'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = performance_country_data.performance_country
    # Onsite Field -CONTACT INFORMATION >> Questions
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Questions")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = '6522400'
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(6) > ul > li > a'):
            attachments_data = attachments()
        # Onsite Field -DOWNLOADS
        # Onsite Comment -Note:Don't take file extention

            attachments_data.file_name = single_record.text.split(".")[0].strip()            
        
        # Onsite Field -DOWNLOADS
        # Onsite Comment -Note:Take onlt file extention

            try:
                attachments_data.file_type = single_record.text.split(".")[1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -DOWNLOADS
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.savethechildren.net/about-us/our-suppliers/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            pop_up = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ' div.stc-popup-modal-close'))).click()
        except:
            pass
        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tender-list"]/div/div/div[1]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tender-list"]/div/div/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tender-list"]/div/div/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > section.post-nav.d-none.d-md-block > div > div > div > div:nth-child(3) > div > a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tender-list"]/div/div/div[1]/div'),page_check))
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
