
#click on "Pesquisa avançada" next >>>  click on Contrats(contracts) from top left box>>> select dates "Data da publicação" >>> next click on "Pesquisar"

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_pt_base_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "cross_check_pt_base_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder =  "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = cross_check_output()

    notice_data.script_name = 'pt_base_ca'
    notice_data.main_language = 'PT'
    notice_data.currency = 'EUR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PT'
    
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.class_at_source = 'CPV'

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_no = notice_data.notice_url.split('&id=')[1].strip()
    except:
        pass
    # Onsite Field -Publicação

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Objeto do contrato

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo de procedimento

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/pt_base_ca_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Preço contratual

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:             
        customer_details_data = customer_details()
        customer_details_data.org_country = 'PT'
        customer_details_data.org_language = 'PT' 
    # Onsite Field -Adjudicante

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos&texto=&tipo=0&tipocontrato=0&cpv=&aqinfo=&adjudicante=&adjudicataria=&sel_price=price_c1&desdeprecocontrato=&ateprecocontrato=&desdeprecoefectivo=&ateprecoefectivo=&desdeprazoexecucao=&ateprazoexecucao=&sel_date=date_c1&desdedatacontrato=&atedatacontrato=&desdedatapublicacao=&atedatapublicacao=&desdedatafecho=&atedatafecho=&pais=0&distrito=0&concelho=0"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="advanced_contratos"]'))).click()
        time.sleep(2) 
        
        pp_btn = Select(page_main.find_element(By.XPATH,'//*[@id="sel_date"]')) 
        pp_btn.select_by_index(1) 
        time.sleep(5) 
        
        date_data = th.strftime('%Y-%m-%d')
        yest_date = page_main.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div/div/div/form[1]/div[2]/div[2]/div[2]/div[7]/div/input[1]').clear()
        yest_date = page_main.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div/div/div/form[1]/div[2]/div[2]/div[2]/div[7]/div/input[1]').send_keys(date_data)
        time.sleep(5)
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search_contratos2"]'))).click()
        time.sleep(2)
        
        
        for page_no in range(1,100):#100
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="no-more-tables-mx767"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="no-more-tables-mx767"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="no-more-tables-mx767"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if notice_count == 50:
                    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'''//*[@id="page_'''+str(page_no)+'''"]''')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="no-more-tables-mx767"]/table/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
