from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_undp_ca"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_undp_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'mfa_undp_ca'
    
    notice_data.currency = 'USD'
    
    # Onsite Field -UNDP Office
    # Onsite Comment -Note:Splite after "-".....Ex,"UNDP CO - TURKEY" take only "TURKEY"            Note:File_name=mfa_undp_ca_countrycode.csv
    try:
        performance_country_data1 = tender_html_element.find_element(By.CSS_SELECTOR, ' tr:nth-child(4) > td:nth-child(2)').text.split("-")[1].strip()
        performance_country_data1 = performance_country_data1.title()
        performance_country_data = performance_country()
        performance_country_data.performance_country = fn.procedure_mapping("assets/mfa_undp_ca_countrycode.csv",performance_country_data1)
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    notice_data.main_language = 'EN'
   
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -Title :
    # Onsite Comment -Note:Split after "Title :" this keyword

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(1) > th').text.split("Title : ")[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Reference Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # category
    
    
    # Onsite Field -Posted on
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr:nth-child(3) > td:nth-child(2)").text
        publish_date2 = re.findall('\d+-\w+',publish_date)[0]
        publish_date1 = publish_date.split('-')[-1]
        publish_date1 = '-20' + publish_date1
        publish_date = publish_date2 + publish_date1
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.notice_url = 'https://procurement-notices.undp.org/view_awards.cfm'
    
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'body > table > tbody > tr:nth-child(1) > td.content > table').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(5) > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Method
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(6) > td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass    
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, ' tr:nth-child(11) > td').text.split("Description of Contract :")[1].strip()
        notice_data.notice_summary_english =notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'United Nations Development Programme'
        customer_details_data.org_parent_id = '7586854'
    # Onsite Field -UNDP Office
    # Onsite Comment -None

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(4) > td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -UNDP Office
    # Onsite Comment -Note:Splite after "-".....Ex,"UNDP CO - TURKEY" take only "TURKEY"            Note:File_name=mfa_undp_ca_countrycode.csv
        try:
            customer_details_data.org_country = performance_country_data.performance_country
        except Exception as e:
            logging.info("Exception in org_country: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'EN'      

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number= 1
    # Onsite Field -Title :
    # Onsite Comment -Note:Split after "Title :" this keyword

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = lot_details_data.lot_title
        
        award_details_data = award_details()

        # Onsite Field -Name of Contractor
        # Onsite Comment -None

        award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(7) > td:nth-child(2)').text
        # Onsite Field -Country of Contractor
        # Onsite Comment -None

        bidder_country = tender_html_element.text.split("Country of Contractor :")[1].split("\n")[0].strip()
        bidder_country = bidder_country.title()
        award_details_data.bidder_country = fn.procedure_mapping("assets/mfa_undp_ca_countrycode.csv",bidder_country)

        # Onsite Field -Date of Contract Signature
        # Onsite Comment -None

        award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(9) > td:nth-child(2)').text
        award_date2 = re.findall('\d+-\w+',award_date)[0]
        award_date1 = award_date.split('-')[-1]
        award_date1 = '-20' + award_date1
        award_date = award_date2 + award_date1
        award_details_data.award_date = datetime.strptime(award_date,'%d-%b-%Y').strftime('%Y/%m/%d')

        # Onsite Field -Contract Amount in US
        # Onsite Comment -None

        grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(10) > td:nth-child(2)').text
        grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
        award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace('.','').replace(',','').strip())

        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    urls = ["https://procurement-notices.undp.org/view_awards.cfm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[1]/td[2]/table/tbody')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[1]/td[2]/table/tbody')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
        except:
            logging.info("No new record")
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
