from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_wbgeprocure_rei"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_wbgeprocure_rei"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_wbgeprocure_rei'
    
    notice_data.main_language = 'EN'
   
    notice_data.currency = 'USD'
   
    notice_data.notice_type = 5
   
    notice_data.procurement_method = 2
    
    # Onsite Field -Procurement Number
    # Onsite Comment -None

     # Onsite Field -Procurement
    # Onsite Comment -if notice_no is not present  in "Procurement Number" field then split the notice_no from url
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.custom-string-cell').text
    except Exception as e:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.uri-cell.sortable.renderable > a').get_attribute("href").split('advertisement/')[1].split('/view.html')[0].strip()
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.uri-cell.sortable.renderable').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publication Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -EOI Deadline
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td.uri-cell.sortable.renderable > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#rfx-page > div.rfx-content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, '#formToSubmit > div:nth-child(10) >  div').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, '#formToSubmit > div:nth-child(10) >  div').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -None

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Category")]//following::ul[1]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'the World Bank'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_parent_id = 1012
        org_country =page_details.find_element(By.CSS_SELECTOR, '#formToSubmit > div:nth-child(11) > div:nth-child(2)').text.split('Project Country')[1].strip()
        if '-' in org_country:
            org_country1 =org_country.split('\n')
            for code in org_country1:
                org_country = code.split('-')[0].strip()
                try:
                    customer_details_data.org_country = re.findall('^[a-zA-Z]{2,}$',org_country)[0]
                except:
                    customer_details_data.org_country = 'US'
        else:
            customer_details_data.org_country = 'US' 
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        performance_country1 =page_details.find_element(By.CSS_SELECTOR, '#formToSubmit > div:nth-child(11) > div:nth-child(2)').text.split('Project Country')[1].strip()
        if '-' in performance_country1:
            performance_country2 =performance_country1.split('\n')
            for code in performance_country2:
                performance_country_data = performance_country()
                performance_country3 = code.split('-')[0].strip()
                try:
                    performance_country_data.performance_country = re.findall('^[a-zA-Z]{2,}$',performance_country3)[0]
                except:
                    performance_country_data.performance_country = 'US'
                notice_data.performance_country.append(performance_country_data)
        else:
            performance_country_data = performance_country()
            performance_country_data.performance_country = 'US'
            notice_data.performance_country.append(performance_country_data)
            
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__)) 
        pass
    
    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = 1012
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#formToSubmit > div:nth-child(20) > div'):
            
            external_url = single_record.find_element(By.CSS_SELECTOR, '#documents  tr > td.file-upload-cell a').get_attribute('href')
            if external_url is not None:
                attachments_data = attachments()
                attachments_data.external_url = external_url
                
        # Onsite Field -Document Description
        # Onsite Comment -ref_url : "https://wbgeprocure-rfxnow.worldbank.org/rfxnow/public/advertisement/2064/view.html"

                attachments_data.file_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Document Description")]//following::td[1]').text
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Advertisement Attachments
# Onsite Comment -ref_url : "https://wbgeprocure-rfxnow.worldbank.org/rfxnow/public/advertisement/1915/view.html"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#formToSubmit > div:nth-child(18) > div'):
            external_url = single_record.find_element(By.XPATH, '//*[contains(text(),"Download ")]//following::td[3]//a[1]').get_attribute('href')
            if external_url is not None:
                attachments_data = attachments()
                attachments_data.external_url = external_url

                attachments_data.file_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Attachment Name")]//following::td[1]').text
                
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://wbgeprocure-rfxnow.worldbank.org/rfxnow/public/advertisement/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,7):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="advertisementsGrid"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="advertisementsGrid"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="advertisementsGrid"]/table/tbody/tr')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="advertisementsGrid"]/ul/li[4]/a')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="advertisementsGrid"]/table/tbody/tr'),page_check))
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