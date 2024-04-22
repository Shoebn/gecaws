from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "hk_ha_rei"
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

#Note:Open the site then click on "Expression of Interest" and grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "hk_ha_rei"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'hk_ha_rei'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'HK'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'HKD'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 5
    
    # Onsite Field -Reference

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject
    # Onsite Comment -Note:Take local_title in textform

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Closing Date
    # Onsite Comment -None 17 November 2023 (12:00 noon Hong Kong time)

    try:
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_deadline_date = re.findall('\d+ \w+ \d{4}',notice_deadline1)[0]
        notice_deadline_time = re.findall('\d+:\d+',notice_deadline1)[0]
        notice_deadline = notice_deadline_date+' '+notice_deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Tender\ AD\ Template\ Table_7677').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            
        # Onsite Field -Issue Date 7 February 2024
        try:
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Issue")]//following::td[2]').text
            try:
                publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        # Onsite Field -Subject Matter
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Subject")]//following::td[2]').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Subject Matter
        try:
            notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Subject")]//following::td[2]').text
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass    

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'HK'
            customer_details_data.org_language = 'EN'

            # Onsite Field -Hospital

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text

            # Onsite Field -Submission Location
            # Onsite Comment -Note:Take data from Submission Location only. 	Note:Splite org_address	after"Submission Location" keyword.

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Submission")])[2]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            # Onsite Field -Tender Enquiry
            # Onsite Comment -Note:Splite first line only

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Enquiry")]//following::td[2]').text.split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            # Onsite Field -Tender Enquiry >> Tel:
            # Onsite Comment -Note:Splite org_phone after "Tel:" and "Email:"

            try:
                org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Enquiry")]//following::td[2]').text
                if 'Tel.:' in org_phone:
                    customer_details_data.org_phone = org_phone.split('Tel.:')[1].split('\n')[0].strip()
                elif 'Tel:' in org_phone:
                    customer_details_data.org_phone = org_phone.split("Tel: ")[1].split('\n')[0].strip()                
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            # Onsite Field -Tender Enquiry >> Email:
            # Onsite Comment -Note:Splite org_email after this "Email:" keyword

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Enquiry")]//following::td[2]').text.split('Email: ')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr > td > a'):
                attachments_data = attachments()
                attachments_data.file_name = 'Tender Document'
            # Onsite Field -Links for downloading Tender Document

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
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
    urls = ["https://www.ha.org.hk/visitor/ha_visitor_index.asp?Content_ID=2001&Lang=ENG&Dimension=100&Ver=HTML"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
        
        iframe = page_main.find_element(By.XPATH,'//*[@id="childframe"]')
        page_main.switch_to.frame(iframe)
        time.sleep(3)
        
        url2 = page_main.find_element(By.LINK_TEXT, "EXPRESSION OF INTEREST").get_attribute('href')
        fn.load_page(page_main, url2, 50)
        time.sleep(5)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/table[2]/tbody/tr')))
            length = len(rows)
            for records in range(4,length-1):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/table[2]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
