
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_spgov"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_spgov"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'br_spgov'
    
    notice_data.main_language = 'PT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BRL'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7) > table  td:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4} \d{2}:\d{2}:\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7) > table  td:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d{2}:\d{2}:\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_url_click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(4)>a:nth-child(2)"))) 
        notice_url_click.location_once_scrolled_into_view 
        notice_url_click.click() 
        time.sleep(5) 
        notice_data.notice_url = page_main.current_url
    except:
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_main,50).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ctl00_c_area_conteudo_lbl_TextoEdital > table > tbody'))).get_attribute("outerHTML") 
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass 
        

    try:
        notice_data.local_title = page_main.find_element(By.CSS_SELECTOR, 'div > p:nth-child(9) > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
                

    try:       
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, ' font > table > tbody > tr:nth-child(n)')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number

            try:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass


            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass


            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

            lot_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(3)>font>b>a"))) 
            lot_click.location_once_scrolled_into_view 
            lot_click.click() 
            time.sleep(5) 
            page_main.switch_to.window(page_main.window_handles[1]) 

            try:
                notice_data.notice_text += WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#Form1'))).get_attribute("outerHTML")
            except Exception as e:
                logging.info("Exception in notice_text: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_description = page_main.find_element(By.CSS_SELECTOR, "#divTela > label.lblData02").text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass


            try:
                lot_details_data.lot_actual_number = page_main.find_element(By.CSS_SELECTOR, "#divTela > label:nth-child(8)").text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            page_main.switch_to.window(page_main.window_handles[0])


            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    try:
        url2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#topMenu > li:nth-child(1) > a'))).get_attribute("href") 
        fn.load_page(page_details,url2,80)
        logging.info(url2)
    except:
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#formulario > fieldset').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass 
    
    try:              
        customer_details_data = customer_details()


        customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'UC')]//following::span[10]").text
        
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Endereço da UC')]//following::span[1]").text
        except:
            pass
        
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Telefone da UC')]//following::span[1]").text
        except:
            pass
        
        
        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ctl00_c_area_conteudo_LblUsuario')))

    
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
    urls = ["https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Pesquisa.aspx?chave="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            page_main.find_element(By.CSS_SELECTOR,'#ctl00_c_area_conteudo_bt_Pesquisa').click()
        except:
            pass
        
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ctl00_c_area_conteudo_LblUsuario')))

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[3]/div/div/div/div/div[2]/div[4]/div[2]/div/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div/div/div/div/div[2]/div[4]/div[2]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div/div/div/div/div[2]/div[4]/div[2]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[3]/div/div/div/div/div[2]/div[4]/div[2]/div/table/tbody/tr[2]'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No records found")
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
