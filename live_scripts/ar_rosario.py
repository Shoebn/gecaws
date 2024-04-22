from gec_common.gecclass import *
import logging
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ar_rosario"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'USD'
    
    notice_data.main_language = 'ES'

   
    if values==1:
        notice_data.notice_type = 4
        notice_data.script_name = 'ar_rosario_spn'
    if values==3:
        notice_data.notice_type = 7
        notice_data.script_name = 'ar_rosario_ca'
    if values==4:
        notice_data.notice_type = 16
        notice_data.script_name = 'ar_rosario_amd'
    notice_data.procurment_method = 2
    
  
    try:
        notice_url=tender_html_element.get_attribute('onclick').split("location='")[1].split("'")[0]
        notice_data.notice_url = 'https://www.rosario.gob.ar/'+str(notice_url)
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass  
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Objeto')]//following::td[1]").text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except:
        pass
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
        if notice_data.notice_no == None or notice_data.notice_no == '':
            notice_data.notice_no = notice_data.notice_url.split('id=')[1]
    except:
        pass
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH,"//*[contains(text(),'Tipo de contratación')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__)) 
        pass  
    try:
        publish_date =  page_details.find_element(By.XPATH,"//*[contains(text(),'Fecha de Publicación')]//following::td[1]").text
        notice_data.publish_date = datetime.strptime(publish_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    logging.info(notice_data.publish_date)
    
    try:
        notice_deadline =  page_details.find_element(By.XPATH,"//*[contains(text(),'Fecha de apertura')]//following::td[1]").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d/%m/%Y  a las   %H:%M hs.').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__)) 
        pass
    logging.info(notice_data.notice_deadline)    
    
    try:
        document_opening_time =  page_details.find_element(By.XPATH,"//*[contains(text(),'Fecha de apertura')]//following::td[1]").text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    try:
        est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Presupuesto Oficial')]//following::td[1]").text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        if ',' in est_amount:
            est_amount = est_amount.replace(',','')
        notice_data.est_amount = float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__)) 
        pass  
    try:
        document_cost = page_details.find_element(By.XPATH, "//*[contains(text(),'Costo de Adquisición del Pliego')]//following::td[1]").text
        document_cost = re.sub("[^\d\.\,]","",document_cost)
        document_cost = est_amount.replace(',','')
        notice_data.document_cost=float(document_cost)
    except:
        pass

    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Consulta y venta del pliego')]//following::td[1]").text.split('-')[0]
        customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Consulta y venta del pliego')]//following::td[1]").text
        customer_details_data.org_email = fn.get_email(customer_details_data.org_address)
        customer_details_data.org_country = 'AR'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Ver pliego adjunto apto para cotizar')]//following::td[1]/ul/li/a"):
            attachments_data = attachments()
            external_url = single_record.get_attribute('href').split("('")[1].split("',")[0]
            external_url1 = single_record.get_attribute('href').split(",'")[1].split("'")[0]
            attachments_data.external_url = 'https://www.rosario.gob.ar/sitio/verArchivo?id='+str(external_url)+'&tipo='+str(external_url)+''
            time.sleep(5)
            attachments_data.file_name = single_record.text
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass 

    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
   
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details= fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    urls = ["https://www.rosario.gob.ar/sitio/licitaciones/buscarLicitacionVisual.do"]

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        index=[1,3,4]
        for values in index:
            fn.load_page(page_main, url, 50)
            pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#main-content > form > div:nth-child(7) > div:nth-child(1) > fieldset > div > select:nth-child(5)'))
            pp_btn.select_by_index(values)
            
            search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#main-content > form > div:nth-child(7) > div:nth-child(1) > fieldset > div > div > button')))
            page_main.execute_script("arguments[0].click();",search)
            time.sleep(7)
            
            try:
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #publicas > table > tbody > tr ')))
                length = len(rows) 
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#publicas > table > tbody > tr ')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break 
                        
            except:
                try:
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #privadas > table > tbody > tr   ')))
                    length = len(rows) 
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'##privadas > table > tbody > tr   ')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break
                except:
                    pass
            try:
                url2=page_main.find_element(By.CSS_SELECTOR,'#tab_privadas').get_attribute('href')
                fn.load_page(page_main,url2,80)
                try:
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #publicas > table > tbody > tr ')))
                except:
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #privadas > table > tbody > tr   ')))
                length = len(rows) 
                for records in range(0,length):
                    try:
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#publicas > table > tbody > tr ')))[records]
                    except:
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#privadas > table > tbody > tr ')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break   
            except:
                pass
            try:
                    
                url3=page_main.find_element(By.CSS_SELECTOR,'#tab_concursos').get_attribute('href')
                fn.load_page(page_main,url3,80)
                try:
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #publicas > table > tbody > tr ')))
                except:
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #privadas > table > tbody > tr   ')))
                length = len(rows) 
                for records in range(0,length):
                    try:
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#publicas > table > tbody > tr ')))[records]
                    except:
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#privadas > table > tbody > tr ')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break   
            except:
                pass
                    
            try:    
                url4=page_main.find_element(By.CSS_SELECTOR,'#tab_directa').get_attribute('href')
                fn.load_page(page_main,url4,80)
                try:
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #publicas > table > tbody > tr ')))
                except:
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,' #privadas > table > tbody > tr   ')))
                length = len(rows) 
                for records in range(0,length):
                    try:
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#publicas > table > tbody > tr ')))[records]
                    except:
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#privadas > table > tbody > tr ')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break    
            except:
                pass


    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
