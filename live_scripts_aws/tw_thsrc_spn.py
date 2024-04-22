from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tw_thsrc_spn"
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

from selenium.common.exceptions import StaleElementReferenceException


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tw_thsrc_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'tw_thsrc_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TW'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'TWD'
    notice_data.main_language = 'CN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    notice_data.local_title  = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass      

    try:     
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text        
        notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass  
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text  
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y/%m/%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass    

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        time.sleep
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")    
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"公告含稅預算")]//following::span[1]').text
        notice_data.grossbudgetlc = float(grossbudgetlc.split('TWD')[1].strip())
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass        
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'TAIWAN HIGH SPEED RAIL CORPORATION'
        customer_details_data.org_parent_id = 7583604
        try:
            customer_details_text = page_details.find_element(By.XPATH,'//*[contains(text(),"採購承辦人")]//following::span[1]').text  
            customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', customer_details_text)[0]
            customer_details_data.contact_person = customer_details_text.split('(')[0].strip()
        except:
            try:
                customer_details_text = page_details.find_element(By.XPATH,'//*[contains(text(),"標案聯絡人")]//following::span[1]').text 
                customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', customer_details_text)[0]
                customer_details_data.contact_person = customer_details_text.split('電話')[0]
            except:
                try:
                    customer_details_text = page_details.find_element(By.XPATH,'//*[contains(text(),"聯絡窗口/聯絡方式")]//following::span[1]').text  
                    
                    customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', customer_details_text)[0]

                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                    pass    
        try:
            org_phone = page_details.find_element(By.XPATH,'//*[contains(text(),"連絡電話")]//following::span[1]').text
            try:
                customer_details_data.org_phone = re.findall(r'\d{2}-\d{7}/\d{3}', org_phone)[0]
            except:
                try:
                    customer_details_data.org_phone = re.findall(r'\d{2}-\d{8}', org_phone)[0]
                except:
                    try:
                        customer_details_data.org_phone = re.findall(r'\(\d{2}\)\d{4}-\d{4}', org_phone)[0]
                    except:
                        customer_details_data.org_phone = org_phone.split('分機')[0]

        except:
            try:
                org_phone = page_details.find_element(By.XPATH,'//*[contains(text(),"標案聯絡人")]//following::span[1]').text  
                try:
                    customer_details_data.org_phone = re.findall(r'\d{2}-\d{7}/\d{3}', org_phone)[0]
                except:
                    try:
                        customer_details_data.org_phone = re.findall(r'\d{2}-\d{8}', org_phone)[0]
                    except:
                        try:
                            customer_details_data.org_phone = re.findall(r'\(\d{2}\)\d{4}-\d{4}', org_phone)[0]
                        except:
                            customer_details_data.org_phone = org_phone.split('電話')[1].split('分機')[0]
            except:
                try:
                    customer_details_data.org_phone = re.findall(r'\d{2}-\d{7}/\d{3}', customer_details_text)[0]
                except:
                    try:
                        customer_details_data.org_phone = re.findall(r'\d{2}-\d{8}', customer_details_text)[0]
                    except:
                        try:
                            customer_details_data.org_phone = re.findall(r'\(\d{2}\)\d{4}-\d{4}', customer_details_text)[0]
                        except Exception as e:
                            logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                            pass    

        customer_details_data.org_country = 'TW'
        customer_details_data.org_language = 'CN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass       
       
    for single_record in page_details.find_elements(By.XPATH,'//*[@class="btn-group"]/button'):
        attachments_data = attachments()
        try:
            attachments_data.file_type = single_record.text.split('.')[-1].strip()
        except:
            pass
        attachments_data.file_name = single_record.text.split(attachments_data.file_type)[0].strip()
        external_url = single_record.get_attribute("onclick")
        only_num = external_url.split('\x3d')[-1].split("';")[0].strip()
        only_num_of_num = only_num.split('x3d')[-1].strip()
        attachments_data.external_url = "https://pms.thsrc.com.tw/web/epms/home?p_p_id=THSRCAnnouncement_WAR_THSRCPMSportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=serveDownloadSR04026&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_pos=1&p_p_col_count=2&_THSRCAnnouncement_WAR_THSRCPMSportlet_VRS1=002&_THSRCAnnouncement_WAR_THSRCPMSportlet_VRS1=002&_THSRCAnnouncement_WAR_THSRCPMSportlet_companyId=20155&_THSRCAnnouncement_WAR_THSRCPMSportlet_ADDN=PCDL-24-0124&_THSRCAnnouncement_WAR_THSRCPMSportlet_ADDN=PCDL-24-0124&_THSRCAnnouncement_WAR_THSRCPMSportlet_UKID=1&_THSRCAnnouncement_WAR_THSRCPMSportlet_UKID=1&_THSRCAnnouncement_WAR_THSRCPMSportlet_VERT=000&_THSRCAnnouncement_WAR_THSRCPMSportlet_CO=20155&_THSRCAnnouncement_WAR_THSRCPMSportlet_CO=20155&_THSRCAnnouncement_WAR_THSRCPMSportlet_ATSQ=0&_THSRCAnnouncement_WAR_THSRCPMSportlet_fileId="+only_num_of_num        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://pms.thsrc.com.tw"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr')))[records]   
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"下一個 ")]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'table > tbody > tr'),page_check))   
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
