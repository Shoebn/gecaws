from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tz_nestgo_spn"
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
import gec_common.th_Doc_Download as Doc_Download
from selenium.webdriver.support.ui import Select

# Note:Open the site than click on "div.hidden.md\:flex.leading-3 > div:nth-child(2)" this dropdown than click on "All Tenders" than grab the data
# Note:Open the site than grab all data than click "Advanced Search" than click "process Stage" dropdown than select "Tendering","Pre Qualification","Framework" than grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tz_nestgo_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'tz_nestgo_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TZ'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'TZS'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > a > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.sm\:flex.sm\:space-x-4.items-center > div:nth-child(1) > div:nth-child(2)").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass 
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -Note:Grab also time

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.sm\:flex.sm\:space-x-4.items-center > div:nth-child(2) > div:nth-child(2)").text
        notice_deadline = re.findall('\d+ \w+ \d{4} \d+:\d+ [apAP][mM]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.sm\:flex.sm\:space-x-4.items-center > div:nth-child(3) > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.flex.items-center.space-x-2 > div.flex.text-\[10px\].items-center > div').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -None
    # Onsite Comment -Note:If in this selector "div.flex.items-center.space-x-2 > div.flex.text-\[10px\].items-center > div" have "Pre Qualification" this keyword than take notice_type 6
    
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.flex.items-center.space-x-2 > div.flex.text-\[10px\].items-center > div').text
        if "Pre Qualification" in notice_type:
            notice_data.notice_type = 6
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.mt-2 > div').text
        customer_details_data.org_country = 'TZ'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -Note:Click on "View Details " button than grab the data
        
    try:
        notice_url_click = WebDriverWait(tender_html_element,150).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.flex.mt-\[20px\].sm\:mt-auto.space-x-2.text-\[11px\].ng-star-inserted > button')))
        page_main.execute_script("arguments[0].click();",notice_url_click)
        time.sleep(5)
        notice_data.notice_url = url
        logging.info(notice_data.notice_url)

    
        # Onsite Field -None
        # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.-mt-80.mb-20 > div.web-container.\!p-0.bg-white.rounded-xl.overflow-hidden.shadow-lg > div').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        # Onsite Field -Tender Category
        # Onsite Comment -Note:Repleace following keywords with given keywords("Non Consultancy=Non consultancy","Goods=Supply","Works=Works","Consultancy=Consultancy")


        # Onsite Field -Tender Category
        # Onsite Comment -None
        try:
            notice_data.contract_type_actual = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Category")]//following::div[1]').text
            if "Non Consultancy" in notice_data.contract_type_actual:
                notice_data.notice_contract_type="Non Consultancy"
            elif "Goods" in notice_data.contract_type_actual:
                notice_data.notice_contract_type='Supply'
            elif "Consultancy" in notice_data.contract_type_actual:
                notice_data.notice_contract_type='Consultancy'
            elif "Works" in notice_data.contract_type_actual:
                notice_data.notice_contract_type='Works'
        except Exception as e:
            logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
            pass    

        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

    # To download attachments its taking to much time,so increase the sleep time. 
        
        try:              
            attachments_data = attachments()
            # Onsite Field -None
            # Onsite Comment -Note:Don't take file extention

            attachments_data.file_name = "View Tender Document"

            # Onsite Field -None
            # Onsite Comment -Note:Take only file extention

            attachments_data.file_type = "pdf"

            external_url_click = WebDriverWait(page_main, 150).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.flex.flex-rows.w-full.items-right.my-4.ng-star-inserted > div > button')))
            page_main.execute_script("arguments[0].click();",external_url_click)
            time.sleep(20)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url= (str(file_dwn[0]))
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        try:
            close = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'span.close-modal')))
            page_main.execute_script("arguments[0].click();",close)
            time.sleep(2)
        except:
            pass

        page_main.execute_script("window.history.go(-1)")
        
        WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div')))
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
page_main = Doc_Download.page_details
page_main.maximize_window() 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://nest.go.tz/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)

        try:   
            status_click_2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/div/app-home/div/div[1]/div/web-nav-bar/div[1]/div[1]/div[1]/mat-icon')))
            page_main.execute_script("arguments[0].click();",status_click_2)
            time.sleep(5)
        except:
            pass
        
        try:
            status_click_2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-menu-panel-3"]/div/a[1]')))
            page_main.execute_script("arguments[0].click();",status_click_2)
            time.sleep(2)
        except:
            pass
        

        for page_no in range(1,10):#10
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tender_search_container"]/div/div[2]/div/parallax-container/div[2]/div[2]/div/app-advanced-tender-search/div[2]/web-page-paginator/div/div[2]/div/button[2]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tender-list-container"]/div[3]/app-advanced-tender-search-tender-item/div/div'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
