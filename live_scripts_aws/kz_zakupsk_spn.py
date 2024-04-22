from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "kz_zakupsk_spn"
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
SCRIPT_NAME = "kz_zakupsk_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'kz_zakupsk_spn'
    
    notice_data.currency = 'KZT'
    
    notice_data.procurement_method = 2
    
    notice_data.main_language = 'RU'
    
    notice_data.notice_type = 4
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'KZ'
    notice_data.performance_country.append(performance_country_data)
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.m-found-item__num.ng-star-inserted').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
   
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#infinityScroll  div > h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'div.m-found-item__col--sum.ng-star-inserted').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','').replace(' ','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.m-found-item__layout.ng-star-inserted').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    try:
        notice_url = WebDriverWait(tender_html_element, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#infinityScroll div > h3')))
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(10) 
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
    

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'sk-main-dialog > div.m-modal__header').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    # Onsite Field -КОНЕЦ ПРИЕМА ЗАЯВОК
    # Onsite Comment -None

    try:
        notice_deadline = page_main.find_element(By.CSS_SELECTOR, "div.m-rangebox__layout.m-rangebox__layout--rtl").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -НАЧАЛО ПРИЕМА ЗАЯВОК
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.CSS_SELECTOR, "div:nth-child(1) > div.m-rangebox__date.ng-star-inserted").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        Attach_click = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.XPATH,'//button[@class="button button--default"]')))
        page_main.execute_script("arguments[0].click();",Attach_click)
        time.sleep(15)
    except:
        pass

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.forClickOutside.m-dropdown__pane.ng-star-inserted > ul  a')[1:]:
            attachments_data = attachments()
        # Onsite Field -Документы
        # Onsite Comment -click on "Документы"

            attachments_data.file_name = single_record.text
        
        # Onsite Field -Документы
        # Onsite Comment -click on "Документы"

            external_url = single_record.click()
            time.sleep(10)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
        
#         Onsite Field -Документы
#         Onsite Comment -click on "Документы"
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    try:              
        customer_details_data = customer_details()
    # Onsite Field -ЗАКАЗЧИК
    # Onsite Comment -None

        customer_details_data.org_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Общая информация')]//following::div[1]").text.split("ЗАКАЗЧИК")[1].strip()       

        customer_details_data.org_country = 'KZ'
        customer_details_data.org_language = 'RU'

    # Onsite Field -ЭЛЕКТРОННАЯ ПОЧТА
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.CSS_SELECTOR, 'div.m-infoblock__col.m-infoblock__col--rtl > div:nth-child(3').text.split("ЭЛЕКТРОННАЯ ПОЧТА")[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -ТЕЛЕФОН
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.CSS_SELECTOR, 'div.m-infoblock__col.m-infoblock__col--rtl > div:nth-child(4)').text.split("ТЕЛЕФОН")[1].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # # Onsite Field -Документы
# # Onsite Comment -None

    
# #NOTE -- click on Arrow - " div.m-accordion__layout.justify-content-end > a > svg"  for lot details

    try:
        lots = page_main.find_element(By.XPATH,"(//a[@class='page-link ng-star-inserted'])[last()]").text
        pages = int(lots)
        for page_no in range(1,pages+1):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.m-modal__row.ng-star-inserted > div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.m-modal__row.ng-star-inserted > div')))
            length = len(rows)
            lot_number = 1
            for records in range(0,length-1):
                single_record = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.m-modal__row.ng-star-inserted > div')))[records]
                click=single_record.find_element(By.CSS_SELECTOR, ' div.m-accordion__layout.justify-content-end > a')
                click.click()
                time.sleep(5)
 
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
 
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div.m-accordion__header > div:nth-child(2) > div.m-accordion__description').text
                lot_details_data.lot_title_english = notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
 
        #         # Onsite Field -Количество
        #         # Onsite Comment -None
 
                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'div.m-accordion__header > div:nth-child(3) > div.m-accordion__description').text
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass
 
        #         # Onsite Field -Краткая характеристика
        #         # Onsite Comment -click on down arrow for details " div.m-accordion__layout.justify-content-end > a > svg"
 
                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'div.m-accordion__body  div:nth-child(5) > div:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
 
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div.d-flex.align-items-center.m-accordion__col.w-10 > label').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
 
                try:
                    lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'div.m-accordion__header > div:nth-child(4) > div.m-accordion__description > span').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace(',','').replace(' ','').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass
 
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
 
            next_lot_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//a[@class="page-link"])[last()]'))).click()
            logging.info("lot next page")
            time.sleep(5)
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.m-modal__row.ng-star-inserted > div'),page_check))
    except:
        try:
            lot_number =1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.m-modal__row.ng-star-inserted > div'):
                click=single_record.find_element(By.CSS_SELECTOR, ' div.m-accordion__layout.justify-content-end > a')
                click.click()
                time.sleep(5)
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
 
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div.m-accordion__header > div:nth-child(2) > div.m-accordion__description').text
                lot_details_data.lot_title_english = notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
 
        #         # Onsite Field -Количество
        #         # Onsite Comment -None
 
                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'div.m-accordion__header > div:nth-child(3) > div.m-accordion__description').text
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass
 
        #         # Onsite Field -Краткая характеристика
        #         # Onsite Comment -click on down arrow for details " div.m-accordion__layout.justify-content-end > a > svg"
 
                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'div.m-accordion__body  div:nth-child(5) > div:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
 
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div.d-flex.align-items-center.m-accordion__col.w-10 > label').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
 
                try:
                    lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'div.m-accordion__header > div:nth-child(4) > div.m-accordion__description > span').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace(',','').replace(' ','').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass
 
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1 
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass
    
    back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ' div.m-modal__close-button > a'))).click()
    time.sleep(2)
    
    try:
        WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.m-sidebar__layout.m-sidebar__layout--header > div:nth-child(1) > span')))
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
page_main = Doc_Download.page_details 
page_main.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://zakup.sk.kz/#/ext?tabs=advert&adst=PUBLISHED&lst=PUBLISHED&page=1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="infinityScroll"]/div[3]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="infinityScroll"]/div')))
                length = len(rows)
                for records in range(2,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="infinityScroll"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"ngb-pagination > ul > li:nth-child(8) > a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="infinityScroll"]/div[3]'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
