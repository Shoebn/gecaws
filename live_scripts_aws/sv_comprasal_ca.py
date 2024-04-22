

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "sv_comprasal_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sv_comprasal_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'sv_comprasal_ca'
    notice_data.main_language = 'ES'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SV'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'SVC'
    notice_data.procurement_method = 2

    notice_data.notice_type = 7

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute("href")                    
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url    

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Bien')]//following::div[1]").text  
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_summary_english = notice_data.local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)   
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        funding_agencies = page_details.find_element(By.XPATH, "//*[contains(text(),'Fuente de Financiamiento')]//following::p[1]").text 
        funding_agencies = funding_agencies.split('(')[1].split(')')[0]
        
        funding_agencies = fn.procedure_mapping("assets/sv_comprasal_ca_fundingagencycode.csv",funding_agencies)    
        if funding_agencies is not None :
            notice_data.funding_agencies = funding_agencies
        
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ngb-nav-0-panel').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Nombre del contacto')]//following::p[1]").text  
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'ES'
        customer_details_data.org_country = 'SV'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
    
        lot_details_data.lot_number = 1

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title

        try:
            lot_details_data.lot_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Bien')]//following::div[1]").text  
            lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(notice_data.lot_description)
            
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass

        try:
            Adjudicaciones_clk = page_details.find_element(By.XPATH,"(//a[contains(@class,'rounded-0 nav-link')])[3]").click()
            time.sleep(3)

            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ngb-nav-3-panel > app-purchase-awards > div > table > tbody > tr'):  

                award_details_data = award_details()

                award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > span').text

                grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                grossawardvaluelc = grossawardvaluelc.split('$')[1]
                award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',',''))

                award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
                award_details_data.award_date  = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        Documentos_clk = page_details.find_element(By.XPATH,"(//a[contains(@class,'rounded-0 nav-link')])[2]").click()
        time.sleep(3)

        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-purchase-documents > div > ul > li'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute("href") 
            try:
                attachments_data.file_type = attachments_data.file_name[-3:]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://unac.gob.sv/comprasalweb/procesos"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        Licitaciones_clk = page_main.find_element(By.XPATH,"(//span[contains(@class,'badge badge-pills border border-dark rounded-circle badge-light')])[1]").click()
        
        Contratación_Directa_clk = page_main.find_element(By.XPATH,"(//span[contains(@class,'badge badge-pills border border-dark rounded-circle badge-light')])[1]").click()
        
        Libre_Gestión_clk = page_main.find_element(By.XPATH,"(//span[contains(@class,'badge badge-pills border border-dark rounded-circle badge-light')])[1]").click()
        
        Compras_por_Lineamiento_clk = page_main.find_element(By.XPATH,"(//span[contains(@class,'badge badge-pills border border-dark rounded-circle badge-light')])[1]").click()

        Otros_clk = page_main.find_element(By.XPATH,"(//span[contains(@class,'badge badge-pills border border-dark rounded-circle badge-light')])[1]").click()

        Búsqueda_clk = page_main.find_element(By.XPATH,"//button[contains(@class,'btn btn-link button-without-outline py-0')]").click() 

        Desde_clk = page_main.find_element(By.XPATH,"(//button[contains(@class,'btn btn-dark calendar rounded-0')])[1]").click()

        back_arrow_clk = page_main.find_element(By.XPATH,"(//button[contains(@class,'btn btn-link ngb-dp-arrow-btn')])[1]").click()

        day_select_clk = page_main.find_element(By.XPATH,"(//div[contains(@class,'btn-light')])[7]").click()

        Gestión_clk = page_main.find_element(By.XPATH,"(//i[contains(@class,'fa fa-check')])[9]").click() 
        time.sleep(3)
        
        Adjudicado_clk = page_main.find_element(By.XPATH,"(//span[contains(@class,'badge badge-pills border border-dark rounded-circle badge-light')])[3]").click() 

        Buscar_clk = page_main.find_element(By.XPATH,"//button[contains(@class,'btn btn-dark rounded-0')]").click()

        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div[1]/table/tbody/tr'),page_check))
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
