from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_rfcl_spn"
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


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_rfcl_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'INR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.script_name = "in_rfcl_spn"
    
    notice_data.notice_type = 4
    
    notice_data.document_type_description = "Open Tenders"
          
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        if "Click to view Details" in local_title:
            local_title = local_title.replace("Click to view Details","").strip()
            notice_data.local_title = local_title
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(1) > a").get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, ' div.wapper > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Work Description")]//following::th[1]').text
        notice_data.local_description = local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description[:4500]) 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__)) 
        pass
    
    try:
        pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Pre Bid Meeting Date and time")]//following::th[1]').text
        pre_bid_meeting_date = re.findall('\d{4}-\d+-\d+',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%Y-%m-%d').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated Tender Value (INR)")]//following::th[1]').text
        if "(excl. GST)" in est_amount:
            est_amount = re.sub("[^\d+]","",est_amount)
            notice_data.est_amount =float(est_amount.replace('.','').replace(',','').strip())
            notice_data.netbudgetlc = notice_data.est_amount
        else:
            est_amount = re.sub("[^\d+]","",est_amount)
            notice_data.est_amount =float(est_amount.replace('.','').replace(',','').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        document_cost = page_details.find_element(By.XPATH, '(//*[contains(text(),"Tender Fee (INR)")])[1]//following::th[1]').text
        document_cost = re.sub("[^\d+]",'',document_cost)
        notice_data.document_cost = float(document_cost.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"EMD Fee (INR)")]//following::th[1]').text
        notice_data.earnest_money_deposit = earnest_money_deposit 
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Publication date and time")]//following::th[1]').text
        try:
            publish_date = re.findall('\d{4}-\d+-\d+ \d{2}:\d{2}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            publish_date = re.findall('\d{4}-\d+-\d+  \d{2}:\d{2}:\d{2}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender opening date and time")]//following::th[1]').text
        document_opening_time = re.findall('\d{4}-\d+-\d+',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%Y-%m-%d').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Closing date and time")]//following::th[1]').text
        notice_deadline = re.findall('\d{4}-\d+-\d+  \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Category")]//following::th[1]').text
        if 'Services' in notice_data.contract_type_actual:
             notice_data.notice_contract_type = 'Service'
        elif 'Works' in notice_data.contract_type_actual:
             notice_data.notice_contract_type = 'Works'
        elif 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
            
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "Ramagundam Fertilizers and Chemicals Limited"
        
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Address")])[2]//following::th[1]').text
        except:
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Address")])//following::th[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
            
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Name")])[3]//following::th[1]').text
        except:
            pass
            

        try:
            customer_details_data.org_email= page_details.find_element(By.XPATH, '(//*[contains(text(),"Email")])//following::th[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
            
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '(//*[contains(text(),"Phone no")])//following::th[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        org_parent_id ="7624167"
        customer_details_data.org_parent_id = int(org_parent_id)
        
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:  
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' tbody > tr > th:nth-child(2)> a'):
            attachments_data = attachments()

            attachments_data.file_name = "Tender Files"

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.file_type = "pdf"

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)      
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
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.rfcl.co.in/opentender.php'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/main/div/div[2]/div/div/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/main/div/div[2]/div/div/div[2]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
            if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
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
