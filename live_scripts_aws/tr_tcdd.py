from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tr_tcdd"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download_VPN as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tr_tcdd"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'tr_tcdd'
    
    notice_data.main_language = 'TR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'TRY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -1.split type_of_procedure_actual. here "AÇIK İHALE USULÜ / MAL ALIMI" take only "AÇIK İHALE USULÜ" in type_of_procedure_actual.
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "h3.c-menu.r-mt-0").text.split("/")[0]
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/tr_tcdd_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_contract_type. here "AÇIK İHALE USULÜ / MAL ALIMI" take only "MAL ALIMI" in notice_contract_type.  	2.Replace follwing keywords with given respective kywords ('EMLAK İHALELERİ=Service','YAPIM İŞLERİ= Works','MAL ALIMI=Supply','HİZMET ALIMI=Supply','DOĞRUDAN TEMİN=Supply')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'h3.c-menu.r-mt-0').text.split("/")[1]
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'h3:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "h3.auction-date.r-mt-0").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'h3:nth-child(4)'))).click()  
        time.sleep(5)
        notice_data.notice_url = page_main.current_url
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.sub-page-C').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -İLAN TARİHİ
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"İLAN TARİHİ")]//following::div').text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    # Onsite Field -DOSYA NUMARASI
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"DOSYA NUMARASI")]//following::div').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ŞARTNAME BEDELİ
    # Onsite Comment -None

    try:
        notice_data.document_fee = page_main.find_element(By.XPATH, '//*[contains(text(),"ŞARTNAME BEDELİ")]//following::div').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'TR'
        customer_details_data.org_language = 'TR'
    
        customer_details_data.org_name = page_main.find_element(By.XPATH,'//*[contains(text(),"İHALEYİ YAPACAK BİRİM")]//following::div').text
        
        # Onsite Field -İHALE YETKİLİSİ
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"İHALE YETKİLİSİ")]//following::div').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -TELEFON VE FAKS NO
        # Onsite Comment -split org_phone. eg., here "Tel: 0322 4575354/4249 Faks: 0322 4531195" take only "0322 4575354/4249".

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"TELEFON VE FAKS NO")]//following::div').text.split("Tel:")[1].split("Faks:")[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -TELEFON VE FAKS NO
        # Onsite Comment -split org_fax. eg., here "Tel: 0322 4575354/4249 Faks: 0322 4531195" take only "0322 4531195".

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"TELEFON VE FAKS NO")]//following::div').text.split("Faks:")[1]
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -ELEKTRONİK POSTA ADRESİ
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"ELEKTRONİK POSTA ADRESİ")]//following::div').text.strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -İHALE ADRESİ
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"İHALE ADRESİ")]//following::div').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        lot_details_data.lot_description = notice_data.notice_title
        
        try:
            lot_quantity_uom = page_main.find_element(By.XPATH, "//*[contains(text(),'Niteliği, türü ve miktarı')]//following::TD [2]").text
            lot_details_data.lot_quantity_uom = GoogleTranslator(source='auto', target='en').translate(lot_quantity_uom)
        except Exception as e:
            logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
            pass
        
        try:
            contract_duration = page_main.find_element(By.XPATH, "//*[contains(text(),'Süresi/teslim tarihi' )]//following::TD [2]").text
            lot_details_data.contract_duration = GoogleTranslator(source='auto', target='en').translate(contract_duration)
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.auction-table-td.doc-link'):
            try:
                attachments_data = attachments()
                attachments_data.file_name = single_record.text
                external_url = single_record.click()
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except:
                pass
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    try:
        WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div:nth-child(2) > div:nth-child(1) > h2')))
    except:
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
     
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tcdd.gov.tr/ihaleler/0"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/div[2]/div[2]/div[2]/div[2]/div/a')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/div[2]/div[2]/div[2]/div[2]/div/a')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
