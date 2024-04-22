from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uz_uzex_spn"
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
import gec_common.Doc_Download_VPN
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uz_uzex_spn"
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'uz_uzex_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UZ'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'UZS'
    notice_data.main_language = 'RU'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    notice_data.document_type_description = "Состоявшиеся"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__left > a:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__num-cat > a:nth-child(1) > div > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__left > div.lot-item__address').text.split(",")[0]
    except Exception as e:
        logging.info("Exception in org_city: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:  
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'div.lot-item__info > div:nth-child(2) > strong').text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lot-item__left > a:nth-child(2)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:  
        publish_date = WebDriverWait(page_details, 150).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div:nth-child(2) > div > p:nth-child(2) > strong'))).text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR,'div.card.p-4.mb-3.lot__products > div > div:nth-child(4) > p').text.split("Подробное описание:")[1]
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
        
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR,'div.card.p-4.mb-3.lot__products > div > h5').text
        lot_details_data.lot_title_english = notice_data.notice_title
        lot_details_data.lot_number = 1
        try:
            lot_quantity = page_details.find_element(By.CSS_SELECTOR,'div.lot__products__item__table-wrap > table > tbody > tr > td:nth-child(1)').text
            lot_quantity = re.findall("\d+",lot_quantity)[0]
            lot_details_data.lot_quantity = float(lot_quantity)
        except Exception as e:
            logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
            pass
        
        try:
            lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div.lot__products__item__table-wrap > table > tbody > tr > td:nth-child(6)').text
            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','').strip())
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        try:
            lot_details_data.contract_duration = page_details.find_element(By.CSS_SELECTOR,'div.lot__products__item__table-wrap > table > tbody > tr > td:nth-child(8)').text
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        try:
            lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR,'div.lot__products__item__table-wrap > table > tbody > tr > td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        est_amount1 = page_details.find_element(By.CSS_SELECTOR,'div.col-md-6.col-lg-4.mb-3 > div > p:nth-child(2) > strong').text
        est_amount = re.sub("[^\d\.\,]","",est_amount1)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try: 
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Дата вскрытия:")]//following::strong[1]').text
        document_opening_time = re.findall('\w+ \d+, \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%b %d, %Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
   

    try:               
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH,'//*[contains(text(),"Наименование заказчика:")]//following::div[1]').text
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH,'//*[contains(text(),"Адрес заказчика")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_city = org_city
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH,'//*[contains(text(),"Телефон:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR,'div:nth-child(3) > div > table > tbody > tr > th').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        customer_details_data.org_country = 'UZ'
        customer_details_data.org_language = 'RU'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:  
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div.row.row-cols-lg-3 > div > div > div'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(3)').text.split(":")[1].split(".")[0]
            external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.text-right > a')))
            page_details.execute_script("arguments[0].click();",external_url)
            file_dwn = Doc_Download.file_download()
            time.sleep(3)
            attachments_data.external_url = str(file_dwn[0])
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.file_type = attachments_data.external_url.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_data: {}".format(type(e).__name__)) 
        pass  

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.main__inner.d-print-none').get_attribute('outerHTML')
    except:
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(15)
page_details = Doc_Download.page_details
time.sleep(15)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://etender.uzex.uz/lots/1/0","https://etender.uzex.uz/lots/2/0"]
    for url in urls:
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/main/app-lot-list/div/div/section/div[3]/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/main/app-lot-list/div/div/section/div[3]/div/div')))
                length = len(rows)                                                                              
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/main/app-lot-list/div/div/section/div[3]/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
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
                    try:
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/main/app-lot-list/div/div/section/div[4]/div/pagination/ul/li[8]/a')))
                        page_main.execute_script("arguments[0].click();",next_page)
                    except:
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/main/app-lot-list/div/div/section/div[4]/div/pagination/ul/li[6]/a')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/main/app-lot-list/div/div/section/div[3]/div/div'))).text
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/main/app-lot-list/div/div/section/div[3]/div/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            pass

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
