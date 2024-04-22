from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tr_ekap"
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
SCRIPT_NAME = "tr_ekap"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'tr_ekap'
    
    notice_data.main_language = 'tr'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'TRY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -grab only numeric value , for ex. 2023/735464
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-5 p').text
    
    try:
        org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.alt.text-muted').text.split('-')[0].strip()
    except:
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text> h6').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p.card-text').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text > div > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_contract_type. eg., here "Hizmet - Açık İhale İlanı Yayımlanmış" take only "Hizmet" in notice_contract_type. 			2.replace following keword with given keywords("Hizmet=Service","Mal=Supply","Danışmanlık=Consultancy","Yapım=Works" )

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-text > div').text.split('-')[0].strip()
        if 'Hizmet' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Mal' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Danışmanlık' in notice_contract_type:
            notice_data.notice_contract_type = 'Consultancy'
        elif 'Yapım' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split type_of_procedure_actual. eg., here "Hizmet - Açık İhale İlanı Yayımlanmış" take only "Açık" in type_of_procedure_actual.
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.card-text > div").text.split('-')[1].split('\n')[0].strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/tr_ekap_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split only date ,for ex: "HAKKARİ - 07.09.2023 10:00" , here take only "07.09.2023"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div p.alt.text-muted").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    Bilgiler_clk = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div > div.col-md-5 > div > div > ul > li:nth-child(1) > button')
    page_main.execute_script("arguments[0].click();",Bilgiler_clk)
    time.sleep(3)
    iframe = page_main.find_element(By.XPATH,'//*[@id="sonuclar"]/div/div/div[2]/iframe')
    page_main.switch_to.frame(iframe)

    try:
        publish_date = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"İhale Onay Tarihi")]//following::td[1]'))).text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bilgiler  
    # Onsite Comment -for page_main you have to click on "Bilgiler" option , you will be see the 4 tabs for tender information
    try:
        notice_data.notice_text += WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tabIhaleBilgi"]/div/table/tbody'))).get_attribute("outerHTML")
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        cpvs_code = page_main.find_element(By.XPATH, '//*[contains(text(),"İhale Branş Kodları (OKAS)")]//following::td[1]').text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
        customer_details_data.org_city = org_city
        customer_details_data.org_country = 'TR'
        customer_details_data.org_language = 'TR'
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"İhale Yeri")]//following::span[1]').text.split('-')[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    page_main.switch_to.default_content()
    time.sleep(4)
    try:
        close = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button.close")))
        close.location_once_scrolled_into_view
        close.click()
        time.sleep(2)
    except:
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://ekap.kik.gov.tr/EKAP/Ortak/IhaleArama/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        for i in  range(1,10):
            i = page_main.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)      

        try:
            rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="sonuclar"]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="sonuclar"]/div')))[records]
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
