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
import gec_common.Doc_Download_ingate

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "co_secop_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'co_secop_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CO'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'COP'
    
    notice_data.main_language = 'ES'
    
    notice_data.notice_type = 7
    
    notice_data.procurement_method = 2

    notice_data.notice_url = url

    
    try: 
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try: 
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > div > span > span').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+ \w+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount) 
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount : {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
    except Exception as e:
        logging.info("Exception in document_type_description : {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        notice_url_click = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10) > a').click()
        time.sleep(25)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    iframe = page_main.find_element(By.XPATH,'//*[@id="OpportunityDetailModal_iframe"]')
    page_main.switch_to.frame(iframe)
    WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/form/table/tbody/tr[4]/td/table/tbody/tr[1]/td/fieldset/div/table/tbody/tr[2]'))).text

    for i in range(1,3):
        i = page_main.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    try:
        notice_data.local_description = page_main.find_element(By.XPATH,'''//*[contains(text(),"Descripción:")]//following::td[1]/span[1]''').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH,'''//*[contains(text(),"Tipo de contrato")]//following::td[1]/span[1]''').text
        if 'Prestación de servicios' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Duración del contrato:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Dirección de ejecución del contrato")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass 
            
        customer_details_data.org_country = 'CO'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        cpv_at_source = ''
        codes = page_main.find_element(By.XPATH, '''//*[@id='fdsObjectOfTheContract_tblDetail_trRowMainObjectCPV_tdCellCat']''').text
        cpv_at_source_regex = re.compile(r'\d{8}')
        cpv_list = cpv_at_source_regex.findall(codes)
        for code in cpv_list:
            cpv_codes_list = fn.CPV_mapping("assets/co_secop_ca_cpvmap.csv",code)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = each_cpv
                cpv_at_source += each_cpv
                cpv_at_source += ','
    
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass


    try:
        notice_data.class_at_source = 'UNSPSC'
        class_codes_at_source = ''
        codes_at_source = page_main.find_element(By.XPATH, '''//*[@id='fdsObjectOfTheContract_tblDetail_trRowMainObjectCPV_tdCellCat']''').text
        cpv_regex = re.compile(r'\d{8}')
        code_list = cpv_regex.findall(codes_at_source)
        for codes in code_list:
            class_codes_at_source += codes
            class_codes_at_source += ','
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        class_title_at_source = '' 
        single_record = page_main.find_element(By.XPATH, '''//*[@id='fdsObjectOfTheContract_tblDetail_trRowMainObjectCPV_tdCellCat']''').text.split('\n')
        
        for record in single_record:
            try:
                cpv_regex = re.compile(r'\d{8}')
                code_list = cpv_regex.findall(record)[0]
                titles_at_source = re.split(code_list, record)[1]
                class_title_at_source += titles_at_source.replace('-','').strip()
                class_title_at_source +=','
            except:
                pass
        notice_data.class_title_at_source = class_title_at_source.rstrip(',') 
    except Exception as e:
        logging.info("Exception in class_title_at_source: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'table.PriceListLineTable > tbody > tr.PriceListLineRow'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        
            try:
                lot_class_codes_at_source = ''
                lot_cpv_at_source = ''
                codes_at_source = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                cpv_regex = re.compile(r'\d{8}')
                code_list = cpv_regex.findall(codes_at_source)
                for cpv_codes in code_list:
                    lot_class_codes_at_source += cpv_codes
                    lot_cpv_at_source += cpv_codes
                    lot_class_codes_at_source += ','
                    lot_cpv_at_source += ','
                
                lot_details_data.lot_class_codes_at_source = lot_class_codes_at_source.rstrip(',')
                lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
            except:
                pass


            try:
                lot_class_codes_at_source = ''
                lot_cpv_at_source = ''
                codes_at_source = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                cpv_regex = re.compile(r'\d{8}')
                code_list = cpv_regex.findall(codes_at_source)
                for cpv_codes in code_list:
                    cpv_codes_list = fn.CPV_mapping("assets/co_secop_ca_cpvmap.csv",cpv_codes)
                    for each_cpv in cpv_codes_list:
                        lot_cpvs_data = lot_cpvs()
                        lot_cpvs_data.lot_cpv_code = each_cpv
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except:
                pass
    
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
    
            try:
                l_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text 
                lot_quantity1 = l_quantity.replace(',','.').strip()
                lot_details_data.lot_quantity = float(lot_quantity1)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
    
            try:
                lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                lot_netbudget_lc = re.sub("[^\d\.]", "", lot_netbudget_lc) 
                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace('.','').strip()) 
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
                
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass   
  
    try: 
        for single_record in page_main.find_elements(By.XPATH, '/html/body/div[2]/div/form/table/tbody/tr[4]/td/table/tbody/tr[14]/td/fieldset/div/table/tbody/tr[3]/td/div/table/tbody/tr')[1:]: 
            attachments_data = attachments() 
            external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(2) > a")))
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(2)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.replace('.pdf','').strip()
            
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass   

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '//*[@id="tblContainer"]').get_attribute('outerHTML')
    except:
        pass

    try:
        page_main_close = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#tbToolBarPlaceholder_btnClose')))
        page_main.execute_script("arguments[0].click();",page_main_close)
        time.sleep(5)
    except:
        pass
    page_main.switch_to.default_content()
    WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/table/tbody/tr/td[3]/form/table/tbody/tr[2]/td/table/tbody/tr[6]/td/div[1]/table/tbody/tr[2]'))).text
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://community.secop.gov.co/Public/Tendering/ContractNoticeManagement/Index?currentLanguage=es-CO&Page=login&Country=CO&SkinName=CCE"] 
    for url in urls:
        fn.load_page(page_main, url, 100)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(20)
            
        select_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#selRequestStatus'))
        select_btn.select_by_index(3)
        time.sleep(5)

        click_buscar = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#btnSearchButton')))
        page_main.execute_script("arguments[0].click();",click_buscar)
        time.sleep(5)

        try:
            page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/table/tbody/tr/td[3]/form/table/tbody/tr[2]/td/table/tbody/tr[6]/td/div[1]/table/tbody/tr[2]'))).text
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/table/tbody/tr/td[3]/form/table/tbody/tr[2]/td/table/tbody/tr[6]/td/div[1]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length-1):
                tender_html_element = WebDriverWait(page_main,100).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/table/tbody/tr/td[3]/form/table/tbody/tr[2]/td/table/tbody/tr[6]/td/div[1]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)