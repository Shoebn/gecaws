from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "id_bigoid_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "id_bigoid_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"




# -------------------------------------------------------------------------------------------------------------------------------------------


# 1) for CA Go to URL : "https://www.bi.go.id/id/layanan/lelang-jasa-barang/default.aspx"

# 2) click on "Histori Tender​"  for CA details


# ----------------------------------------------------------------------------------------------------------------------------------------




def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'id_bigoid_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ID'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ID'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'IDR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Tanggal Pengumuman
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "th:nth-child(1)").text
        
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        try:
            publish_date = re.findall('[A-Za-z]+ \d+, \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')  
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     Onsite Field -Nama Perkerjaan
    # Onsite Comment -take local_title  as a text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Batas Akhir Pendaftaran
    # Onsite Comment -None

    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = "Histori Tender​"
    
    # Onsite Field -Nama Perkerjaan
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#DeltaPlaceHolderMain > div.content-text').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Nomor Pengadaan
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(1) > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -pagu
    # Onsite Comment -None

    try:
        grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(7) > td:nth-child(3)').text
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(',',''))
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
#     # Onsite Field -Pagu
#     # Onsite Comment -None

    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Url Link
#     # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(11) > td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    customer_details_data = customer_details()
    customer_details_data.org_name = '"bank indonesia"'
    customer_details_data.org_country = 'ID'
    customer_details_data.org_language = 'ID'
    customer_details_data.org_parent_id = '7627165'
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    
# Onsite Field -None
# Onsite Comment -None

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number=1
# Onsite Field -Nama Perkerjaan
# Onsite Comment -take local_title as a lot_title ,  take local_title as a text

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title

        award_details_data = award_details()

        # Onsite Field -Rekanan Pemenang
        # Onsite Comment -None
        award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(10)> td:nth-child(3)').text
        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -Lampiran
# # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr:nth-child(12)'):
            attachments_data = attachments()
        # Onsite Field -Lampiran
        # Onsite Comment -split only file_name for ex."Pengumuman_Pengadaan_20731.Pdf" , here split only "Pengumuman_Pengadaan_20731" , ref_url : "https://www.bi.go.id/id/layanan/lelang-jasa-barang/history/Pages/17871-5_19175_Konsultan%20MK%20KPwBI%20Tasikmalaya.aspx"
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
        
        # Onsite Field -Lampiran
        # Onsite Comment -split only file_type for ex."Pengumuman_Pengadaan_20731.Pdf" , here split only "Pdf"

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Lampiran
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bi.go.id/id/layanan/lelang-jasa-barang/default.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk=page_main.find_element(By.XPATH,'//*[@id="ul-floating"]/li[3]/a').click()
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_ctl54_g_8c904a79_3b2b_47ce_9bc0_24a31922ce5d_ctl00_UpdatePanelHistoryPengumumanLelang"]/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_ctl54_g_8c904a79_3b2b_47ce_9bc0_24a31922ce5d_ctl00_UpdatePanelHistoryPengumumanLelang"]/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_ctl54_g_8c904a79_3b2b_47ce_9bc0_24a31922ce5d_ctl00_UpdatePanelHistoryPengumumanLelang"]/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl00_ctl54_g_8c904a79_3b2b_47ce_9bc0_24a31922ce5d_ctl00_UpdatePanelHistoryPengumumanLelang"]/div[2]/table/tbody/tr'),page_check))
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
    
