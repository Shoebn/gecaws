from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gh_ghaneps_spn"
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
SCRIPT_NAME = "gh_ghaneps_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'gh_ghaneps_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'GHS'

    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -Note:If tender_html_element page in this "tr > td:nth-child(6)" selector have this keywod start with "National " than the  procurement_method will be "0" and start with "International" than the  procurement_method will be "1" other wise it will be "2"
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(6)').text
        if "National" in procurement_method:
            notice_data.procurement_method = 0
        elif "International" in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bids Submission Deadline
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(5)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Content > dl').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Tender Unique ID:
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Unique ID:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -APP Reference Number:
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"APP Reference Number:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description:")]//following::dd[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Procurement Type:
    # Onsite Comment -Note:Repleace following keywords with given keywords("Goods=Supply","Consulting Services=Consultancy","Disposals=Service","Technical Services=Service","Works=Works")
    
    # Onsite Field -Procurement Type:
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Type:")]//following::dd[1]').text
        if "Technical Services" in notice_data.contract_type_actual :
            notice_data.notice_contract_type ="Service"
        elif "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        elif "Consulting Services" in notice_data.contract_type_actual :
            notice_data.notice_contract_type = "Consultancy"
        elif "Works" in notice_data.contract_type_actual :
            notice_data.notice_contract_type = "Works"
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -UNSPSC Codes:
    # Onsite Comment -None
    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC Codes:")]//following::dd[1]').text.split("-")[0].strip()
        cpv_codes = fn.CPV_mapping("assets/gh_ghaneps_spn_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Publication/Invitation:
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of Publication/Invitation:")]//following::dd[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Bid Opening Date:
    # Onsite Comment -None

    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Opening Date:")]//following::dd[1]').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    

#Ref_url:https://www.ghaneps.gov.gh/epps/cft/prepareViewCfTWS.do?resourceId=712780
    try:              
        lot_number =1 
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Lot Name")]//following::dd[1]'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Lot Name
        # Onsite Comment -Note:Take both data

            lot_details_data.lot_title = single_record.text
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        custormer_url = page_details.find_element(By.CSS_SELECTOR, 'dd > a').get_attribute("href")                     
        fn.load_page(page_details1,custormer_url,80)
        logging.info(custormer_url)
    except Exception as e:
        logging.info("Exception in custormer_url: {}".format(type(e).__name__))
    
# Onsite Field -None
# Onsite Comment -Note:IN page_detail click "dd > a" and grab the data

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Organisation Name
    # Onsite Comment -None

        customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Organisation Name")]//following::dd[1]').text

    # Onsite Field -Address:
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Address:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Postal Code:
    # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Postal Code:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -City:
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"City:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Email:
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::dd[1]').text.strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Phone Number:
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Phone Number:")]//following::dd[1]').text.strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax:
    # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Website
    # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Website")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'GH'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -Note:Go to site and open tender then first click "Show Menu", than second click "Tender Documents", than third click "Tender Documents" than grab the data
    try:
        click2 = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a#ToggleSubmenu')))
        page_details.execute_script("arguments[0].click();",click2)
        time.sleep(5)
    except:
        pass
        
    try:
        url1 = page_details.find_element(By.XPATH, ' //*[@id="Submenu"]/div/ul[1]/li[2]/a').get_attribute("href")                     
        fn.load_page(page_details1,url1,80)
        logging.info(url1)
    except Exception as e:
        logging.info("Exception in url1: {}".format(type(e).__name__))
        
    try:
        attach_url = page_details1.find_element(By.CSS_SELECTOR, ' div.tabbertab > ul > li:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details1,attach_url,80)
        logging.info(attach_url)
    except Exception as e:
        logging.info("Exception in attach_url: {}".format(type(e).__name__))

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, ' tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -File
        # Onsite Comment -Note:Don't take file extention

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split(".")[0].strip()
        # Onsite Field -File
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split(".")[1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3) > a').get_attribute('href')
        
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
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ghaneps.gov.gh/epps/quickSearchAction.do?searchSelect=6&selectedItem=quickSearchAction.do%3FsearchSelect%3D6"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,3):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="T01"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[1]/div[5]/div[2]/div/div/div[2]/p[2]/button[3]")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="T01"]/tbody/tr'),page_check))
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
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
