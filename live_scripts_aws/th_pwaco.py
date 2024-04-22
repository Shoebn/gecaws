from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "th_pwaco"
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
from selenium import webdriver
from gec_common import functions as fn


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "th_pwaco"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'th_pwaco'
    
    notice_data.main_language = 'TH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)
    

    notice_data.currency = 'THB'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,20)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
  
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"วันที่ปรับปรุงข้อมูล :")]//following::div[1]').text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"วงเงินงบประมาณ :")]//following::div[1]').text.replace(",",'').split('.')[0]
        notice_data.grossbudgetlc = int(notice_data.grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"วงเงินงบประมาณ :")]//following::div[1]').text.replace(",",'').split('.')[0]
        notice_data.est_amount = int(notice_data.est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    

    try:              
        customer_details_data = customer_details()
    
        try:
            customer_details_data.org_name = org_name
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
    
        customer_details_data.org_country = 'TH'
        customer_details_data.org_language = 'TH'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number =  1
        notice_data.is_lot_default = True

        try:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass
    

        try:
            lot_details_data.lot_description = notice_data.notice_title
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
    

        try:
            lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"วงเงินงบประมาณ :")]//following::div[1]').text.replace(",",'').split('.')[0]
            lot_details_data.lot_grossbudget_lc = int(lot_details_data.lot_grossbudget_lc)
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
    
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        for filename in page_details.find_elements(By.CSS_SELECTOR, 'div.panel-body > table ul > li'):
            attachments_data = attachments()
            
            try:
                attachments_data.file_name = filename.text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_size = attachments_data.file_name.split()
                attachments_data.file_size = attachments_data.file_size[-1]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(attachments_data.file_name)
                file_name_split = attachments_data.file_name.split()
                file_name_split_point = file_name_split[-1]
                attachments_data.file_name = attachments_data.file_name.split(file_name_split_point)[0]
            except:
                pass


            attachments_data.external_url = filename.find_element(By.CSS_SELECTOR,'a').get_attribute('href')

            try:
                attachments_data.file_type = attachments_data.external_url.split(').')[1]
            except:
                pass

        
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

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://eprocurement.pwa.co.th/e-bidding'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div[2]/div[2]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[2]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[2]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/div[2]/div[2]/div/table/tbody/tr'),page_check))
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
    
