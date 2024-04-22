from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uk_eusupply_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_eusupply_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
 
    notice_data.currency = 'EUR'
   
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 7
  
    notice_data.script_name = 'uk_eusupply_ca'

    try:
        performance_country_data = performance_country()
        p_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text.strip()
        performance_country_data.performance_country = fn.procedure_mapping("assets/uk_eusupply_ca_countrycode.csv",p_country)
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:
        performance_country_data.performance_country = 'GB'
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
 
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)>a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ctm-content-container > div > div').get_attribute("outerHTML")
        if "RFT details" in notice_data.notice_text: 
            rft_url = page_details.find_element(By.CSS_SELECTOR, 'a#showTenderDetails').get_attribute("href")                     
            fn.load_page(page_details,rft_url,80)
        elif "View RFT" in notice_data.notice_text:
            rft_url1 = page_details.find_element(By.XPATH, '//*[contains(text(),"View RFT")]//parent::a').get_attribute("href")                     
            fn.load_page(page_details,rft_url1,80)
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of dispatch")]//following::tr').text
        dispatch_date = re.findall('\d+/\d+/\d{4} \d+:\d+',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="tenderInfoSection"]/div[1]/div[1]/p/span'):
            cpvs_data = cpvs()
            cpv_code = single_record.text.split("-")[0]
            cpvs_data.cpv_code = re.sub("[^\d]","",cpv_code)
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#notices-table > tbody > tr > td:nth-child(1)'):
                if 'http' in single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href'):
                    attachments_data = attachments()
                # Onsite Field -Additional information:--- ref url for country (France, Sweeden, Netherland)----"https://eu.eu-supply.com/ctm/Supplier/PublicPurchase/373401/0/0?returnUrl=ctm/Supplier/publictenders&b="
                # Onsite Comment -from detail page click on "RFT detail button" > page_detail 1 will appear select data from this page
                    attachments_data.file_name = single_record.text
                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Packages")]//following::div[1]'):
            lot_details_data = lot_details()  
            lot_details_data.lot_number = lot_number
            try:
                lot_title = single_record.find_element(By.XPATH, '//*[contains(text(),"LOT")]//following::div[38]')[:-1].text
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
            except Exception as e:
                lot_details_data.lot_title =notice_data.notice_title
                notice_data.is_lot_default = True
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
            try:
                lot_details_data.lot_description = lot_details_data.lot_title
            except Exception as e:
                lot_details_data.lot_description=notice_data.notice_title
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            try:
                award_details_data = award_details()
                award_details_data.bidder_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Awarded supplier:")]//following::p[1]').text.split(",")[0]
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            
            try:
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = cpvs_data.cpv_code
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
                
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        # Onsite Field -Countries
        # Onsite Comment -None

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contracting authority:-------ref url "https://eu.eu-supply.com/ctm/Supplier/PublicPurchase/371648/0/0?returnUrl=ctm/Supplier/publictenders&b=", "https://eu.eu-supply.com/ctm/Supplier/PublicPurchase/373401/0/0?returnUrl=ctm/Supplier/publictenders&b="
        # Onsite Comment -from detail page click on "RFT detail button" > page_detail 1 will appear select data from this page

        try:
            org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Contracting authority:")]//following::p[1]').text
            if "View profile" in org_address:
                rft_url = page_details.find_element(By.XPATH, '//*[contains(text(),"View profile")]//parent::a').get_attribute("href")                     
                fn.load_page(page_details,rft_url,80)
                if "View profile" in org_address:
                    customer_details_data.org_address = org_address.split("View profile")[0]
                else:
                    customer_details_data.org_address = org_address
                click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a#cmlightClose")))
                page_details.execute_script("arguments[0].click();",click)
                time.sleep(2)
        except:
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Office:")]//following::p[1]').text
                click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a#cmlightClose")))
                page_details.execute_script("arguments[0].click();",click)
                time.sleep(2)
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        
        
        
         # Onsite Field -Contact:-------ref url "https://eu.eu-supply.com/ctm/Supplier/PublicPurchase/371648/0/0?returnUrl=ctm/Supplier/publictenders&b=", "https://eu.eu-supply.com/ctm/Supplier/PublicPurchase/373401/0/0?returnUrl=ctm/Supplier/publictenders&b="
        # Onsite Comment -from detail page click on "RFT detail button" > page_detail 1 will appear select data from this page
        
        # Onsite Field -Contact:-------ref url -ref url "https://eu.eu-supply.com/app/rfq/rwlproposal_s.asp?PID=371913","https://eu.eu-supply.com/app/rfq/rwlproposal_s.asp?PID=371854"
        # Onsite Comment -from page_detail1 click on > My Response > View RFT
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, ' div.row-fluid > div:nth-child(2) > div:nth-child(2) > div:nth-child(2)').text
        except:
            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.span3 > p:nth-child(4)').text.split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contracting authority:-------ref url ""https://eu.eu-supply.com/app/rfq/rwlproposal_s.asp?PID=371913","https://eu.eu-supply.com/app/rfq/rwlproposal_s.asp?PID=371854""
        # Onsite Comment -from page_detail click on > My Response > View RFT > page_detail1


        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(3) > a').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(4) > address > abbr').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = performance_country_data.performance_country
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments) 
 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://eu.eu-supply.com/login.asp?B='] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        
        page_main.find_element(By.XPATH,'//*[@id="username"]').send_keys('akanksha3')
        page_main.find_element(By.XPATH,'//*[@id="frmLogin"]/fieldset/input[2]').send_keys('ak1234567')
        page_main.find_element(By.XPATH,'//*[@id="submitBtn"]').click()
        time.sleep(5)
        
        
        url = 'https://eu.eu-supply.com/ctm/supplier/publictenders?B='
        logging.info('----------------------------------')
        logging.info(url)
        fn.load_page(page_main, url, 50)
        
        pp_btn = Select(page_main.find_element(By.XPATH,'//*[@id="SearchFilter_PublishType"]'))
        pp_btn.select_by_index(1)
        time.sleep(2)
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[@id='search']")))
            page_main.execute_script("arguments[0].click();",click)
        except:
            pass
        
        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="searchResultContainer"]/table/tbody/tr')))
        except:
            pass

        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="searchResultContainer"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchResultContainer"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchResultContainer"]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="searchResultContainer"]/table/tbody/tr'),page_check))
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
    
    
