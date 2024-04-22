#click on "Ver todas as negociações em andamento"	

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_elicsc"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_elicsc"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'br_elicsc'
    
    notice_data.main_language = 'PT'
   
    notice_data.currency = 'BRL'

    notice_data.notice_type = 4
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.areaClique').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    element = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(2)")))
    element.location_once_scrolled_into_view
    element.click()
    time.sleep(5)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#divDetalhes> div'))).text
    
    try:
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#divDetalhes> div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        procurement_method = page_main.find_element(By.XPATH, "//*[contains(text(),'Tipo de processo:')]//following::span[1]").text
        if "Nacional" in procurement_method:
            notice_data.procurement_method= 0
        else:
            pass
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'

        customer_details_data.org_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Unidade compradora:')]//parent::li").text.split(':')[1]
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number=1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#gridItem > div.k-grid-content.k-auto-scrollable > table > tbody > tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number=lot_number

            try:
                title = single_record.find_element(By.CSS_SELECTOR, '  td:nth-child(2) > div ').text
                lot_title = GoogleTranslator(source='auto', target='en').translate(title)
                if "Lot" in lot_title:
                    pass
                else:
                    lot_details_data.lot_title=lot_title
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

            try:
                lot_quantity = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > span').text
                lot_quantity1 = re.sub("[^\d\.\,]","",lot_quantity)
                lot_quantity2=lot_quantity1.replace(".",'')
                lot_quantity3=lot_quantity2.replace(",",'.')
                lot_details_data.lot_quantity =float(lot_quantity3)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
            try:
                lot_details_data.lot_quantity_uom = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > span').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number+=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
        
    try:

        bacl_click =  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="areaDetalhes"]/div[1]/h1/div/a[8]')))
        page_main.execute_script("arguments[0].click();",bacl_click)
        time.sleep(5)
        WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div[4]/div/div[1]/div[3]/table/tbody/tr')))
    except:
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://e-lic.sc.gov.br/Default.aspx#"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            click=page_main.find_element(By.CSS_SELECTOR, '#colunaEsquerda > div:nth-child(1) > div.legenda > a')
            page_main.execute_script("arguments[0].click();",click)
            time.sleep(5)
        except:
            pass
        
        scheight = .1

        while scheight < 9.9:
            page_main.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
            scheight += .01

        time.sleep(2)

        try:
            page_check = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[3]/div[4]/div/div[1]/div[3]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div[4]/div/div[1]/div[3]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div[4]/div/div[1]/div[3]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    
