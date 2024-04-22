from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "id_bigoid"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium import webdriver
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "id_bigoid"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'id_bigoid'
    
    notice_data.main_language = 'ID'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ID'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.notice_type = 4
   
    notice_data.currency = 'IDR'
    
    notice_data.document_type_description = 'Pengumuman Tender'
    
    # Onsite Field -Tanggal Pengumuman 30 November 2023
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "th").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        if ',' in publish_date:
            publish_date1 = re.findall('\w+ \d+, \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date1,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        else:
            publish_date1 = re.findall('\d+ \w+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date1,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Nama Perkerjaan
    # Onsite Comment -take local_title as a text
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Batas Akhir Pendaftaran
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        if ',' in notice_deadline:
            notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        else:
            notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
   
    # Onsite Field -Nama Perkerjaan
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,90)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
  
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#DeltaPlaceHolderMain > div.content-text').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Nomor Pengadaan
    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(1) > td:nth-child(3)').text
    except Exception as e:
        notice_data.notice_no = notice_data.notice_url.split("Pages/")[1].split("_Pengadaan")[0].strip()
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nama Perkerjaan
    # Onsite Comment -if notice_no is not available in "Nomor Pengadaan" field then paas the notice_no from notice_url

    
    # Onsite Field -Url Link
    # Onsite Comment -ref_url :: "https://www.bi.go.id/id/layanan/lelang-jasa-barang/announcement/Pages/19958_19958_Iklan%20Digital%20dan%20Tokoh%20Media%20Sosial%20Dalam%20Rangka%20Penguatan%20Strategi%20Komunikasi.aspx"

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(11) > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'bank indonesia'
        customer_details_data.org_country = 'ID'
        customer_details_data.org_language = 'ID'
        customer_details_data.org_parent_id = '7627165'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Lampiran
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr:nth-child(12)'):
            attachments_data = attachments()
        # Onsite Field -Lampiran
        # Onsite Comment -split only file_name for ex."Pengumuman_Pengadaan_20731.Pdf" , here split only "Pengumuman_Pengadaan_20731"  , ref_url : "https://www.bi.go.id/id/layanan/lelang-jasa-barang/announcement/Pages/20731_20731_Pengadaan%20dan%20Pemeliharaan%201%20(satu)%20Unit%20Sistem%20Briket%20600Kg%20Jam%20di%20KPwBI%20Provin.aspx"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, '#layout-lampiran').text
        
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, '#layout-lampiran').text.split(".")[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lampiran
        # Onsite Comment -None  #layout-lampiran > div > p > a

            try:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, '#layout-lampiran > div > a').get_attribute('href')
            except:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, '#layout-lampiran > div > p > a').get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Ceiling
    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(7) > td:nth-child(3)').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ceiling
    # Onsite Comment -ref_url : https://www.bi.go.id/id/layanan/lelang-jasa-barang/announcement/Pages/20176_20176_PENGADAAN%20ALAT%20KEBUGARAN%20E-CATALOGUE.aspx
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bi.go.id/id/layanan/lelang-jasa-barang/default.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[12]/div/div[3]/div[2]/div[4]/div/div[1]/div/div[2]/div[1]/div/div[1]/div/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[12]/div/div[3]/div[2]/div[4]/div/div[1]/div/div[2]/div[1]/div/div[1]/div/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[12]/div/div[3]/div[2]/div[4]/div/div[1]/div/div[2]/div[1]/div/div[1]/div/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input.next')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[12]/div/div[3]/div[2]/div[4]/div/div[1]/div/div[2]/div[1]/div/div[1]/div/div[2]/table/tbody/tr'),page_check))
                    time.sleep(5)
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
