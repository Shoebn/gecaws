#"click on cancelled > click on bidder list on right hand side > enter "select Department" as all > enter Captcha Code > Search "	

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
from gec_common import functions as fn
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.alert import Alert

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_sppprajast_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'INR'
    
    notice_data.procurement_method = 2
  
    notice_data.notice_type = 7
    
    notice_data.script_name = 'in_sppprajast_ca'
    
    notice_data.notice_url = url
    
    # Onsite Field -Remark
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if len(notice_data.local_title) <= 5:
            return
        notice_data.notice_title = notice_data.local_title 
        notice_data.local_description = notice_data.local_title
        notice_data.notice_summary_english = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.sorting_1").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'IN'

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

        try:
            customer_details_data.contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1

        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        lot_details_data.lot_description = lot_details_data.lot_title

        try:
            award_details_data = award_details()

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('[')[0].strip()
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        if lot_details_data.award_details !=[]:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        attachments_data = attachments()

        file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text.split(']')[0].replace('[','').strip()
        attachments_data.file_name=GoogleTranslator(source='auto', target='en').translate(file_name)
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')
        if 'pdf' in attachments_data.external_url:
            attachments_data.file_type = 'pdf'

        try:
            attachments_data.file_size = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text.split(']')[1].strip()
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
options = webdriver.ChromeOptions()
options.add_extension("Rumola-bypass-CAPTCHA.crx")
page_main = webdriver.Chrome(options=options)
page_main.maximize_window()
time.sleep(2)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://sppp.rajasthan.gov.in/bidderlist.php"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            cancelled = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Cancelled')))
            page_main.execute_script("arguments[0].click();",cancelled)
        except:
            pass
        time.sleep(5)
        try:
            bidder_list = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Bidder List')))
            page_main.execute_script("arguments[0].click();",bidder_list)
        except:
            pass
        time.sleep(3)
        try:
            pp_btn = Select(page_main.find_element(By.XPATH,'//*[@id="ddldepartment"]'))
            pp_btn.select_by_value('0')
            time.sleep(5)
        except:
            pass
        
        alert = Alert(page_main) 
        alert.accept() 

        while True:
            time.sleep(15) #######to give time to extention to solve captcha
            search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="btnsearch"]')))
            page_main.execute_script("arguments[0].click();",search)
            
            try:
                table_row = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="examplesearch"]/tbody/tr[1]'))).text
                break
            except:
                try:
                    elementRefresh = page_main.find_element(By.XPATH, '//*[@id="tblformdesign"]/tbody/tr[3]/td/table/tbody/tr[6]/td[2]/a')  
                    elementRefresh.click()
                    input1 = page_main.find_element(By.XPATH,'//*[@id="txtcaptcha"]').clear()
                except:
                    pass
        time.sleep(5)

        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#examplesearch > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#examplesearch > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#examplesearch > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#examplesearch > tbody > tr'),page_check))
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
    
