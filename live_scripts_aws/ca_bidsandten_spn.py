from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_bidsandten_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_bidsandten_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ca_bidsandten_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CAD'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.main_language = 'FR'
    
    # Onsite Field -Bid Name
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Published Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\w+ \d+, \d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%b %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\w+ \d+, \d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    # Onsite Field -View
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -View
    # Onsite Comment -None
    
      # Onsite Field -Description:
    # Onsite Comment -None

    try:
        notice_summary_english = page_details.find_element(By.XPATH, "//*[contains(text(),'Description:')]//following::td[1]").text
        if  len(notice_summary_english)<=1:
            notice_data.notice_summary_english = notice_data.notice_title
        else:
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Type:
    # Onsite Comment -None

    try:
        document_type_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Bid Type:')]//following::td[1]").text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description:')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Bid Number:')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'FR'
        customer_details_data.org_country = 'CA'
        # Onsite Field -Organization
        # Onsite Comment -None
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        
        # Onsite Field -Submission Address:
        # Onsite Comment -None

        try:
            org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Submission Address:')]//following::td[1]").text
            if "Online Submissions Only" in org_address:
                pass
            else:
                customer_details_data.org_address = org_address
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try: 
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, "td.x-grid3-col.x-grid3-cell.x-grid3-td-Email.x-grid3-cell-last ").text
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, "td.x-grid3-col.x-grid3-cell.x-grid3-td-Email").text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, "td.x-grid3-col.x-grid3-cell.x-grid3-td-FullName.x-grid3-cell-first").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        catg_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a#lnkCat")))
        page_details.execute_script("arguments[0].click();",catg_clk)
        category = ''
        class_title_at_source = ''
        for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Categories')]//following::li"):
            category += single_record.text.split("\n")[0]
            category += ','
        notice_data.category = category.rstrip(',')
        notice_data.class_title_at_source = notice_data.category
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Categories')]//following::li"):
            category = single_record.text.split("\n")[0]
            cpv_codes = fn.CPV_mapping("assets/ca_bidsandten_category.csv",category)
            for cpv_code1 in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv_code1
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#contenu > div').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://bidsandtenders.ca/suppliers/bid-opportunities/'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="hs-eu-confirmation-button"]')))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(3)
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#TenderName')))
        except:
            pass
        
        try:
            iframe = page_main.find_element(By.XPATH,'//*[@id="content"]/div[2]/div/div/div/div/iframe')
            page_main.switch_to.frame(iframe)
        except:
            pass

        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bidsTable"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bidsTable"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bidsTable"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," div:nth-child(3) > ul > li:nth-child(1) > a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="bidsTable"]/tbody/tr'),page_check))
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
