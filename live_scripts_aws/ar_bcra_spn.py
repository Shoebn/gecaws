from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ar_bcra_spn"
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
import gec_common.Doc_Download_ingate


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ar_bcra_spn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'ar_bcra_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'ARS'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ES'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -ID Evento
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    # Onsite Field -Objeto de la Contratación
    # Onsite Comment -None
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estado Evento
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha Publicación
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        try:
            publish_date = re.findall('\d+/\d+/\d+ \d+:\d+[apAP][Mm]',publish_date)[0]
        except:
            publish_date = re.findall('\d+/\d+/\d+  \d+:\d+[apAP][Mm]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%y %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Fecha Apertura / Pre pliego
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        try:
            notice_deadline = re.findall('\d+/\d+/\d+ \d+:\d+[apAP][Mm]',notice_deadline)[0]
        except:
            notice_deadline = re.findall('\d+/\d+/\d+  \d+:\d+[apAP][Mm]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ID Evento
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) a').click()  
        notice_data.notice_url = page_main.current_url
        time.sleep(30)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        iframe = page_main.find_element(By.CSS_SELECTOR,'iframe#ptifrmtgtframe')
        page_main.switch_to.frame(iframe)
    except:
        pass        
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#AUC_RESP_INQ_AUC').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
              
    customer_details_data = customer_details()
    customer_details_data.org_name = 'BANCO CENTRAL DE LA REPÚBLICA ARGENTINA'
    customer_details_data.org_parent_id = '7785754'
    customer_details_data.org_country = 'AR'
    customer_details_data.org_language = 'ES'
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#BCA_EXPDOC_WRK\$scroll\$0 > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(n) > td > div > span > a'):
            attachments_data = attachments()

    #         # Onsite Field -Pliego - Condiciones de Contratación >> Id Anexo
    #         # Onsite Comment -Note:Split only file_name,for ex:"Pliego_de_bases_y_condiciones_CP_04-23.pdf",here take only"Pliego_de_bases_y_condiciones_CP_04-23"


            attachments_data.file_name = single_record.text


    #         # Onsite Field -Pliego - Condiciones de Contratación >> Id Anexo
    #         # Onsite Comment -Note:Splite only file extention

            try:
                attachments_data.file_type = single_record.text.split('.')[1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

    #         # Onsite Field -Pliego - Condiciones de Contratación >> Id Anexo
    #         # Onsite Comment -None

            external_url = single_record.click()
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            time.sleep(20)

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    try:
        clk=page_main.find_element(By.XPATH,'//*[@id="BCA_EXPDOC_WRK_RETURN_PB"]').click()
        time.sleep(15)
    except:
        clk=page_main.find_element(By.XPATH,'//*[@id="ancBack"]').click()
        time.sleep(15)
        
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[7]/td[2]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/table/tbody/tr'))).text
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
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
    urls = ["https://ps.bcra.gob.ar/psp/sup/SUPPLIER/ERP/c/BCA_ESUP.AUC_RESP_INQ_AUC.GBL?&cmd=uninav&Rnode=LOCAL_NODE&uninavpath=Ra%C3%ADz"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        time.sleep(30)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            iframe = page_main.find_element(By.CSS_SELECTOR,'iframe#ptifrmtgtframe')
            page_main.switch_to.frame(iframe)
        except:
            pass
        
        
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[7]/td[2]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[7]/td[2]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[7]/td[2]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[7]/td[2]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/table/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
