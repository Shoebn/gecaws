from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_buyandsell_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_buyandsell_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ca_buyandsell_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CAD'
    notice_data.procurement_method = 2
    notice_data.document_type_description = 'Tender notice'
    
    # Onsite Field -take notice type "4" for "spn", and "16" for "Amendment"
    # Onsite Comment -None
    organization = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-tender-organization').text
    if 'NATO - North Atlantic Treaty Organization' in organization:
        return
    else:
        
        try:
            notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            if 'Amended' in notice_type:
                notice_data.notice_type = 16
            else:
                notice_data.notice_type = 4
        except Exception as e:
            logging.info("Exception in notice_type: {}".format(type(e).__name__))
            pass

        # Onsite Field -Title
        # Onsite Comment -None

        try:
            local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-dummy-notice-title').text
            if len(local_title)>=5:
                notice_data.local_title = local_title
                notice_data.notice_title = notice_data.local_title
            else:
                return
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Open/amendment date
        # Onsite Comment -None

        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
            publish_date = re.findall('\d{4}/\d+/\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        # Onsite Field -Category
        # Onsite Comment -None
  
        try:
            notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            if 'Goods' in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'
            elif 'Services' in notice_contract_type:
                notice_data.notice_contract_type = 'Service'
            elif 'Construction' in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
            elif 'Services related to goods' in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'
            else:
                pass
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)>a').get_attribute("href")                     
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            notice_data.notice_url = url

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.dialog-off-canvas-main-canvas > main').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, '#edit-group-description > div >div.field.field').text
            notice_data.notice_summary_english=notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation number")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"duration")]//following::div[1]').text
            contract_duration1 = re.findall('\d+ \w+[(\w)]+',contract_duration)
            for item in contract_duration1:
                notice_data.contract_duration = item
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        try:
            Contact_info = page_details.find_element(By.CSS_SELECTOR, 'a#edit-group-contact-information-id').get_attribute("href")                     
            fn.load_page(page_details1,Contact_info,80)
        except:
            pass
        
        try:
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#wb-cont__content > div.tender-notice.full.clearfix > div').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        
        try:              
            customer_details_data = customer_details()
            
            try: 
                customer_details_data.org_name = page_details1.find_element(By.XPATH, '(//*[contains(text(),"Organization")]//following::dd[1])[2]').text 
            except:
                try:
                    customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Organization")]//following::dd[1]').text 
                except:
                    customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-tender-organization').text

    # Onsite Field -Click on Contact Information for this detail
    # Onsite Comment -ref. url-"https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/ns2023-19cbvrce"

            
            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Buying organization(s)")]//following::div[6]').text.split('Address')[1].strip()
            except:
                try:
                    customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::dd[1]').text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

    # Onsite Field -Click on Contact Information for this detail
    # Onsite Comment -ref. url-"https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/ns2023-19cbvrce"

            try:
                customer_details_data.contact_person = page_details1.find_element(By.XPATH, '//*[contains(text(),"Contracting authority")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
    # Onsite Field -Click on Contact Information for this detail
    # Onsite Comment -ref. url -"https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/ssc-23-00023193t"

            try:
                customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
    # Onsite Field -Click on Contact Information for this detail
    # Onsite Comment -ref. url-"https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/ns2023-19cbvrce"

            try:
                customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::dd[1]').text
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
        
        try:
            notice_deadline = page_details1.find_element(By.XPATH, '''//*[contains(text(),"Closing date and time")]/span''').text
            notice_deadline = re.findall('\d{4}/\d+/\d+\n\d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y/%m/%d\n%H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Click on "bidding detail" for this detail "attachments are just present in Amendment"
    # Onsite Comment -ref. no- "https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/ssc-23-00023193t"
        try:
            bidding_details = page_details.find_element(By.CSS_SELECTOR, 'a#edit-group-bidding-details-id').get_attribute("href")                     
            fn.load_page(page_details2,bidding_details,80)
        except:
            pass
        
        try:
            notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#wb-cont__content > div.tender-notice.full.clearfix > div > div > div > div').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass

        try:              
            for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'div.dialog-off-canvas-main-canvas > main td.views-field.views-field-field-document-link a'):
                attachments_data = attachments()
            # Onsite Field -Click on "bidding detail" for this detail
            # Onsite Comment -ref. no- "https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/ssc-23-00023193t"
                attachments_data.file_name = single_record.text
                attachments_data.file_type = single_record.text.split('.')[-1]
                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome( options=options)
page_details = webdriver.Chrome(options=options)
page_details1 = webdriver.Chrome( options=options)
page_details2 = webdriver.Chrome( options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://canadabuys.canada.ca/en/tender-opportunities?status%5B0%5D=1920&status%5B1%5D=87#msg'] 
    for url in urls:
        fn.load_page_expect_xpath(page_main, url, '//*[@id="t"]/div/div/div[2]/div/div/table/tbody/tr', 100)
        logging.info('----------------------------------')
        logging.info(url)
        
        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'select#edit-items-per-page--4'))
        pp_btn.select_by_index(2)
        time.sleep(5)
        
        for i in range(10):
            button = page_main.find_element(By.XPATH,'//*[@id="t"]/div/div/div[3]/p/a').click()
            time.sleep(5)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="t"]/div/div/div[2]/div/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="t"]/div/div/div[2]/div/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details2.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
