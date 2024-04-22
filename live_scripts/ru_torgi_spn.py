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
import gec_common.Doc_Download_VPN


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ru_torgi_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ru_torgi_spn'
    
    notice_data.main_language = 'RU'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'RUB'
        
    notice_data.notice_type = 4
        
    try: 
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, ' div.noticeStatus > span.noticeStatus-biddform').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try: 
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.noticeNumber').text.split('Версия')[0].strip()
        notice_no = notice_data.notice_no.split('№')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div.noticeName > div').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, ' div > div.publishDate').text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'div.noticePrice > div > div').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e: 
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.notice_url = "https://torgi.gov.ru/new/public/notices/view/"+notice_no
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,100)
        logging.info(notice_data.notice_url)    

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main > app-work-area > div > div').get_attribute("outerHTML")                     
        except:
            pass

        customer_details_scroll = page_details.find_element(By.XPATH,'//*[contains(text(),"Организатор торгов")]//following::app-notice-org[1]')
        page_details.execute_script("arguments[0].scrollIntoView(true);", customer_details_scroll)
        time.sleep(8)

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'RU'
            customer_details_data.org_language = 'RU'

            WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.XPATH,'//*[contains(text(),"Полное наименование")]//following::div[1]')))
            time.sleep(5)
            org_name =  page_details.find_element(By.XPATH, '//*[contains(text(),"Полное наименование")]//following::div[1]').get_attribute('innerHTML')
            if '"' in org_name:
                customer_details_data.org_name =  org_name.replace('"','').strip().split('<!---->')[0].strip()
            else:
                customer_details_data.org_name =  org_name.split('<!---->')[0].strip()

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Фактический/почтовый адрес")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__)) 
                pass 

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Контактное лицо")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__)) 
                pass 

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Телефон")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                pass

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Адрес электронной почты")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__)) 
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass 


        lot_details_scroll = page_details.find_element(By.CSS_SELECTOR,'div.lot-collapsed-card')
        page_details.execute_script("arguments[0].scrollIntoView(true);", lot_details_scroll)
        time.sleep(3)
        try:
            parent_element = page_details.find_element(By.CSS_SELECTOR, 'div.lot-collapsed-card').text
            for lots in page_details.find_elements(By.CSS_SELECTOR, 'div.lot-collapsed-card'):

                click_lot = WebDriverWait(lots, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' app-inline-icon:nth-child(1) > app-icon-chevron-right > svg'))).click()
                time.sleep(5)

                WebDriverWait(lots, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' div > div:nth-child(2) > h4')))

                lot_number = 1
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_details_data.lot_title = lots.find_element(By.XPATH, '//*[contains(text(),"Открыть карточку лота")]//following::span[2]').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                try:
                    lot_details_data.lot_description = lots.find_element(By.XPATH, '//*[contains(text(),"Описание лота")]//following::div[1]').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass     

                try:
                    lot_grossbudget_lc = lots.find_element(By.XPATH, '//*[contains(text(),"Начальная цена")]//following::div[1]').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.contract_duration = lots.find_element(By.XPATH, '//*[contains(text(),"Срок заключения договора")]//following::div[1]').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass

        attachments_data_scroll = page_details.find_element(By.XPATH,'//*[contains(text(),"Документы лота")]//following::div[1]/app-hashed-attachments-list/div/div')
        page_details.execute_script("arguments[0].scrollIntoView(true);", attachments_data_scroll)
        time.sleep(3)
        try: 
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Документы лота")]//following::div[1]/app-hashed-attachments-list/div/div'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' app-button.attachments-list__item__buttons__name.align-label-left.display-flex.text-button-no-center.word-break-caption > button > span.button__label').text

                external_url = single_record.find_element(By.CSS_SELECTOR, ' app-button.attachments-list__item__buttons__name.align-label-left.display-flex.text-button-no-center.word-break-caption > button > span.button__label').click()
                time.sleep(2)                                                
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])

                try:
                    file_size = single_record.find_element(By.CSS_SELECTOR, 'div > div.file-name-with-info > div.attachments-list__item__description > span:nth-child(1)').text
                    attachments_data.file_size = GoogleTranslator(source='auto', target='en').translate(file_size)
                except:
                    pass

                try:
                    attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
                except:
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
            pass

        try: 
            notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Дата и время окончания подачи заявок")]//following::div[1]').text
            notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline1: {}".format(type(e).__name__))
            pass

        try:
            notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Дата и время окончания приема заявлений")]//following::div[1]').text
            notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline2: {}".format(type(e).__name__))
            pass

        attachments_scroll = page_details.find_element(By.XPATH,'(//*[contains(text(),"Документы извещения")]//following::div[1])[2]')
        page_details.execute_script("arguments[0].scrollIntoView(true);", attachments_scroll)

        try: 
            for single_record in page_details.find_elements(By.XPATH, '(//*[contains(text(),"Документы извещения")]//following::div[1])[2]/div/div'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' div > div > div.file-name-with-info > div:nth-child(1)').text

                external_url = single_record.find_element(By.CSS_SELECTOR, ' app-button.attachments-list__item__buttons__name.align-label-left.display-flex.text-button-no-center.word-break-caption > button > span.button__label').click()
                time.sleep(2)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])

                try:
                    file_size = single_record.find_element(By.CSS_SELECTOR, ' div.file-name-with-info > div.attachments-list__item__description > span:nth-child(1)').text
                    attachments_data.file_size = GoogleTranslator(source='auto', target='en').translate(file_size)
                except:
                    pass

                try:
                    attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
                except:
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
            pass

    except Exception as e:
        logging.info("Exception in page_details: {}".format(type(e).__name__)) 
        pass
                 
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

options = webdriver.ChromeOptions()
options.add_extension("Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
page_main.maximize_window()
time.sleep(10)

page_details = Doc_Download.page_details
time.sleep(10)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://torgi.gov.ru/new/public/notices/reg"] 
    for url in urls:
        fn.load_page(page_main, url, 70)
        logging.info('----------------------------------')
        logging.info(url)  

        click_Извещение = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'form > app-collapse > div > div.card-header.arrow-position-right')))
        page_main.execute_script("arguments[0].click();",click_Извещение)
        time.sleep(5)

        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"(//*[@class='ng-arrow-wrapper'][1])[5]"))).click()
        time.sleep(5)

        lst = [0,1,2]
        for index in lst:
            click = page_main.find_elements(By.CSS_SELECTOR, 'div.checkbox-wrapper__icon')[index]
            click.click()
            time.sleep(5)
            
        for more in range(1,15):
            more_click = WebDriverWait(page_main, 70).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' div.form-content > div > app-button > button')))
            page_main.execute_script("arguments[0].click();",more_click)
            time.sleep(5)
        
        time.sleep(10)
        
        try:
            rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.form-content > app-public-notice-list-view-item > div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.form-content > app-public-notice-list-view-item > div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
