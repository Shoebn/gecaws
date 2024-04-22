from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "qa_sidra"
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
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "qa_sidra"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global script_name
    global type1
    notice_data = tender()

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'QA'
    notice_data.performance_country.append(performance_country_data)
    notice_data.main_language = 'EN'
    notice_data.currency = 'QAR'
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except:
        pass
    
    if notice_data.document_type_description == 'Active':
        notice_data.script_name = 'qa_sidra_spn'
        notice_data.document_type_description = "Request For Quotation (RFQ)"
        notice_data.notice_type =4
    if notice_data.document_type_description == 'Awarded':
        notice_data.script_name = 'qa_sidra_ca'
        notice_data.notice_type =7
    if notice_data.document_type_description=='Amended' or notice_data.document_type_description=='Canceled' or notice_data.document_type_description=='Closed':
        notice_data.script_name = 'qa_sidra_amd'
        notice_data.notice_type =16

    try:  
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text  
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        tender_contract_start_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        tender_contract_start_date = re.findall('\d+/\d+/\d{2}',tender_contract_start_date)[0]
        notice_data.document_purchase_start_time = datetime.strptime(tender_contract_start_date,'%m/%d/%y').strftime('%Y/%m/%d')
    except:
        pass
    
    try:
        tender_contract_end_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        tender_contract_end_date = re.findall('\d+/\d+/\d{2}',tender_contract_end_date)[0]
        notice_data.document_purchase_end_time = datetime.strptime(tender_contract_end_date,'%m/%d/%y').strftime('%Y/%m/%d')
    except:
        pass
    try:
        if notice_data.notice_type !=7:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    if notice_data.notice_type == 7:
        lot_details_data = lot_details() 
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title 
        notice_data.is_lot_default = True
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    notice_text = tender_html_element.get_attribute('outerHTML')
    
    clk=tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) img ').click()
    time.sleep(5)
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name ="SIDRA MEDICINE"
        customer_details_data.org_parent_id =7373948
        customer_details_data.contact_person = page_main.find_element(By.XPATH,'//*[contains(text(),"Buyer")]//following::td[1]').text
        customer_details_data.org_email =page_main.find_element(By.XPATH,'//*[contains(text(),"Email")]//following::td[1]').text
        customer_details_data.org_country = 'QA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_no = page_main.find_element(By.XPATH,'//*[@id="pt1:r1:0:pt1:AP1:d31::_ttxt"]').text.split('Abstract: ')[1]
    except:
        pass
    
    try:              
        attachments_data = attachments()
        attachments_data.file_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Attachments")]//following::td[1]').text.split('(')[0].split('.')[0]
        attachments_data.external_url=page_main.find_element(By.XPATH, '//*[contains(text(),"Attachments")]//following::td/a').get_attribute('href')
        attachments_data.file_size = page_main.find_element(By.XPATH, '//*[contains(text(),"Attachments")]//following::td[1]').text.split('(')[1].split(')')[0]
        attachments_data.file_type = page_main.find_element(By.XPATH, '//*[contains(text(),"Attachments")]//following::td[1]').text.split('(')[0].split('.')[1]
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        notice_data.notice_text += notice_text
        notice_data.notice_text += page_main.find_element(By.XPATH,'//*[@id="pt1:r1:0:pt1:AP1:d31"]').get_attribute('outerHTML')
    except:
        pass
    
    clk=page_main.find_element(By.CSS_SELECTOR,'#pt1\:r1\:0\:pt1\:AP1\:d31\:\:ok').click()
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://fa-epxn-saasfaprod1.fa.ocs.oraclecloud.com/fscmUI/faces/NegotiationAbstracts?prcBuId=300000003054324&_adf.ctrl-state=12wnfqr60q_1&_afrLoop=56310434711060090&_afrWindowMode=0&_afrWindowId=null&_afrFS=16&_afrMT=screen&_afrMFW=1280&_afrMFH=551&_afrMFDW=1280&_afrMFDH=720&_afrMFC=8&_afrMFCI=0&_afrMFM=0&_afrMFR=144&_afrMFG=0&_afrMFS=0&_afrMFO=0"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        clk=page_main.find_element(By.CSS_SELECTOR,'#pt1\:r1\:0\:pt1\:AP1\:sf1\:b2').click()
        time.sleep(3)
        i=[3,4,5,7,6]
        for index in i:
            select_fr = Select(page_main.find_element(By.XPATH,'/html/body/div[2]/form/div/div[1]/div/div/div/div[3]/div/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[1]/table/tbody/tr/td[1]/div/div/div/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/div/span/div[2]/table/tbody/tr/td[1]/div/div[2]/div/div/div[2]/div/div/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td[1]/table/tbody/tr/td/span/select'))
            select_fr.select_by_index(index)
            time.sleep(3)

            clk=page_main.find_element(By.XPATH,'//*[@id="pt1:r1:0:pt1:AP1:qryId1::search"]').click()
            time.sleep(5)

            try:
                for page_no in range(2,10):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#pt1\:r1\:0\:pt1\:AP1\:AT1\:_ATp\:resId1\:\:db > table > tbody tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#pt1\:r1\:0\:pt1\:AP1\:AT1\:_ATp\:resId1\:\:db > table > tbody tr')))
                    length = len(rows)
                    for records in range(0,length-1):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#pt1\:r1\:0\:pt1\:AP1\:AT1\:_ATp\:resId1\:\:db > table > tbody tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
                            
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    try:   
                        next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#pt1\:r1\:0\:pt1\:AP1\:AT1\:_ATp\:resId1\:\:db > table > tbody tr'),page_check))
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
