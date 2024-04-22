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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "rs_jnportal_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# first Go to URL : "https://jnportal.ujn.gov.rs/odluke-o-dodeli-ugovora"

# click on  ( selector : "div.dx-dropdowneditor-input-wrapper.dx-selectbox-container div.dx-button-normal.dx-button-mode-contained.dx-widget.dx-dropdowneditor-button > div > div"   )   dropdown button

# select "He" for filter

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'rs_jnportal_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'SR'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RS'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'RSD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Назив набавке
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#searchGridContainer div.dx-datagrid-rowsview  td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Објављено
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#searchGridContainer div.dx-datagrid-rowsview  td:nth-child(9) > font").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#searchGridContainer div.dx-datagrid-rowsview  td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#uiContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Процењена вредност
    # Onsite Comment -None

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Процењена вредност")]//following::td[1]/span').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Ставка плана на основу које је набавка покренута
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#planItemsAssociatedPanel > div'):
            cpvs_data = cpvs()
        # Onsite Field -ЦПВ
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer  tr.dx-row.dx-data-row td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = '"CPV"'
    
    # Onsite Field -ЦПВ
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer  tr.dx-row.dx-data-row td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Основни подаци о набавци
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderBasicInfoPanel > div > div'):
            customer_details_data = customer_details()
        # Onsite Field -Наручилац
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#searchGridContainer div.dx-datagrid-rowsview  td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'RS'
            customer_details_data.org_language = 'SR'
        # Onsite Field -Локација наручиоца
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),'Локација наручиоца')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Предмет / партије
# Onsite Comment -format 1 , contains multiple lots ,  ref_url : "https://jnportal.ujn.gov.rs/tender-eo/168027"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailLotsPanel > div'):
            lot_details_data = lot_details()
        # Onsite Field -Предмет / партије >>  Назив
        # Onsite Comment -format 1,

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#tenderDetailLotsContainer div.dx-scrollable table td.wrappedColumnMobile').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Предмет / партије >>  Процењена вредност
        # Onsite Comment -format 1,   if this field "Предмет / партије" have more than one lots then use following selkector "#tenderDetailLotsContainer tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(4)" , ref_url : "https://jnportal.ujn.gov.rs/tender-eo/168027"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, '#tenderDetailLotsContainer tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Одлуке о додели
        # Onsite Comment -format 1

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailAwardDecisionsPanel > div'):
                    award_details_data = award_details()
		
                    # Onsite Field -Одлуке о додели >>  Изабрани
                    # Onsite Comment -format 1, ref_url : "https://jnportal.ujn.gov.rs/tender-eo/168027"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, '#awardDecisionsContainer > div tbody > tr> td:nth-child(5)').text
			
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    
    
# Onsite Field -Предмет / партије
# Onsite Comment -format 2 , contains only 1 lot , ref_url : "https://jnportal.ujn.gov.rs/tender-eo/182683"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailLotsPanel > div'):
            lot_details_data = lot_details()
        # Onsite Field -Предмет / партије >>  Назив
        # Onsite Comment -format 2 , contains only 1 lot , ref_url : "https://jnportal.ujn.gov.rs/tender-eo/182683"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#tenderDetailLotsContainer div.dx-scrollable table td.wrappedColumnMobile').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Предмет / партије >> Процењена вредност
        # Onsite Comment -format 2 , contains only 1 lot , ref_url : "https://jnportal.ujn.gov.rs/tender-eo/182683"

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, '#tenderDetailLotsContainer tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Одлуке о додели
        # Onsite Comment -format 2 , contains only 1 lot , ref_url : "https://jnportal.ujn.gov.rs/tender-eo/182683"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailAwardDecisionsPanel > div'):
                    award_details_data = award_details()
		
                    # Onsite Field -Одлуке о додели
                    # Onsite Comment -format 2 , contains only 1 lot , ref_url : "https://jnportal.ujn.gov.rs/tender-eo/182683"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, '#awardDecisionsContainer > div tbody > tr> td:nth-child(4) > font').text
			
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#searchGridContainer > div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(1) > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ["https://jnportal.ujn.gov.rs/odluke-o-dodeli-ugovora"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="searchGridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchGridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchGridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="searchGridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr'),page_check))
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