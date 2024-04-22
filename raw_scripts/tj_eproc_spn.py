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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tj_eproc_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'tj_eproc_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'RU'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RU'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'RUB'
    
    # Onsite Field -№
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12    td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Название объявления
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12    td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Метод закупки
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12    td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Вид предмета закупки
    # Onsite Comment -Replace following keywords with given respective keywords ('Услуга = service' , 'Товар = supply' , 'Job   = service')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12 td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Вид предмета закупки
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12 td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Дата начала приема заявок
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-12 td:nth-child(7)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Дата окончания приема заявок
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-12 td:nth-child(8)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Название объявления
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12 td:nth-child(4) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Название объявления
    # Onsite Comment -if notice_no is not available in " №" field then pass notice_no from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12 td:nth-child(4) a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -in the detail_page there are 4 tabs as follows "Общие сведения" (selector :  div:nth-child(9)   li:nth-child(1)) , "Лоты" (selector :   div:nth-child(9)   li:nth-child(2) ) , "Разъяснение положений документации" (selector : "div:nth-child(9)   li:nth-child(3)") , "Протоколы" (selector : "div:nth-child(9)   li:nth-child(4)")
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.container-full > div.col-md-12').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -Закупающая организация
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.col-md-12 td:nth-child(3)'):
            customer_details_data = customer_details()
        # Onsite Field -Закупающая организация
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-12 td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Юр. адрес организатора
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'RU'
            customer_details_data.org_language = 'RU'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


# Onsite Field -Лоты >> Информация о лоте >> Код CPV
# Onsite Comment -Go to  "Лоты" tab (selector :   div:nth-child(9)   li:nth-child(2) ) ,  click on "div.col-md-12 div.panel-body td:nth-child(2) a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.modal div > div > table'):
            cpvs_data = cpvs()
        # Onsite Field -Лоты >> Информация о лоте >> Код CPV
        # Onsite Comment -Go to  "Лоты" tab (selector :   div:nth-child(9)   li:nth-child(2) ) ,  click on "div.col-md-12 div.panel-body td:nth-child(2) a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"

            try:
                cpvs_data.cpv_code = page_details1.find_element(By.CSS_SELECTOR, 'div.modal-body.modal-body-lot tr:nth-child(6) > td').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-md-12.col-lg-12.col-xs-12'):
            lot_details_data = lot_details()
        # Onsite Field -№ пункта плана
        # Onsite Comment -ref_url : "https://eprocurement.gov.tj/ru/announce/index/418782?tab=lots"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"№ пункта плана")] //following::tr//td[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Номер лота
        # Onsite Comment -ref_url : "https://eprocurement.gov.tj/ru/announce/index/418839?tab=lots"

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"№ п/п")] //following::tr//td[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Лоты >> Наименование пункта плана
        # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418958?tab=lots"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12  div.panel-body  td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Лоты >> Наименование
        # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418884?tab=lots"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12  div.panel-body  td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Лоты >> 	Дополнительная характеристика
        # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418958?tab=lots"

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12  div.panel-body  td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Лоты >> 	Дополнительная характеристика
        # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418838?tab=lots"

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12  div.panel-body  td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Лоты >> 	Кол-во
        # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418838?tab=lots"

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12  div.panel-body  td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Лоты >> 	Кол-во
        # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418795?tab=lots"

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12  div.panel-body  td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Лоты >> 	Ед. изм.
        # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418838?tab=lots"

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12  div.panel-body  td:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Лоты >> 	Ед. изм.
        # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418795?tab=lots"

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12  div.panel-body  td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

        # Onsite Field -Код CPV
        # Onsite Comment -click on "div.col-md-12 div.panel-body td:nth-child(2) a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"

            try:
                lot_details_data.lot_cpv_at_source = page_details1.find_element(By.CSS_SELECTOR, 'div.modal-body.modal-body-lot tr:nth-child(6) > td').text
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -Информация о лоте
        # Onsite Comment -click on "div.col-md-12 div.panel-body td:nth-child(2)	 a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"

            try:
                for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.modal div > div > table'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -Код CPV
                    # Onsite Comment -click on "div.col-md-12 div.panel-body td:nth-child(2)	 a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"

                    lot_cpvs_data.lot_cpv_code = page_details1.find_element(By.CSS_SELECTOR, 'div.modal-body.modal-body-lot  tr:nth-child(6) > td').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://eprocurement.gov.tj/en/searchanno"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,None):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody/tr')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody/tr'),page_check))
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)