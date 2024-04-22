from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_caleprocure_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
import os
import csv
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.support.ui import Select
import gec_common.web_application_properties as application_properties
import gec_common.Doc_Download
import pandas as pd
from bs4 import BeautifulSoup
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_caleprocure_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global HTMLFile
    notice_data = tender()

    notice_data.script_name = 'us_caleprocure_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.notice_no = tender_html_element.select_one('td:nth-of-type(3)').getText()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        document_type_description1 = tender_html_element.select_one('td:nth-of-type(5)').getText()
        document_type_description2 = tender_html_element.select_one('td:nth-of-type(6)').getText()
        notice_data.document_type_description = document_type_description1+' '+document_type_description2
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.select_one('td:nth-of-type(4)').getText()
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.select_one('td:nth-of-type(7)').getText()
        try:
            notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+[apAP][mM]',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\d+/\d+/\d{4}  \d+:\d+[apAP][mM]',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y  %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    org_name = tender_html_element.select_one('td:nth-of-type(2)').getText()
    
    try:
        notice_data.notice_text = tender_html_element.getText()
    except:
        pass
    
    try:
        department = tender_html_element.select_one('td:nth-of-type(1)').getText()
    except:
        pass
  
    try:      
        notice_data.notice_url = 'https://caleprocure.ca.gov/event/'+department+'/'+notice_data.notice_no                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try: 
        publish_date = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"Published Date")]//following::span[1]'))).text
        try:
            publish_date = re.findall('\d+/\d+/\d{4}  \d+:\d+[apAP][mM]',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y  %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+[apAP][mM]',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:  
        pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Pre Bid Conference")]//following::div[1]').text.split("Date:")[1].split("\n")[0]
        pre_bid_meeting_date = re.findall('\d+/\d+/\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%m/%d/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.pre_bid_meeting_date)
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#serviceAreaTable > tbody > tr'):
            customer_details_data = customer_details()

            customer_details_data.org_name = org_name

            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'

            try:
                org_city = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                if len(org_city) > 1:
                    customer_details_data.org_city = org_city
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            try:
                contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::strong[1]').text
                if len(contact_person) > 1:
                    customer_details_data.contact_person = contact_person
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass


            try:
                org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::span[1]').text
                if len(org_phone) > 1:
                    customer_details_data.org_phone = org_phone
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass


            try:
                org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::a[1]').text
                if len(org_email) > 1:
                    customer_details_data.org_email = org_email
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.class_at_source = "CPV"
    
    try: 
        category = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#unspscTable > tbody > tr'):
            try:
                category_1 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.strip()
                category += category_1
                category += ','
                cpv_codes = fn.CPV_mapping("assets/us_caleprocure_spn_unspscpv.csv",category_1)
                for cpv_code1 in cpv_codes:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = cpv_code1.strip()
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
                    
            except:
                pass
        notice_data.category = category.rstrip(',')
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__)) 
        pass
    
    try: 
        cpv_at_source = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#unspscTable > tbody > tr'):
            try:
                category_1 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.strip()
                cpv_codes = fn.CPV_mapping("assets/us_caleprocure_spn_unspscpv.csv",category_1)
                for cpv_code1 in cpv_codes:
                    cpv_at_source += cpv_code1.strip()
                    cpv_at_source += ','
            except:
                pass
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="main"]/div[2]').get_attribute("outerHTML")                     
    except:
        pass

        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')

arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost'] 
page_details = fn.init_chrome_driver(arguments)
tmp_dwn_dir = application_properties.TMP_DIR#.replace('/',"\\")  #for linux remove --> .replace('/',"\\")
experimental_options = {"prefs": {"download.default_directory": tmp_dwn_dir}}
page_main = fn.init_chrome_driver(arguments=[], experimental_options = experimental_options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    url = 'https://caleprocure.ca.gov/pages/Events-BS3/event-search.aspx'
    logging.info(url)
    logging.info('----------------------------------')
    fn.load_page(page_main, url,80)

    clk = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="RESP_INQA_HD_VW_GR$hexcel$0"]' )))
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(10)
    
    clk1 = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#downloadButton.btn.btn-primary' )))
    page_main.execute_script("arguments[0].click();",clk1)
    time.sleep(10)
    
    xlsfile_path = application_properties.TMP_DIR+"/ps.xls"
 
    htmlfile_path = application_properties.TMP_DIR+"/ps.html"

    os.rename(xlsfile_path, htmlfile_path)
    HTMLFile = open(htmlfile_path, "r")
    
    index = HTMLFile.read() 
    Parse = BeautifulSoup(index, 'lxml') 
    for tender_html_element in Parse.select('tr')[1:]:
        extract_and_save_notice(tender_html_element)
        if notice_count >= MAX_NOTICES:
            break

        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    os.remove(application_properties.TMP_DIR+"/ps.html")
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
