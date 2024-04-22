
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "kz_mitwork_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "kz_mitwork_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'kz_mitwork_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'KZ'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'KZT'
    notice_data.main_language = 'RU'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    
            
    notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass           
    
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        est_amount = est_amount.split('KZT')[0].strip()
        notice_data.est_amount = float(est_amount.replace(' ','').replace(',','').strip())
        notice_data.netbudgetlc = notice_data.est_amount 
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass           
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text  
        publish_date = re.findall('\d+-\d+-\d+ \d+:\d+:\d+', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)    
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass        

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return        

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+-\d+-\d+ \d+:\d+:\d+', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)    
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass                 
            
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div').get_attribute("outerHTML")    
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url   
        pass         
        
    try:
        notice_url1 = page_details.find_element(By.XPATH, '(//*[contains(text(),"Организатор")]//following::td[1])[2]/a').get_attribute("href")                     
        fn.load_page(page_details2,notice_url1,80)
        logging.info(notice_url1)
        notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div').get_attribute("outerHTML")    
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))        
        pass

    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Организатор")]//following::td[5]').text        
        try:
            customer_details_data.org_address = page_details2.find_element(By.XPATH, '//*[contains(text(),"Адрес")]//following::td[3]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))        
            pass    
            
        try:
            customer_details_data.org_phone = page_details2.find_element(By.XPATH, '//*[contains(text(),"Телефон")]//following::td[4]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))        
            pass    
            
        try:
            org_fax = page_details2.find_element(By.XPATH, '//*[contains(text(),"Факс")]//following::td[5]').text
            if len(org_fax)>3:
                customer_details_data.org_fax = org_fax
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))        
            pass        
            
        customer_details_data.org_country = 'KZ'
        customer_details_data.org_language = 'RU'

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#w1 > table > tbody > tr'): 
            attachments_data = attachments()
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute('href') 
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
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
        notice_data.contract_type_actual = page_details2.find_element(By.XPATH, '//*[contains(text(),"Тип закупки")]//following::td[1]').text  
        if 'Закупка услуг' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Закупка товаров' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Закупка работ' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass        
        
    try:
        lot_text = page_details.find_element(By.CSS_SELECTOR, '#w2 > table > thead> tr').text
        if 'Номер' in lot_text:
            lot_number = 1 
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#w2 > table > tbody > tr'):

                test_text = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                if 'KZT' not in test_text:

                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number
                    lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

                    try:
                        notice_url2 = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
                        fn.load_page(page_details3,notice_url2,80)
                        logging.info(notice_url2)
                        notice_data.notice_text += page_details3.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div').get_attribute("outerHTML")    
                    except Exception as e:
                        logging.info("Exception in notice_url2: {}".format(type(e).__name__))        
                        pass
                    
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description) 

                    try:
                        lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                        lot_netbudget_lc = lot_netbudget_lc.split('KZT')[0].strip()
                        lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace(' ','').replace(',','').strip())  
                    except Exception as e:
                        logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                        pass   
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1

                else:
                    lot_details_data = lot_details()

                    lot_details_data.lot_number = lot_number
                    lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    try:
                        notice_url2 = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
                        fn.load_page(page_details3,notice_url2,80)
                        logging.info(notice_url2)
                        notice_data.notice_text += page_details3.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div').get_attribute("outerHTML")    
                    except Exception as e:
                        logging.info("Exception in notice_url2: {}".format(type(e).__name__))        
                        pass

                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description) 
                    try:
                        lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

                        lot_netbudget_lc = lot_netbudget_lc.split('KZT')[0].strip()
                        lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace(' ','').replace(',','').strip())  
                    except Exception as e:
                        logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                        pass   

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1

    except:
        try:
            lot_text = page_details.find_element(By.CSS_SELECTOR, '#w1 > table > tbody > tr').text
            
            lot_number = 1 
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#w1 > table > tbody > tr'):

                lot_details_data = lot_details()

                lot_details_data.lot_number = lot_number
                lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                
                try:
                    notice_url2 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
                    fn.load_page(page_details3,notice_url2,80)
                    logging.info(notice_url2)
                    notice_data.notice_text += page_details3.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div').get_attribute("outerHTML")    
                except Exception as e:
                    logging.info("Exception in notice_url2: {}".format(type(e).__name__))        
                    pass

                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description) 

                try:
                    lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

                    lot_netbudget_lc = lot_netbudget_lc.split('KZT')[0].strip()
                    lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace(' ','').replace(',','').strip())  
                except Exception as e:
                    logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                    pass   

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
            
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass   

        try:              
            for single_record in page_details3.find_elements(By.CSS_SELECTOR,'#w2 > table > tbody > tr'): 
                attachments_data = attachments()
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute('href') 
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
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
    
    notice_data.identifier = str(notice_data.script_name)  +  str(notice_data.local_description) + str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details2 = fn.init_chrome_driver(arguments) 
page_details3 = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://eep.mitwork.kz/ru/publics/buys"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
                
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#w0 > table > tbody > tr :nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#w0 > table > tbody > tr ')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#w0 > table > tbody > tr')))[records]   
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#w0 > table > tbody > tr :nth-child(1)'))).text  
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#w0 > table > tbody > tr :nth-child(1)'),page_check))
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
    page_details2.quit() 
    page_details3.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)            
            
    
    
