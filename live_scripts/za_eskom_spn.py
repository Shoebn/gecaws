from gec_common.gecclass import *
import logging
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
import gec_common.Doc_Download
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_eskom_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    
    notice_data = tender()

    notice_data.script_name = 'za_eskom_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'za'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'ZAR'
    notice_data.notice_type = 4
    notice_data.procurement_method = 2
    notice_data.notice_url =  url
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        notice_deadline = re.findall('\d+-\w+-\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    
    try: 
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        publish_date = re.findall('\d+-\w+-\d+ \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Sponsor's company
    # Onsite Comment -None   
        customer_details_data.org_name = "Eskom"
        customer_details_data.org_parent_id = 272593   
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        except:
            pass
        
        try:
            org_email = tender_html_element.find_element(By.XPATH, '(//td[7])['+str(num)+']').get_attribute("innerHTML") 
            customer_details_data.org_email = fn.get_email(org_email)
        except:
            pass

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
        local_description = tender_html_element.find_element(By.XPATH, '(//td[7])['+str(num)+']').get_attribute("innerHTML")
        notice_data.local_description = local_description.split('#')[4]
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = local_description.split('#')[8].strip()
    except Exception as e:
        logging.info("Exception in notice_no : {}".format(type(e).__name__))
        pass

    try:   
        notice_url = WebDriverWait(tender_html_element, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.btn-group > a'))).get_attribute("href")    
        tenderid = notice_url.split('?')[-1].strip()
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
        
    try:
        fn.load_page(page_details,notice_url,80)
    except:
        pass
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'div.page-inner.mt--5  table > tbody > tr'):
            attachments_data = attachments() 

            external_url = single_record.find_element(By.CSS_SELECTOR, 'a.btn.pull-right.downloadable').get_attribute("ng-show")
            if "i.ContentType!='Folder'" in external_url:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'a.btn.pull-right.downloadable').click()
                time.sleep(2)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                if attachments_data.external_url != '':
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('.')[-1].strip()
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split(attachments_data.file_type)[0].strip()
                    attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

                    
            if attachments_data.external_url != None:
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except:
        pass
    
    try:
        external_url = "https://tenderbulletin.eskom.co.za/webapi/api/Files/DownloadAll?"+tenderid
        attachments_data = attachments() 
        for single_record in page_details.find_elements(By.XPATH,'//tr//a[1][not(@class="ng-hide")]'):
            
            is_folder = single_record.get_attribute("ng-show")
            if "i.ContentType=='Folder'" in is_folder:
                try:
                    attachments_data.external_url = external_url
                    attachments_data.file_name = "Documents"
                    attachments_data.file_type = "Zip"
                except:
                    pass
        if attachments_data.external_url != None:
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
        pass
        
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
page_details.maximize_window()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tenderbulletin.eskom.co.za/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        time.sleep(2)
        clk_Pub_dt = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="add-row"]/thead/tr/th[2]'))).click()
        time.sleep(5)

        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tbodyID"]/tr'))).text
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tbodyID"]/tr')))
            length = len(rows)
            num = 1
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tbodyID"]/tr')))[records]
                extract_and_save_notice(tender_html_element)
                num +=1
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
                next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tbodyID"]/tr'),page_check))
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
