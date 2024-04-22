from gec_common.gecclass import *
import logging
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
from deep_translator import GoogleTranslator
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_ocpdc_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_ocpdc_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'USD'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div').text.replace('-Cancelled','').strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > span').text
        notice_data.notice_title = GoogleTranslator(source='es', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

    try: 
        deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        deadline_date = re.findall('\d+/\d+/\d{4}',deadline)[0]
        deadline_time = re.findall('\d+:\d+ \w+',deadline)[0]
        notice_deadline = deadline_date + ' ' + deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div > span').text

    try:
        org_email = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in org_email: {}".format(type(e).__name__))
        pass

    try:
        org_phone = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > div:nth-child(3) > span').text
    except Exception as e:
        logging.info("Exception in org_phone: {}".format(type(e).__name__))
        pass

    try:
        contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in contact_person: {}".format(type(e).__name__))
        pass   
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass


    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > span').click()
        time.sleep(3)
        notice_data.notice_url = page_main.current_url
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    try: 
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Open Date")]//following::div[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_data.local_description = page_main.find_element(By.XPATH,'''//*[contains(text(),"Synopsis")]//following::div[1]''').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
    try:
        class_codes_at_source = ''
        codes_at_source = page_main.find_element(By.XPATH, '//*[contains(text(),"NIGP Code")]//following::span[1]').text
        cpv_regex = re.compile(r'\d{7}')
        code_list = cpv_regex.findall(codes_at_source)
        for codes in code_list:
            class_codes_at_source += codes
            class_codes_at_source += ','
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in class_codes_at_source: {}".format(type(e).__name__)) 
        pass

    try:
        class_title_at_source = '' 
        single_record = page_main.find_element(By.XPATH, '//*[contains(text(),"NIGP Code")]//following::span[1]').text.split('\n')
        for record in single_record:
            titles_at_source = re.split("\d{7}.", record)[1]
            class_title_at_source += titles_at_source
            class_title_at_source +=','
        notice_data.class_title_at_source = class_title_at_source.rstrip(',') 
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass


    try:
        notice_data.notice_text += page_main.find_element(By.XPATH,'/html/body/app-root/div[2]/div/app-solicitations/app-solicitation-details').get_attribute('outerHTML')
    except:
        pass

    try:
        customer_details_data = customer_details()  
        customer_details_data.org_name = org_name
        try:
            customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass 
            
        try:
            customer_details_data.org_email = org_email
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
            
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        customer_details_data = customer_details()  
        customer_details_data.org_name = org_name
        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contracting Officer")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass 
            
        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Contracting Officer")]//following::div[2]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Contracting Officer")]//following::div[3]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
            
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Work Site Location")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
            
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:  
        for single_record in page_main.find_elements(By.XPATH,'//*[contains(text(),"Attachments")]//following::div/a'):
            if 'txt' in single_record.text:
                pass
            else:
                attachments_data = attachments()
                attachments_data.external_url = single_record.get_attribute('href')
    
                external_url = single_record.click()
                time.sleep(3)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                
                attachments_data.file_name = single_record.text
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.activatable'))).text
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://contracts.ocp.dc.gov/solicitations/search"] 
    for url in urls:
        fn.load_page(page_main, url, 120)
        logging.info('----------------------------------')
        logging.info(url)                                                                                                             
        try:   
            search_solitations_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//*[@class='btn btn-primary'][1])[1]")))
            page_main.execute_script("arguments[0].click();",search_solitations_click)
            time.sleep(3)
        except:
            pass

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.activatable'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.activatable')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.activatable')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li.pagination-next.page-item > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tr.activatable'),page_check))
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