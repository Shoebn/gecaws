from gec_common.gecclass import *
import logging
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
from selenium.webdriver.support.ui import Select
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "kz_nationalbank_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global notice_type
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'KZ'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'KZT'
    notice_data.main_language = 'RU'
    notice_data.script_name = 'kz_nationalbank_spn'

    notice_data.notice_type = 4

    notice_data.procurment_method = 2
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__)) 
        pass    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(2) a').get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass     
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__)) 
        pass
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        est_amount = est_amount.replace(' ','').replace(',','.')
        notice_data.est_amount = float(est_amount)
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__)) 
        pass 
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
    except:
        pass
    try:
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_data.publish_date = datetime.strptime(publish_date, '%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    logging.info(notice_data.publish_date)
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    try:
        notice_deadline =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__)) 
        pass


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH,'//*[contains(text(),"Организатор")]//following::td[1]').text
        customer_details_data.contact_person = page_details.find_element(By.XPATH,'//*[contains(text(),"ФИО автора объявления")]//following::td[1]').text
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH,'//*[contains(text(),"Электронный адрес организатора закупки")]//following::td[1]').text
        except:
            pass
        customer_details_data.org_country = 'KZ'
        customer_details_data.org_language = 'RU'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#w1 > table > tbody > tr '):
            attachments_data = attachments()
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(6) a ').get_attribute('href')
            time.sleep(5)
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except:
                pass
            attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
            attachments_data.file_size = re.sub("[^\d\.\,]","",attachments_data.file_size)
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass 
    try:
        lot_number=1
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#w2 > table > tbody > tr'):
            lot_details_data=lot_details()
            lot_details_data.lot_number = lot_number
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
            except:
                pass
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            try:
                lot_details_data.lot_description =  single_record.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except:
                pass
            try:
                lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
                lot_netbudget_lc = re.sub("[^\d\.\,]","",lot_netbudget_lc)
                lot_netbudget_lc = lot_netbudget_lc.replace(' ','').replace(',','.')
                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
            except:
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass        


    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text +=  page_details.find_element(By.CSS_SELECTOR,'body > div.container.content-container > div:nth-child(1) > div > div').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details= fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    for page_no in range(1,10):
        urls = ['https://zakup.nationalbank.kz/ru/publics/buys?page='+str(page_no)+'&per-page=50'] 

        for url in urls:
            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url)

            try:
                clk=page_main.find_element(By.CSS_SELECTOR,'body > div.container.content-container > div:nth-child(1) > div.col-sm-3.page-filter > div > div > form > div:nth-child(2) > div:nth-child(4) > label > span > span').click()
                clk=page_main.find_element(By.CSS_SELECTOR,'body > div.container.content-container > div:nth-child(1) > div.col-sm-3.page-filter > div > div > form > button.btn.btn-primary.btn-sm').click()
                time.sleep(5)
            except:
                pass

            try:
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#w0 > table > tbody > tr')))
                length = len(rows) 
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#w0 > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
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