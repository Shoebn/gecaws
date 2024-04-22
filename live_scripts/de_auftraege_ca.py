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
from gec_common import functions as fn
from deep_translator import GoogleTranslator
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "de_auftraege_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'de_auftraege_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'EUR'
    
    notice_data.main_language = 'DE'

    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    notice_data.notice_url = url
    
    notice_data.document_type_description = "award notice"
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').text
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
      
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_parent_id = 7800848
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_click = WebDriverWait(tender_html_element, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(3) > a')))
        page_main.execute_script("arguments[0].click();",notice_click)
        time.sleep(6)
    except:
        pass
    
    WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#BekSummaryModalContainer > div.modal-dialog.modal-lg > div > div.modal-header > h4'))).text
    
    try:
        publish_date = page_main.find_element(By.XPATH, '''//*[contains(text(),"Datum der Publikation")]//following::td[1]''').text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_no = page_main.find_element(By.CSS_SELECTOR, 'label.badge.badge-default > small').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#BekSummaryModalContainer > div.modal-dialog.modal-lg > div').get_attribute("outerHTML") 
    except:
        pass
    
    try:
        Bekanntmachung_click = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[5]/div/div[1]/div/div[2]/div/div/div[1]/div/div[2]/div/span')))
        page_main.execute_script("arguments[0].click();",Bekanntmachung_click)
        time.sleep(2)
    except:
        pass
    
    try: 
        iframe = page_main.find_element(By.XPATH,'/html/body/div[5]/div/div[1]/div/div[2]/div/div/div[3]/iframe')
        page_main.switch_to.frame(iframe)
        
        WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body'))).text
        time.sleep(4)
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'body').get_attribute("outerHTML") 
    except:
        pass
    
    try:  
        iframe2 = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div/div/div/span/div/iframe')))
        page_main.switch_to.frame(iframe2)
        WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div[1]/div/div[2]/span[2]')))
        attachments_data = attachments()
        
        attachments_data.file_name = page_main.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/span[2]').get_attribute('title')


        external_url = page_main.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/span[2]')
        page_main.execute_script("arguments[0].click();",external_url)
        time.sleep(3)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        print("external_url::",attachments_data.external_url)

        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass
        
        if attachments_data.file_name != '':
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'body').get_attribute("outerHTML") 
    except:
        pass
    
    page_main.switch_to.default_content()
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#selectboxSearch > div.dx-scrollable-wrapper').get_attribute("outerHTML") 
    except:
        pass
    
    try:
        close_button = page_main.find_element(By.CSS_SELECTOR, '#BekSummaryModalContainer > div.modal-dialog.modal-lg > div > div.modal-header > button').click()
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://www.auftraege.bayern.de/Dashboards/Dashboard_off?BL=09"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        
        accept = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' div.dx-lookup-field-wrapper > div.dx-lookup-field')))
        page_main.execute_script("arguments[0].click();",accept)
        time.sleep(2)
        
        accept1 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[10]/div/div[3]/div/div[1]/div/div[1]/div[2]/div[3]/div')))
        page_main.execute_script("arguments[0].click();",accept1)
        time.sleep(2)
        
        try:
            for scroll in  range(1,4):
                scroll = page_main.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
        except:
            pass
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div[1]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/div/div[3]/div/div[6]/div/div/div[1]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/div/div[3]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/div/div[3]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#gridContainerATender > div > div.dx-widget.dx-datagrid-pager.dx-pager > div.dx-pages > div > div:nth-child('+str(page_no)+')')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[3]/div[1]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/div/div[3]/div/div[6]/div/div/div[1]/div/table/tbody/tr'),page_check))
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
