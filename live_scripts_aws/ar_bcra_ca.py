from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ar_bcra_ca"
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
from selenium.webdriver.support.ui import Select

#Note:Open the site then go to "Estado Evento:" and select "Adjudicado" then grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ar_bcra_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'ar_bcra_ca'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'ARS'
    notice_data.main_language = 'ES'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.notice_url = url
    
    # Onsite Field -ID Evento
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, '#tdgbrRESP_INQA_HD_VW_GR\$0 > tbody > tr > td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objeto de la Contratación
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#tdgbrRESP_INQA_HD_VW_GR\$0 > tbody > tr > td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estado Evento
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, '#tdgbrRESP_INQA_HD_VW_GR\$0 > tbody > tr > td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha Publicación
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#tdgbrRESP_INQA_HD_VW_GR\$0 > tbody > tr > td:nth-child(6)").text
        try:
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        except:
            publish_date = re.findall('\d+/\d+/\d{4}  \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'BANCO CENTRAL DE LA REPÚBLICA ARGENTINA'
        customer_details_data.org_parent_id = '7785754'
        customer_details_data.org_country = 'AR'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try: 
        lot_number = 1
        lot_details_data = lot_details()
        # Onsite Field -Objeto de la Contratación
        lot_details_data.lot_number = lot_number
        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, '#tdgbrRESP_INQA_HD_VW_GR\$0 > tbody > tr > td:nth-child(4)').text
        
        notice_url_click = tender_html_element.find_element(By.CSS_SELECTOR, '#tdgbrRESP_INQA_HD_VW_GR\$0 > tbody > tr > td:nth-child(1) a').click()  
        time.sleep(3)

        try:
            award_details_data = award_details()

            # Onsite Field -Adjudicación - Orden de Compra >> Nombre
            award_details_data.bidder_name = page_main.find_element(By.CSS_SELECTOR, '#trAUC_BIDDERID_VW_\$30\$\$0_row1 > td:nth-child(3)').text

            # Onsite Field -Adjudicación - Orden de Compra >> Importe
            grossawardvaluelc = page_main.find_element(By.CSS_SELECTOR, '#trAUC_BIDDERID_VW_\$30\$\$0_row1 > td:nth-child(4)').text
            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
            award_details_data.grossawardvaluelc = float(grossawardvaluelc)
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
        lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#win0divPAGECONTAINER > table > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
   
    retrun_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' #BCA_EXPDOC_WRK_RETURN_PB'))).click()
    time.sleep(4)
    WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[7]/td[2]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/table/tbody/tr'))).text
    
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
page_main = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://ps.bcra.gob.ar/psp/sup/SUPPLIER/ERP/c/BCA_ESUP.AUC_RESP_INQ_AUC.GBL?&cmd=uninav&Rnode=LOCAL_NODE&uninavpath=Ra%C3%ADz"] 
    for url in urls:
        fn.load_page(page_main, url, 60)
        logging.info('----------------------------------')
        logging.info(url)
        
        iframe = page_main.find_element(By.XPATH,'//*[@id="ptifrmtgtframe"]')
        page_main.switch_to.frame(iframe)
        time.sleep(3)
        
        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#RESP_INQA_WK_AUC_STATUS'))
        pp_btn.select_by_index(1)
            
        search_btn = WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#RESP_INQA_WK_INQ_AUC_GO_PB'))).click()
        time.sleep(60)
        try:
            for page_no in range(2,5):
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
        except:
            logging.info("No new record") 
            pass
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
