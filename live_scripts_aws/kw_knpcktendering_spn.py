from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "kw_knpcktendering_spn"
log_config.log(SCRIPT_NAME)
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
tender_no = 0
SCRIPT_NAME = "kw_knpcktendering_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'kw_knpcktendering_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'KW'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'KWD'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url  
    
    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        if 'null' not in document_type_description:
            notice_data.document_type_description = document_type_description
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        if 'Not specified' in notice_no or 'null' in notice_no:
            n_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.strip()
            notice_no = re.findall('\d{7}',n_no)[0] 
            notice_data.notice_no = notice_no
        else:
            notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no1: {}".format(type(e).__name__))
        pass
            
            
    try:
        if notice_data.notice_no == None:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('-')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no2: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.earnest_money_deposit = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "Kuwait National Petroleum Company"
        customer_details_data.org_parent_id = 7594965
        customer_details_data.org_country = 'KW'
        customer_details_data.org_language = 'EN'
            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute("href")
    except:
        pass
    
    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#cntDetail').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        try:
            notice_data.project_name = page_details.find_element(By.XPATH, '(//*[contains(text(),"Project Title")]//following::tr[1]/td[2])[1]').text
        except Exception as e:
            logging.info("Exception in project_name: {}".format(type(e).__name__))
            pass
        
        try:
            p_date = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Publication- Date")]//following::tr[1]/td)[1]''').text
            p_time = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Publication- Time")]//following::tr[1]/td[2])[1]''').text
            publish_date = re.findall('\d+/\d+/\d{4}',p_date)[0]
            publish_time = re.findall('\d+:\d+:\d+',p_time)[0]
            published_date = publish_date + ' ' + publish_time
            notice_data.publish_date = datetime.strptime(published_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
            
        try:
            d_date = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Closing Date")]//following::tr[1]/td)[1]''').text
            d_time = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Closing Date")]//following::tr[1]/td[2])[1]''').text
            deadline_date = re.findall('\d+/\d+/\d{4}',d_date)[0]
            deadline_time = re.findall('\d+:\d+',d_time)[0]
            notice_deadline = deadline_date + ' ' + deadline_time
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
        

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Description")]//following::tr[1])[1]').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:              
            attachments_data = attachments()

            attachments_data.file_name = 'Tender documents'
            
            external_url = page_details.find_element(By.XPATH,'/html/body/section[1]/div[3]/main/div/input[5]')
            page_details.execute_script("arguments[0].click();",external_url)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)

        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://ktendering.com.kw/esop/kuw-kpc-host/public/report/runningTenders.jsp?ipc=1"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#detail_header > table > tbody > tr:nth-child(2)'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#detail_header > table > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#detail_header > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr[2]'),page_check))
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
