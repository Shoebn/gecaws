from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_saskten"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
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
SCRIPT_NAME = "ca_saskten"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global row_number
    notice_data = tender()
  
    notice_data.script_name = 'ca_saskten'
  
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.currency = 'CAD'
  
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -If document_type_description have keywords like "Invitation to Tender/Request for Proposal/Request for Quotation/Request for Bid" then notice type will be 4 and for "Advanced Contract Award Notice" then notice type will be 7 and for "Request for Pre-Qualification/Request for Qualifications" then notice type will be 2  

    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/table/tbody/tr/td[4]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Open Date
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/table/tbody/tr/td[5]').text.replace("\n",' ')
        publish_date = re.findall('\w+ \d+, \d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%b %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    # Onsite Field -Close Date
    # Onsite Comment -None

    try:
        notice_deadline = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/table/tbody/tr/td[6]').text.replace("\n",' ')
        notice_deadline = re.findall('\w+ \d+, \d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:  
        notice_data.local_title = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/table/tbody/tr/td[2]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        tender_details = page_main.find_element(By.XPATH,'/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/table/tbody/tr/td[1]/div')
        page_main.execute_script("arguments[0].click();",tender_details)
        time.sleep(5)
    except:
        pass
    row_number += 1
    # Onsite Field -None
    # Onsite Comment -click on '+' sign on tender_html_page  to get the data
    try:
        notice_data.notice_text += page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/div/table/tbody/tr/td[2]/table/tbody').get_attribute("outerHTML")                     
    except:
        pass
    # Onsite Field -Competition Type:
    # Onsite Comment -click on '+' sign on tender_html_page  to get the data

    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/div/table/tbody/tr/td[2]/table/tbody/tr/td[1]/table/tbody/tr[6]/td/table/tbody/tr/td').text
        if 'Invitation to Tender' in notice_data.document_type_description or 'Request for Proposal' in notice_data.document_type_description or 'Request for Bid' in notice_data.document_type_description:
            notice_data.notice_type = 4
        elif 'Advanced Contract Award Notice' in notice_data.document_type_description:
            notice_data.notice_type = 7
        elif 'Request for Pre-Qualification' in notice_data.document_type_description or 'Request for Qualifications' in notice_data.document_type_description:
            notice_data.notice_type = 2
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -click on '+' sign on tender_html_page  to get the data

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Response Address:
    # Onsite Comment -None

        customer_details_data.org_name =  page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/div/table/tbody/tr/td[2]/table/tbody/tr/td[3]/table/tbody/tr[2]/td').text
        
    # Onsite Field -Response Address:
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/div/table/tbody/tr/td[2]/table/tbody/tr/td[3]/table/tbody/tr[3]/td').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact:
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/div/table/tbody/tr/td[2]/table/tbody/tr/td[3]/table/tbody/tr[7]/td').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Phone:
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/div/table/tbody/tr/td[2]/table/tbody/tr/td[3]/table/tbody/tr[8]/td').text.split("Phone:")[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Email:
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[1]/div[2]/div['+str(row_number)+']/div/table/tbody/tr/td[2]/table/tbody/tr/td[3]/table/tbody/tr[9]/td/span/a').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'CA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    row_number += 1
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    urls = ['https://sasktenders.ca/content/public/Search.aspx'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ContentPlaceHolder1"]/table/tbody/tr'))).text
                row_number = 1
                for records in range(0,51,1):
                    extract_and_save_notice(records)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/form/div[9]/div/div/div[3]/div/div[3]/div/div/div/div[2]/table/tbody/tr[2]/td[3]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ContentPlaceHolder1"]/table/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
