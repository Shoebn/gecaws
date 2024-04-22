from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "rs_jnportal_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

import pyautogui

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "rs_jnportal_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
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
    
    notice_data.script_name = 'rs_jnportal_ca'
    
    notice_data.main_language = 'SR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RS'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.procurement_method = 2
    
    notice_data.currency = 'RSD'
    
    notice_data.notice_type = 7
    
    notice_data.class_at_source = "CPV"
    
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
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

      
    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(1) > a'):
            attachments_data = attachments()
            attachments_data.file_name = "Tender Documents"
       
            attachments_data.external_url = single_record.get_attribute('href')
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        notice_data.notice_no = notice_data.notice_url.split("eo/")[1].strip()
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#uiContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Референтни број")]//following::td[1]/span').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Процењена вредност
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Процењена вредност")]//following::td[1]/span').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        est_amount =est_amount.replace('.','')
        notice_data.est_amount = float(est_amount.replace(',','.').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Ставка плана на основу које је набавка покренута
# Onsite Comment -None

    try:              
        cpvs_data = cpvs()
        # Onsite Field -ЦПВ
        # Onsite Comment -None

        cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer  tr.dx-row.dx-data-row td:nth-child(5)').text.split("-")[0].strip()

        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -ЦПВ
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer  tr.dx-row.dx-data-row td:nth-child(5)').text.split("-")[0].strip()
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Основни подаци о набавци
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'RS'
        customer_details_data.org_language = 'SR'
        # Onsite Field -Наручилац
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#searchGridContainer div.dx-datagrid-rowsview  td:nth-child(3)').text
        # Onsite Field -Локација наручиоца
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, "//*[contains(text(),'Локација наручиоца')]//following::td[1]").text
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
        range_lot=page_details.find_element(By.CSS_SELECTOR, '#uiContent').text
    except:
        pass
    
    try:
        if "За партију" in range_lot:
            lot_number=1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#awardDecisionsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap > div > table > tbody > tr')[:-1]:
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number
                lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
                try:
                    award_details_data = award_details()

                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except:
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
        else:
            lot_number=1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#awardDecisionsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap > div > table > tbody > tr')[:-1]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual

                lot_details_data.lot_title = notice_data.local_title 
                notice_data.is_lot_default = True
                lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                 # Onsite Field -Одлуке о додели
        # Onsite Comment -format 1
                try:
                    award_details_data = award_details()

                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except:
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

page_main = fn.init_chrome_driver(arguments)
page_main.maximize_window()
page_details = fn.init_chrome_driver(arguments)
page_details.maximize_window()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://jnportal.ujn.gov.rs/odluke-o-dodeli-ugovora"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        time.sleep(5)
        logging.info('----------------------------------')
        logging.info(url)
        
        for i in range(0,2):
            with pyautogui.hold('ctrl'):
                pyautogui.press('-')
        
        drop_down = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="uiMainHeader"]/nav/a')))
        page_main.execute_script("arguments[0].click();",drop_down)
        time.sleep(5)
        
        drop_down = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="searchGridContainer"]/div/div[5]/div/table/tbody/tr[2]/td[11]/div/div/div/div/div/div[2]')))
        page_main.execute_script("arguments[0].click();",drop_down)
        time.sleep(5)
        
        click_he = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//div[@class="dx-item-content dx-list-item-content"])[3]')))
        page_main.execute_script("arguments[0].click();",click_he)
        time.sleep(5)

        try:
            for page_no in range(1,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="searchGridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchGridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="searchGridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#searchGridContainer > div > div.dx-datagrid-pager.dx-pager > div.dx-pages > div.dx-navigate-button.dx-next-button")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="searchGridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
