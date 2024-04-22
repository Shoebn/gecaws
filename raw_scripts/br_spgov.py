#click on "Pesquisar" for data


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
import functions as fn
from functions import ET
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
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'br_spgov'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'PT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'BRL'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Oferta de Compra
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Início
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7) > table  td:nth-child(1)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Fim
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7) > table  td:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -data is present in "a)"
    # Onsite Comment -ref url   ---https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Edital.aspx?chave=&OC=WjGl6MQaVzC8Y5equn9l0S32slbcVOfFkogOu%2bMDlqSeTD5QUWmcrBlO2feWmFrR

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p:nth-child(9) > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p:nth-child(9) > span').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -data is present in "a)"
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p:nth-child(9) > span').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Oferta de Compra
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ctl00_c_area_conteudo_lbl_TextoEdital > table > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_c_area_conteudo_lbl_TextoEdital > table > tbody'):
            customer_details_data = customer_details()
        # Onsite Field -Ente Federativo
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),'UC')]//following::span[9]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'BR'
            customer_details_data.org_language = 'PT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

 # Onsite Field -click on "Convite" to get data for lots > next click on each lots for page_details1
# Onsite Comment -ref url ="https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Detalhe_Item.aspx?chave=&OC=MCMj1v1EhsQgdLb2mvsDYpBewRWQ7Ru3vFoO8pPLYpREjzA0f0sKUICEOriLIgHL&item=MCMj1v1EhsQgdLb2mvsDYtZlqMXnjEl4gcjJ2nhZslg%3d&cditem=MCMj1v1EhsQgdLb2mvsDYgq2I2XRanL1dBCV3z1r5tI%3d"

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#formulario > fieldset'):
            lot_details_data = lot_details()
        # Onsite Field -Descrição
        # Onsite Comment -ref url ="https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Detalhe_Item.aspx?chave=&OC=MCMj1v1EhsQgdLb2mvsDYpBewRWQ7Ru3vFoO8pPLYpREjzA0f0sKUICEOriLIgHL&item=MCMj1v1EhsQgdLb2mvsDYtZlqMXnjEl4gcjJ2nhZslg%3d&cditem=MCMj1v1EhsQgdLb2mvsDYgq2I2XRanL1dBCV3z1r5tI%3d"

            try:
                lot_details_data.lot_title = page_details1.find_element(By.XPATH, '//*[contains(text(),'Descrição')]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Especificação técnica
        # Onsite Comment -ref url ="https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Detalhe_Item.aspx?chave=&OC=MCMj1v1EhsQgdLb2mvsDYpBewRWQ7Ru3vFoO8pPLYpREjzA0f0sKUICEOriLIgHL&item=MCMj1v1EhsQgdLb2mvsDYtZlqMXnjEl4gcjJ2nhZslg%3d&cditem=MCMj1v1EhsQgdLb2mvsDYgq2I2XRanL1dBCV3z1r5tI%3d"

            try:
                lot_details_data.lot_description = page_details1.find_element(By.XPATH, '//*[contains(text(),'Especificação técnica')]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Item
        # Onsite Comment -ref url ="https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Detalhe_Item.aspx?chave=&OC=MCMj1v1EhsQgdLb2mvsDYpBewRWQ7Ru3vFoO8pPLYpREjzA0f0sKUICEOriLIgHL&item=MCMj1v1EhsQgdLb2mvsDYtZlqMXnjEl4gcjJ2nhZslg%3d&cditem=MCMj1v1EhsQgdLb2mvsDYgq2I2XRanL1dBCV3z1r5tI%3d"

            try:
                lot_details_data.lot_number = page_details1.find_element(By.XPATH, '//*[contains(text(),'Item')]//following::span[18]').text
            except Exception as e:
                logging.info("Exception in lot_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Código
        # Onsite Comment -ref url ="https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Detalhe_Item.aspx?chave=&OC=MCMj1v1EhsQgdLb2mvsDYpBewRWQ7Ru3vFoO8pPLYpREjzA0f0sKUICEOriLIgHL&item=MCMj1v1EhsQgdLb2mvsDYtZlqMXnjEl4gcjJ2nhZslg%3d&cditem=MCMj1v1EhsQgdLb2mvsDYgq2I2XRanL1dBCV3z1r5tI%3d"

            try:
                lot_details_data.lot_actual_number = page_details1.find_element(By.XPATH, '//*[contains(text(),'//*[contains(text(),'Código')]//following::span[1]')]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Unidade de fornecimento
        # Onsite Comment -ref url ="https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Detalhe_Item.aspx?chave=&OC=MCMj1v1EhsQgdLb2mvsDYpBewRWQ7Ru3vFoO8pPLYpREjzA0f0sKUICEOriLIgHL&item=MCMj1v1EhsQgdLb2mvsDYtZlqMXnjEl4gcjJ2nhZslg%3d&cditem=MCMj1v1EhsQgdLb2mvsDYgq2I2XRanL1dBCV3z1r5tI%3d"

            try:
                lot_details_data.lot_quantity_uom = page_details1.find_element(By.XPATH, '//*[contains(text(),'Unidade de fornecimento')]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quantidade
        # Onsite Comment -ref url ="https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Detalhe_Item.aspx?chave=&OC=MCMj1v1EhsQgdLb2mvsDYpBewRWQ7Ru3vFoO8pPLYpREjzA0f0sKUICEOriLIgHL&item=MCMj1v1EhsQgdLb2mvsDYtZlqMXnjEl4gcjJ2nhZslg%3d&cditem=MCMj1v1EhsQgdLb2mvsDYgq2I2XRanL1dBCV3z1r5tI%3d"

            try:
                lot_details_data.lot_quantity = page_details1.find_element(By.XPATH, '//*[contains(text(),'Quantidade')]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bec.sp.gov.br/BEC_Convite_UI/ui/BEC_CV_Pesquisa.aspx?chave="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,4):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[3]/div/div/div/div/div[2]/div[4]/div[2]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div/div/div/div/div[2]/div[4]/div[2]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[3]/div/div/div/div/div[2]/div[4]/div[2]/div/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[3]/div/div/div/div/div[2]/div[4]/div[2]/div/table/tbody/tr'),page_check))
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
 