from gec_common.gecclass import *
import logging
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from deep_translator import GoogleTranslator
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "tr_ilan_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global tnotice_count
    global notice_data
    notice_data = tender()
    
    
    
    notice_data.main_language = 'TR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'TRY'

    notice_data.procurement_method = 2

    
    
    # Onsite Field -Title---Başlık
    
    # Onsite Field -İhale Usulü

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,"ng-component > a > div > div:nth-child(3)").get_attribute('innerHTML')
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'ng-component > a > div > div:nth-child(2)').text
        if 'İhale İptal' in notice_data.local_title or 'İhale Düzeltme' in notice_data.local_title:
            notice_data.script_name = 'tr_ilan_amd'
            notice_data.notice_type = 16
        else:
            notice_data.script_name = 'tr_ilan_spn'
            notice_data.notice_type = 4
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title---Başlık

    try:
        notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'ng-component > a > div > div:nth-child(2)').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        document_type_description = page_main.find_element(By.CSS_SELECTOR, ' nav > div > div > div:nth-child(3) > a').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -İhale Türü

    try:
        notice_data.notice_url =tender_html_element.find_element(By.CSS_SELECTOR, 'ng-component > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass 
        
    try:
        publish_date = page_details.find_element(By.XPATH,"//*[contains(text(),'Yayınlandığı Gazeteler')]//following::div").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#description-content > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH,"//*[contains(text(),'Niteliği, türü ve miktarı')]//following::td[2]").text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Türü")]//following::div').text
        if 'Satış' in notice_contract_type or 'Kiraya Verme' in notice_contract_type or 'Kiralama ve Hizmet Alımı' in notice_contract_type:
            notice_data.notice_contract_type = 'Service' 
        elif 'Mal Alımı' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Yapım İşi' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no =  page_details.find_element(By.XPATH, '//*[contains(text(),"İlan Numarası")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.related_tender_id =  page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Kayıt No")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -İhale Usulü

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Usulü")]//following::div[1]').text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/tr_ilan_procedure.csv",notice_data.type_of_procedure_actual) 
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Kurum

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'ng-component > a > div > div:nth-child(1)').text

    # Onsite Field -Sehir

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'ng-component > a > div > div:nth-child(4)').text
        except:
            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Şehir")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

        try:
            org_phone = page_details.find_element(By.XPATH,'//*[contains(text(),"Telefon ve faks numarası")]//following::td[2]').text
            if '-' in org_phone:
                customer_details_data.org_phone = org_phone.replace('-',',')
        except:
            try:
                org_phone = page_details.find_element(By.CSS_SELECTOR, '#description-content > div ').text.split('Telefon ve faks numarası')[1].split(':')[1]
                if '-' in org_phone:
                    customer_details_data.org_phone = org_phone.replace('-',',')
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

    # Onsite Field -Adresi

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH,'//*[contains(text(),"Adresi")]//following::td[2]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'TR'
        customer_details_data.org_country = 'TR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.ilan.gov.tr/ilan/tum-ilanlar/ihale?ats=3'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,50): 
                page_check = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.XPATH,'/html/body/igt-root/main/igt-ad-list/div/div/div[2]/section/div[2]/div[2]/div/igt-ad-single-list[1]'))).text
                rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/igt-root/main/igt-ad-list/div/div/div[2]/section/div[2]/div[2]/div/igt-ad-single-list')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/igt-root/main/igt-ad-list/div/div/div[2]/section/div[2]/div[2]/div/igt-ad-single-list')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if notice_count == 20:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
    
                try:   
                    next_page = WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li.pagination-next.ng-star-inserted > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 180).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/igt-root/main/igt-ad-list/div/div/div[2]/section/div[2]/div[2]/div/igt-ad-single-list[1]'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
