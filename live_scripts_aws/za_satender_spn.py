from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_satender_spn"
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

#Note:Open site and go to "ADVANCED SEARCH" select "Sector=any" and "Region=any" and "Issuer=Blank" than click "Go" button

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_satender_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'za_satender_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'ZAR'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.views-field.views-field-field-extended-title').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Closing Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td.views-field.views-field-field-closing-date").text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.views-field.views-field-field-tender-reference').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.views-field.views-field-field-extended-title > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div.content-area').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Issue Date:
    # Onsite Comment -None  

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Issue Date:")]//following::span[1]').text
        publish_date = re.findall('\w+ \d+, \d{4} - \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Meeting Date:
    # Onsite Comment -None 

    try:
        pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Meeting Date:")]//following::span[1]').text
        pre_bid_meeting_date = re.findall('\w+ \d+, \d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass

    # Onsite Field -Sector:
    # Onsite Comment -Note:Splite category after this "Sector:" keyword
    
    try:
        category1 = ''
        data = page_details.find_element(By.XPATH, '//*[contains(text(),"Sector:")]//following::div[1]')
        for category in data.find_elements(By.CSS_SELECTOR, ' div.field.field-name-field-sector.field-type-taxonomy-term-reference.field-label-above > div.field-items > div'):
            category_data = category.text
            category1 += category_data
            category1 += ','
            cpv_codes = fn.procedure_mapping("assets/za_satender_spn_cpv.csv",category_data)
            cpv_codes = re.findall('\d{8}',cpv_codes)
            for cpv_code in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        notice_data.category = category1.rstrip(',')
    except Exception as e:
            logging.info("Exception in cpv: {}".format(type(e).__name__))
            pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Issuer:
        # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Issuer:")]//following::div[1]').text
        
        # Onsite Field -Region:
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Region:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact Person
        # Onsite Comment -Note=Splite contact parson after this "Contact Person" keyword

        try:
            contact_person = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div.content-area').text
            if "Contact Person:" in contact_person:
                customer_details_data.contact_person = contact_person.split("Contact Person:")[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Email:
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::a[1]').text
        except:
            try:
                org_email = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div.content-area').text
                if "E-mails: " in org_email:
                    customer_details_data.org_email = org_email.split("E-mails: ")[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telephone number:
        # Onsite Comment -Note=Splite org_phone after this "Telephone number:" keyword

        try:
            org_phone = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div.content-area').text
            if "Tel:" in org_phone:
                customer_details_data.org_phone = org_phone.split('Tel:')[1].split('\n')[0].strip()
            elif 'Telephone number:' in org_phone:
                customer_details_data.org_phone = org_phone.split('Telephone number: ')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -FAX Number
        # Onsite Comment -Note:Splite org_fax after this "FAX Number:" keyword

        try:
            org_fax = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div.content-area').text
            if "Fax: " in org_fax:
                org_fax1 = org_fax.split('Fax:')[1].split('\n')[0].strip()
                if "N/A" in org_fax1:
                    pass
                else:
                    customer_details_data.org_fax = org_fax1
                    
            elif 'FAX Number: ' in org_fax:
                org_fax1 =org_fax.split('FAX Number: ')[1].split('\n')[0].strip()
                if "N/A" in org_fax1:
                    pass
                else:
                    customer_details_data.org_fax = org_fax1
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"see:")]//following::a'):
            
        # Onsite Field -see: 
        # Onsite Comment -Note:Split only file_name , for ex : "TENDER NOTICE AND INVITATION TO BID - FBC T8-2023.pdf",here take only "TENDER NOTICE AND INVITATION TO BID - FBC T8-2023". Don't take file extentions

            file_name = single_record.text
            if "pdf" in file_name or 'docx' in file_name or 'zip' in file_name or 'xlsx' in file_name:
                attachments_data = attachments()
                attachments_data.file_name = file_name
                
                attachments_data.external_url = single_record.get_attribute('href')
                
                try:
                    attachments_data.file_type = attachments_data.file_name.split(".")[-1].strip()
                except:
                    pass
        
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
    urls = ["https://www.sa-tenders.co.za/?page='+str(page_no)+"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            click_go = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="edit-submit-advanced-search-block"]')))
            page_main.execute_script("arguments[0].click();",click_go)
        except:
            pass
        
        time.sleep(3)
        for page_no in range(2,28):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="page"]//div/div/div/div/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page"]//div/div/div/div/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page"]//div/div/div/div/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="page"]//div/div/div/div/div/table/tbody/tr'),page_check))
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