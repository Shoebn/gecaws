from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_bayvebe"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
import time
from gec_common import functions as fn
import gec_common.Doc_Download_ingate as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_bayvebe"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_bayvebe'
    notice_data.main_language = 'DE'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2


    # Onsite Comment -click on 'aktuelle Ausschreibungen' to select 'aktuelle Vorinformationen' take all the data and repeat same for 'aktuelle Zuschlagsbekanntmachungen' and for 'aktuelle Vorinformationen' notice type will be 2 and for 'aktuelle Zuschlagsbekanntmachungen' notice type will be 7 
    
    notice_data.notice_type = 4
    notice_data.notice_url = url
    # Onsite Field -Titel
    # Onsite Comment -None
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('\n')[0]
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Frist
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Titel
    # Onsite Comment -split type_of_procedure_actual from the given selector
    try:              
       
        customer_details_data = customer_details()
        # Onsite Field -Vergabestelle
        # Onsite Comment -None
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    
        # Onsite Field -Region
        # Onsite Comment -None

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
    
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3) a > small").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping('assets/de_bayvebe_procedure.csv',type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
               
    # Onsite Field -Titel
    # Onsite Comment -None    
    
    try: 
        WebDriverWait(tender_html_element, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.BekSummary'))).click()
        time.sleep(5)
    except Exception as e:
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.tab-content'))).get_attribute('outerHTML')
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.additional_tender_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Internetadresse")]//following::a[1]').get_attribute("href")
    except:
        pass
    
    try:              
        cpvs_data = cpvs()
        # Onsite Field -CPV-Klassifizierung
        # Onsite Comment -None  #//*[contains(text(),"CPV-Klassifizierung")]//following::ul[1]/li/a/badge/small  #//h2[contains(text(),"CPV-Klassifizierung")]//following::small[1] 
        cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"CPV-Klassifizierung")]//following::ul[1]/li/a/badge/small').get_attribute("outerHTML")
        cpvs_data.cpv_code = cpv_code.split('>')[1].split('<')[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
  
 # Onsite Field -Bekanntmachung
# Onsite Comment -click on 'Bekanntmachung' to get attachment
    try:  
        attachments_data = attachments()  
        attachments_data.file_name =  'Bekanntmachung'
        
        WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="BekSummaryModalContainer"]/div/div/div[2]/div/div/div/div/ul/li[2]/a'))).click()
        page_main.switch_to.frame(page_main.find_element(By.TAG_NAME,"iframe")) 
        try:
            WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#RenderBodyContent > div > div > span > a"))).click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            try:
                attachments_data.file_type = str(file_dwn[0]).split('.')[-1]
            except:
                pass
        except:
            attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, "#RenderBodyContent > div > div > span > a").get_attribute('href')
            attachments_data.file_type = 'pdf'
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        page_main.switch_to.window(page_main.window_handles[0])
        close_secondWindow = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.modal-content.animated.fadeIn div.modal-footer > button.btn.btn-white')))
        page_main.execute_script("arguments[0].click();",close_secondWindow)
    except:
        pass

    WebDriverWait(page_main, 90).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="gridContainerATender"]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')

# ----------------------------------------- Main Body
page_main = Doc_Download.page_details
page_main.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.bayvebe.bayern.de/'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="gridContainerATender"]/div/div[11]/div[1]/div[3]'))).click()
        except:
            pass

        try:
            for page_no in range(2,15):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="gridContainerATender"]/div/div[6]/div/div/div[1]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="gridContainerATender"]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="gridContainerATender"]/div/div[6]/div/div/div[1]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="gridContainerATender"]/div/div[6]/div/div/div[1]/div/table/tbody/tr'),page_check))
                except:
                    try:
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="gridContainerATender"]/div/div[11]/div[2]/div['+str(page_no)+']')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="gridContainerATender"]/div/div[6]/div/div/div[1]/div/table/tbody/tr'),page_check))
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
    
