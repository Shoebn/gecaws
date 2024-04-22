from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "th_egat"
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
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "th_egat"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
  
    notice_data.main_language = 'TH'
    
    notice_data.script_name = 'th_egat'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'THB'
   
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -Cancel the solicitation announcement / Change the solicitation notice / Change the announcement of bidders / Change the solicitation notice / Contract Termination Notice	= Addendam (notice type 16) Announcement of Bid Winners/Announcement of Selected Candidates	= Contract award (7) Other than above all grabb as spn 1(notice type =4)

    try:
        notice_type1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_type = GoogleTranslator(source='auto', target='en').translate(notice_type1)
        if "Cancel the solicitation announcement" in notice_type or "Change the solicitation notice" in notice_type or "Change the announcement of bidders" in notice_type or "Change the solicitation notice" in notice_type or 'Contract Termination Notice' in notice_type:
            notice_data.notice_type = 16
        elif "Announcement of Bid Winners/Announcement of Selected Candidates" in notice_type:
            notice_data.notice_type = 7
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -announcement type  --  ประเภทประกาศ
    # Onsite Comment -Cancel the solicitation announcement / Change the solicitation notice / Change the announcement of bidders / Change the solicitation notice / Contract Termination Notice	= Addendam (notice type 16) Announcement of Bid Winners/Announcement of Selected Candidates	= Contract award (7) Other than above all grabb as spn 1(notice type =4)

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'tr >  td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -details -- รายละเอียด
    # Onsite Comment -None

    try:
        notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'tr >  td:nth-child(5)').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -project number  -- เลขที่โครงการ
    # Onsite Comment -remove "a" tag just take number

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -details -- รายละเอียด
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(5)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Announcement start date  --  วันที่เริ่มประกาศ
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Announcement end date  --  วันสิ้นสุดประกาศ
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.find_element(By.XPATH, '//*[@id="dataDiv"]').get_attribute("outerHTML")                     
    except:
        pass 

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'TH'
        customer_details_data.org_language = 'TH'
#         # Onsite Field -sourcing agency -- หน่วยงานจัดหา
#         # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
  
   
    try:
        click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' tr > td.text-center > a'))).click()
        time.sleep(2)
    except:
        pass
    
    try:
        holder = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#fileUploadList > table > tbody > tr')))
    except:
        pass
    time.sleep(5)

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#fileUploadList > table > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -ชื่อเอกสาร -- document name
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, '#fileUploadList  td:nth-child(1)').text
            
        # Onsite Field -ดาวน์โหลด -- download
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' tr > td:nth-child(2) > a').get_attribute('href')
        
            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="fileUploadModal"]/div/div/div[3]/button'))).click()
        time.sleep(2)
    except:
        pass
    
    try:
        holder = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dataDiv"]/div[2]/table/tbody/tr')))
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://bidding.egat.co.th/procure/procure_list.php'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        scheight = .1

        while scheight < 9.9:
            page_main.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
            scheight += .01
        time.sleep(2)
        
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.modal-construction.modal-construction-display > div > div > svg"))).click()
            time.sleep(3)
        except:
            pass
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#qrcodeModal > div > div.qrcodeModal-content__header > button"))).click()
            time.sleep(3)
        except:
            pass
        
        time.sleep(5)

        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dataDiv"]/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dataDiv"]/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dataDiv"]/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="dataDiv"]/div[3]/div[2]/div/div[1]/div/div[2]/button[1]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="dataDiv"]/div[2]/table/tbody/tr'),page_check))
                    time.sleep(2)
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
