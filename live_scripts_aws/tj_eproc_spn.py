from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tj_eproc_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tj_eproc_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'tj_eproc_spn'
    notice_data.main_language = 'RU'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TJ'
    notice_data.performance_country.append(performance_country_data)

    notice_data.notice_type = 4
    notice_data.procurement_method = 2
    notice_data.currency = 'TJS'
    
    # Onsite Field -Название объявления
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Метод закупки
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Вид предмета закупки
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        if "Услуга" in notice_data.contract_type_actual or 'Job' in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Service"
        elif "Товар" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Дата начала приема заявок
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Дата окончания приема заявок
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
        notice_deadline = re.findall('\\d{4}-\d+-\d+ \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Название объявления
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    # Onsite Field -№
    # Onsite Comment -None
    # Onsite Field -Название объявления
    # Onsite Comment -if notice_no is not available in " №" field then pass notice_no from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.strip()
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('/')[-1].strip()
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
        customer_details_data = customer_details()
        customer_details_data.org_country = 'TJ'
        customer_details_data.org_language = 'RU'
    # Onsite Field -Закупающая организация
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

    # Onsite Field -Юр. адрес организатора
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(7) td').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


# Onsite Field -Лоты >> Информация о лоте >> Код CPV
# Onsite Comment -Go to  "Лоты" tab (selector :   div:nth-child(9) li:nth-child(2) a ) ,  click on "div.col-md-12 div.panel-body td:nth-child(2) a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"
    try:
        lot_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(9) li:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details1,lot_url,80)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'div.content-block > div:nth-child(9) > div').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        lot_number = 1
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'td:nth-child(2)'):
            lot_clk = WebDriverWait(single_record, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a.btn-select-lot"))).click()
            time.sleep(5)
    
            try:                           
                notice_data.notice_text += WebDriverWait(page_details1, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.modal-body.modal-body-lot'))).get_attribute("outerHTML")                    
            except:
                pass
    
            # Onsite Field -None
            # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details
    
            try:              
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
            # Onsite Field -№ пункта плана
            # Onsite Comment -ref_url : "https://eprocurement.gov.tj/ru/announce/index/418782?tab=lots"

                try:
                    lot_details_data.lot_actual_number = page_details1.find_element(By.XPATH, '(//*[contains(text(),"№ пункта плана")])[2]//following::td[1]').text
                except:
                    try:
                        lot_details_data.lot_actual_number = page_details1.find_element(By.XPATH, '//*[contains(text(),"№ пункта плана")] //following::td[1]').text
                    except Exception as e:
                        logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                        pass
            
                # Onsite Field -Лоты >> Наименование пункта плана
                # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418958?tab=lots"
                                                    
                lot_details_data.lot_title = WebDriverWait(page_details1, 60).until(EC.presence_of_element_located((By.XPATH,'//*[contains(text(),"Наименование CPV")] //following::td[1]'))).text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            
                # Onsite Field -Лоты >> 	Дополнительная характеристика
                # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418958?tab=lots"
    
                try:
                    lot_details_data.lot_description = page_details1.find_element(By.XPATH, '(//*[contains(text(),"Дополнительная характеристика")])[2] //following::td[1]').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
            
                # Onsite Field -Лоты >> 	Кол-во
                # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418838?tab=lots"
                try:
                    lot_quantity = page_details1.find_element(By.XPATH, '(//*[contains(text(),"Количество")])[3]//following::td[1]').text
                    lot_details_data.lot_quantity = float(lot_quantity)
                except:
                    try:
                        lot_quantity = page_details1.find_element(By.XPATH, '//*[contains(text(),"Количество")]//following::td[1]').text
                        lot_details_data.lot_quantity = float(lot_quantity)
                    except Exception as e:
                        logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                        pass
            
                # Onsite Field -Лоты >> 	Ед. изм.
                # Onsite Comment -go to "Лоты" (selector :   div:nth-child(9)   li:nth-child(2)) tab for lot_details, ref_url : "https://eprocurement.gov.tj/ru/announce/index/418838?tab=lots"
        
                try:
                    lot_details_data.lot_quantity_uom = page_details1.find_element(By.XPATH, '//*[contains(text(),"Единица измерения")]//following::td[1]').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass
        
                # Onsite Field -Код CPV
                # Onsite Comment -click on "div.col-md-12 div.panel-body td:nth-child(2) a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"
        
                # Onsite Field -Информация о лоте
                # Onsite Comment -click on "div.col-md-12 div.panel-body td:nth-child(2)	 a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"
        
                try:
                    lot_cpvs_data = lot_cpvs()
    
                    # Onsite Field -Код CPV
                    # Onsite Comment -click on "div.col-md-12 div.panel-body td:nth-child(2)	 a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"
    
                    lot_cpvs_data.lot_cpv_code = page_details1.find_element(By.CSS_SELECTOR, 'div.modal-body.modal-body-lot  tr:nth-child(6) > td').text.split('-')[0].strip()
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass
            
            
            try:              
                cpvs_data = cpvs()
            # Onsite Field -Лоты >> Информация о лоте >> Код CPV
            # Onsite Comment -Go to  "Лоты" tab (selector :   div:nth-child(9)   li:nth-child(2) ) ,  click on "div.col-md-12 div.panel-body td:nth-child(2) a" for detail_page1 , ref_url : "https://eprocurement.gov.tj/ru/announce/index/418965?tab=lots" , "https://eprocurement.gov.tj/ru/announce/index/418969?tab=lots"
    
                cpvs_data.cpv_code = page_details1.find_element(By.CSS_SELECTOR, 'div.modal-body.modal-body-lot tr:nth-child(6) > td').text.split('-')[0].strip()
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
                pass
        
        
            clk = WebDriverWait(page_details1, 80).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[1]/div[2]/div[4]/div[5]/div/div/div/div/div/div[2]/div/div[2]/button"))).click()
            time.sleep(5)
    except:
        pass
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://eprocurement.gov.tj/ru/searchanno"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody/tr[2]'),page_check))
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
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
