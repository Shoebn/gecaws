from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gh_ppaghana_rei"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "gh_ppaghana_rei"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'gh_ppaghana_rei'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'GHS'
    
    notice_data.notice_type = 5
    
    notice_data.procurement_method = 2
    
    notice_data.document_type_description = 'Open Tenders'

    # Onsite Field -None  15th December, 2023
    # Onsite Comment -split the left side date as a publish_date

    try:
        publish_date1 = tender_html_element.find_element(By.CSS_SELECTOR, "div.list-date").text
        publish_date_day = re.findall('\d{2}',publish_date1)[0]
        publish_date_year = re.findall('\w+, \d{4}',publish_date1)[0]
        publish_date = publish_date_day+' '+publish_date_year
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline : 10th January, 2024
    # Onsite Comment -split the right side date as a notice_deadline

    try:
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR, "div.list-date").text.split('Deadline : ')[1].strip()
        notice_deadline_day = re.findall('\d{2}',notice_deadline1)[0]
        notice_deadline_year = re.findall('\w+, \d{4}',notice_deadline1)[0]
        notice_deadline = notice_deadline_day+' '+notice_deadline_year
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-title > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        page_details.refresh()
        time.sleep(3)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-md-9').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
      
    # Onsite Field -None
    # Onsite Comment -if notice_no is not available in "Pack #:" field then pass from notice_url

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Pack #:")]//following::dd[1]').text
        if notice_data.notice_no == '':
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-title > a').get_attribute("href").split('eois/')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -Eoi Name:
    # Onsite Comment - split the data after "Eoi Name:"

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Eoi Name:")]//following::dd[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

      # Onsite Field -Tender Cat:
    # Onsite Comment -Replace following keywords with given respective keywords ('Works = Works' ,
#     'Non Consultant Services = Non consultancy' ,
#     'Consultancy Services   = Consultancy' , 'Goods = Supply' , 'Technical Services = Service' )

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Cat:")]//following::dd[1]').text
        if 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Non Consultant Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Non consultancy'
        elif 'Consultancy Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Consultancy'
        elif 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Technical Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Description:
    # Onsite Comment -None
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::dd[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'GH'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Agency:
        # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Agency:")]//following::dd[1]').text
        
        # Onsite Field -Region:
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Region:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        # Onsite Field -Contact Person:
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Email :
        # Onsite Comment -None

        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email :")]//following::dd[1]').text
            email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
            customer_details_data.org_email = email_regex.findall(org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Tel :
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Tel :")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Fax :
        # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax :")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Website:
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Website:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number = 1 
        lots= page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::dd[1]').text
        for lots_data in lots.split('\n')[1:]:
            if 'ZONE' in lots_data:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
                # Onsite Field -Description:
        # Onsite Comment -split only lot_actual_number for ex."Lot 1" , "Lot 2" ref_url : "https://tenders.ppa.gov.gh/eois/4335"

                try:
                    lot_details_data.lot_actual_number = lots_data.split('–')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                # Onsite Field -Description:
        # Onsite Comment -split only lot_title for ex."LOT 1 – CONSULTANCY SERVICES FOR DESIGN REVIEW & SUPERVISION OF THE PROVISION OF SOCIO-ECONOMIC INFRASTRUCTURE IN BINDURI, LAMBUSSIE, KARAGA, EAST GONJA, AND CHEREPONI DISTRICTS (ZONE1)", here take only "CONSULTANCY SERVICES FOR DESIGN REVIEW & SUPERVISION OF THE PROVISION OF SOCIO-ECONOMIC INFRASTRUCTURE IN BINDURI, LAMBUSSIE, KARAGA, EAST GONJA, AND CHEREPONI DISTRICTS (ZONE1)", ref_url : "https://tenders.ppa.gov.gh/eois/4335"

                lot_details_data.lot_title = lots_data.split('–')[1].strip()
        
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -Additional Info:
# Onsite Comment -ref_url : "https://tenders.ppa.gov.gh/eois/4335"

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'tender documents'
        # Onsite Field -Additional Info:
        # Onsite Comment -None

        attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-9 > div a').get_attribute('href')
        
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
    urls = ["https://tenders.ppa.gov.gh/eois"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------') 
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/div'),page_check))
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
