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
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_ireps_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_ireps_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2

    notice_data.notice_url = url
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='es', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

    try:
        notice_data.document_type_decscription = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR,"td:nth-child(5)").text
        if 'Goods & Service' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Earning / Leasing' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            notice_data.notice_contract_type = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR,"td:nth-child(5)").text
        if 'Earning / Leasing' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Goods & Service' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) > a').click()   
        time.sleep(5)
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(20)
    except:
        pass

    try:
        customer_details_data = customer_details()  
        customer_details_data.org_name = org_name 
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try: 
        attachments_data = attachments()
        var_url = page_main.find_element(By.XPATH,'/html/body/table/tbody/tr[4]/td[2]/script[2]').get_attribute('innerHTML').split("var url=")[2].split(";")[0].strip()
        ext_var_url = var_url.replace("'",'').strip()
        attachments_data.external_url = 'https://ireps.gov.in'+str(ext_var_url)
        attachments_data.file_name = "Tender Documents"
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass

    try:  
        for single_record in page_main.find_elements(By.CSS_SELECTOR,'#attach_docs > tbody > tr')[1:]:
            attachments_data = attachments()
            ext_url = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2) > a').get_attribute('onclick')
            external_url = ext_url.split("('")[1].split("')")[0].strip()
            attachments_data.external_url = 'https://ireps.gov.in'+str(external_url)
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except:
                pass
    
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.XPATH,'//*[@id="content"]/table').get_attribute('outerHTML')
    except:
        pass

    try:
        for single_record in page_main.find_elements(By.CSS_SELECTOR,'#tempTable > tbody > tr:nth-child(1)')[1:]:
            corrigendum = single_record.find_element(By.CSS_SELECTOR,' td:nth-child(2)').text
            if 'Corrigendum' in corrigendum:
                notice_data.notice_type = 16

            try: 
                publish_date = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            try:
                notice_text_click = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(4) > a').click()
                time.sleep(5)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            page_main.switch_to.window(page_main.window_handles[1])
            time.sleep(5)
            try:
                notice_data.notice_text += page_main.find_element(By.XPATH,'/html/body/form/div/table').get_attribute('outerHTML')
            except:
                pass
            page_main.switch_to.window(page_main.window_handles[0])
            time.sleep(5)
    except:
        pass

   
    page_main.switch_to.window(page_main.window_handles[0])
    time.sleep(5)
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_head(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://ireps.gov.in"] 
    for url in urls:
        fn.load_page(page_main, url, 120)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
        try:   
            close_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#myModal > div > div > div > button')))
            page_main.execute_script("arguments[0].click();",close_click)
            time.sleep(3)
        except:
            pass

        search_tender = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[1]/div[1]/section/div/div/div[1]/div/div[2]/div/div/div[1]/div/div[3]/ul/li[1]/a")))
        page_main.execute_script("arguments[0].click();",search_tender)
        time.sleep(20)

        try:   
            custom_search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#custumSearchId')))
            page_main.execute_script("arguments[0].click();",custom_search)
            time.sleep(3)
        except:
            pass

        railway_pu = Select(page_main.find_element(By.CSS_SELECTOR,'#railwayZone'))
        railway_pu.select_by_index(43)

        select_date = Select(page_main.find_element(By.XPATH,'//*[@id="searchPeriodBlock"]/td/table/tbody/tr[2]/td[2]/select'))
        select_date.select_by_index(1)
        time.sleep(5)


        try:
            status_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#dateImgFrom'))).click()    
            time.sleep(5)

            action = ActionChains(page_main)

            action.send_keys(Keys.ARROW_LEFT)
            time.sleep(3)

            action.perform()

            action.send_keys(Keys.ENTER) 
            time.sleep(2)

            action.perform()
        except:
            pass

        try:   
            search_button = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#searchButtonBlock > td > input.buttonStyle')))
            page_main.execute_script("arguments[0].click();",search_button)
            time.sleep(5)
        except:
            pass

        try:
            for page_no in range(2,30):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/table[1]/tbody/tr[4]/td[2]/table/tbody/tr[1]/td/div/table/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table[1]/tbody/tr[4]/td[2]/table/tbody/tr[1]/td/div/table/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table[1]/tbody/tr[4]/td[2]/table/tbody/tr[1]/td/div/table/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/table[1]/tbody/tr[4]/td[2]/table/tbody/tr[1]/td/div/table/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr[2]'),page_check))
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