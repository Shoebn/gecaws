from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ke_tendersgo_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ke_tendersgo_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ke_tendersgo_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'KE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'KES'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    notice_data.document_type_description = "Active Tenders"
    if 'No records to display' in tender_html_element.text:
        return
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(1)').text
    except:
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title =  notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
        if 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        if 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        if 'Disposal of assets' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        if 'Non Consultancy Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Non consultancy"
        if 'Consultancy Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Consultancy"
    except:
        pass
    try:
        notice_text = tender_html_element.get_attribute('innerHTML')
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "PUBLIC PROCUREMENT REGULATORY AUTHORITY"
        customer_details_data.org_parent_id = "7603908"
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        except:
            pass
        customer_details_data.org_country = 'KE'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'td.e-rowcell.e-templatecell > div > b:nth-child(1)').click()
        notice_data.notice_url = page_main.current_url 
        time.sleep(5)

        try:
            dispatch_date = page_main.find_element(By.CSS_SELECTOR,'#nav-home > div > form > div:nth-child(1) > div.card-body > table > tbody > tr:nth-child(5) > td:nth-child(2)').text
            notice_data.dispatch_date= datetime.strptime(dispatch_date, '%b %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass
        try:
            notice_text1 = page_main.find_element(By.CSS_SELECTOR,'#nav-home > div > form > div:nth-child(1) > div.card-body').get_attribute('innerHTML')
        except:
            pass
        try:
            publish_date = page_main.find_element(By.XPATH,'//*[contains(text(),"Portal Publish Date:")]//following::td[1]').text
            notice_data.publish_date= datetime.strptime(publish_date, '%Y %B %d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        try:
            notice_data.document_fee = page_main.find_element(By.XPATH,'//*[contains(text(),"Tender Fee:")]//following::td[1]').text
        except:
            pass
        try:
            notice_deadline1 =  page_main.find_element(By.XPATH,' //*[contains(text(),"Close Date:")]//following::td[1]').text
            notice_deadline2 =  page_main.find_element(By.XPATH,' //*[contains(text(),"Closing Time:")]//following::td[1]').text
            notice_deadline =  notice_deadline1 + ' ' +notice_deadline2   
            notice_data.notice_deadline = datetime.strptime(notice_deadline, '%b %d, %Y %H:%S').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass

        detail_page =  page_main.find_element(By.XPATH,'//*[contains(text(),"Public Link:")]//following::td[1]/a').get_attribute('href')
        fn.load_page(page_details,detail_page,80)

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#nav-home > div > form > div:nth-child(2) > div.card-body > div > div > table > tbody > tr:nth-child(n)'):
                attachments_data = attachments()
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text

                external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)')
                page_details.execute_script("arguments[0].click();",external_url)
                time.sleep(8)
                page_details.switch_to.window(page_details.window_handles[1])
                attachments_data.external_url = page_details.current_url
                time.sleep(8)
                page_details.close()
                page_details.switch_to.window(page_details.window_handles[0])
                time.sleep(10)


                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        notice_text3 = page_details.find_element(By.XPATH,'//*[@id="content"]/div/div/div').get_attribute('innerHTML')
        try:
            clk=page_main.find_element(By.XPATH,'//*[@id="nav-home"]/div/form/div[2]/div[3]/div/button').click()
        except:
            clk=page_main.find_element(By.XPATH,"(//*[@class ='btn btn-warning p-2'])[2]").click()
        
    except:
        pass
    try:
        notice_data.notice_text += notice_text
        notice_data.notice_text += notice_text1
        notice_data.notice_text += notice_text3
    except:
        pass
  
    WebDriverWait(tender_html_element, 20).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tbody > tr'),page_check))


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details  
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tenders.go.ke/OpenTenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(2,25):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,' /html/body/div[2]/div/div/div/div[3]/div/div/div/div[4]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div/div[3]/div/div/div/div[4]/div/table/tbody/tr')))
                length = len(rows)                                                                              
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, ' /html/body/div[2]/div/div/div/div[3]/div/div/div/div[4]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.XPATH,' /html/body/div[2]/div/div/div/div[3]/div/div/div/div[4]/div/table/tbody/tr'),page_check))
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
    
