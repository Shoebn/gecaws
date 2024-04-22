from gec_common.gecclass import *
import logging
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
import functions as fn
from functions import ET

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_findtenserv_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -click on "Procurement stage > Definitions > Pipeline > Update results" only for get records for pp
    notice_data.script_name = 'uk_findtenserv_pp'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UK'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'GBP'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 3
    
    # Onsite Field -Notice type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > dd').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Publication date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3) > dd").text
        publish_date = re.findall('\d+ \w+ \d{4}, \d+:\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y, %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Total value
    # Onsite Comment -None

    try:
        grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > dd').text
        grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Total value
    # Onsite Comment -None

    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-container > div.govuk-width-container > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Reference
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract type
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Service contract = services','Works = works',' Supply contract = supply ')

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract type")]//following::p[1]').text
        if "Services" in notice_data.notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Goods" in notice_data.notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Supply contract" in notice_data.notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Service contract" in notice_data.notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Works" in notice_data.notice_contract_type:
            notice_data.notice_contract_type = "Works"
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'
      
        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result > div:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -2. Buyer
        # Onsite Comment -take only address from the given selector

        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#main-container > div.govuk-width-container > main').text
            if "Contract is not suitable for" in customer_details_data.org_address:
                customer_details_data.org_address = customer_details_data.org_address.split("Contract is not suitable for")[1].split("Buyer")[1].split("Website")[0]
            elif "Contract is suitable for" in customer_details_data.org_address:
                customer_details_data.org_address = customer_details_data.org_address.split("Contract is suitable for")[1].split("Buyer")[1].split("Website")[0]
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Contract location
#         # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract location")]//following::ul[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact name:
        # Onsite Comment -split contact_person from the given selector

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact name:")]').text.split("Contact name:")[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Telephone
        # Onsite Comment -split org_phone from the given selector

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone:")]').text.split("Telephone:")[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Email:
#         # Onsite Comment -split org_email from the given selector

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email:")]').text.split("Email:")[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -NUTS code:
        # Onsite Comment -split customer_nuts from the given selector

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS code:")]').text.split("NUTS code:")[1]
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Website:
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Website:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'ul.govuk-list.govuk-list--bullet li'):
            cpvs_data = cpvs()
        # Onsite Field -Main category (CPV code)
        # Onsite Comment -take " Main category (CPV code)" and "Additional categories (CPV codes)" field data also (selector for additional cpv '//*[contains(text(),"Additional categories (CPV codes)")]//following::ul/li') and take numeric value from the given selector only for cpv_code
            cpvs_data.cpv_code = single_record.text.split(' -')[0].strip()
            cpvs_data.cpv_code = int(cpvs_data.cpv_code)
            cpvs_data.cpv_code = str(cpvs_data.cpv_code)
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        lot_details_data.lot_description = notice_data.notice_title
        lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
        lot_details_data.contract_type = notice_data.notice_contract_type
        
        # Onsite Field -Contract start date (estimated)
        # Onsite Comment -None

        try:
            contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract start date (estimated)")]//following::p[1]').text
            contract_start_date = re.findall('\d+ \w+ \d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contract end date (estimated)
        # Onsite Comment -None

        try:
            contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract end date (estimated)")]//following::p[1]').text
            contract_end_date = re.findall('\d+ \w+ \d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass

        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'ul.govuk-list.govuk-list--bullet li'):
                lot_cpvs_data = lot_cpvs()
                # Onsite Field -Main category (CPV code)
                # Onsite Comment -take " Main category (CPV code)" and "Additional categories (CPV codes)" field data also (selector for additional cpv '//*[contains(text(),"Additional categories (CPV codes)")]//following::ul/li') and take numeric value from the given selector only for cpv_code
                lot_cpvs_data.lot_cpv_code = single_record.text.split(' -')[0].strip()
                lot_cpvs_data.lot_cpv_code = int(lot_cpvs_data.lot_cpv_code)
                lot_cpvs_data.lot_cpv_code = str(lot_cpvs_data.lot_cpv_code)
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#view-notice-side-menu > div:nth-child(2) > ul > li '):
            attachments_data = attachments()
            attachments_data.file_name = 'Download'
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            # Onsite Field -Download
            # Onsite Comment -split file_type from the given selector
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split("version")[0]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ['https://www.find-tender.service.gov.uk/Search/Results?&page=1#dashboard_notices'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#stage\[1\]_label")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#stage\[2\]_label")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#stage\[3\]_label")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#adv_search_button")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        try:
            WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' #sort_label')))
        except:
            pass
            
        for page_no in range(2,4):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dashboard_notices"]/div[1]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="dashboard_notices"]/div[1]/div'),page_check))
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
    
