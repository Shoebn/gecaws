from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_suedtirol"
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
import gec_common.Doc_Download
    
NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_suedtirol"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_suedtirol'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
        
    # Onsite Field -None
    # Onsite Comment -take local_title after the number(035555/2023)

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > span.process-type').text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_suedtirol_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo di appalto
    # Onsite Comment -In Tipo di appalto if "Lavori pubblici" take it under "works","Servizi' under 'Service" and "Fornitura" under "Goods".

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.contractType').text
        if 'Lavori pubblici' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Fornitura' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            notice_data.notice_contract_type = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > span.protocolId').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data di pubblicazione
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.publishedAt").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'td.amount').text
        grossbudgetlc = re.sub("[^\d\.\,]", "",grossbudgetlc)
        grossbudgetlc = grossbudgetlc.replace('.','').replace(',','.').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Oggetto
    # Onsite Comment -None
     
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

    try:
        cookie_click1 = WebDriverWait(page_details, 60).until(EC.element_to_be_clickable((By.XPATH,'/html/body/tendering-app/pleiade-footer2/div[2]/div/nav/div/button')))
        page_details.execute_script("arguments[0].click();",cookie_click1)
    except:
        pass
    
    try:                                                                                          
        clk = WebDriverWait(page_details, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.page-nav > div > a')))
        page_details.execute_script("arguments[0].click();",clk)
    except:
        pass
    
    # Onsite Field -None
    # Onsite Comment -if "manifestazioni di interesse tra" ia present then take notice_type=5 and if "Fine ricezione offerte tra" ia present then take notice_type=4 and other variation of keyword=4

    try:
        notice_type = page_details.find_element(By.CSS_SELECTOR, 'div.label.pad-top-20px > ul > li:nth-child(1)').text
        if 'manifestazioni di interesse tra' in notice_type:
            notice_data.notice_type = 5
        elif 'Fine ricezione offerte tra' in notice_type:
            notice_data.notice_type = 4
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "div.label.pad-top-20px > ul > li:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.content-panel').get_attribute("outerHTML")                     
    except:
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Contenuto').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.box-content.pad-20px.collapsible-content > div > div > div:nth-child(3) > div.pad-left-20px'):
            try:
                if 'Documento allegato' in single_record.text:
                    attachments_data = attachments()
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'h3').text
                    external_url = single_record.find_element(By.CSS_SELECTOR, 'div > a').click() 
                    file_dwn = Doc_Download.file_download()
                    attachments_data.external_url= (str(file_dwn[0]))
                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'div > span:nth-child(4)').text.split(':')[1].strip()
                    except:
                        pass
                    file_type =  attachments_data.external_url
                    if '.pdf' in file_type or '.PDF' in file_type:
                        attachments_data.file_type = 'pdf'
                    elif '.docx' in file_type:
                         attachments_data.file_type = 'docx'
                    elif '.doc' in file_type:
                         attachments_data.file_type = 'doc'
                    elif '.xlsx' in file_type:
                        attachments_data.file_type = 'xlsx'
                    elif '.zip' in file_type:
                        attachments_data.file_type = 'zip'
                    else:
                        pass
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
                else:
                    pass
            except:
                pass
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()    
        customer_details_data.org_language = 'IT'

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        try:                                                                              
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'li:nth-child(10) > span.value').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        clk3 = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,'CLASSIFICAZIONE')))
        page_details.execute_script("arguments[0].click();",clk3)
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > classification-tab').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR,"classification-first-level > div > div > div > div:nth-child(2) > div > span"):
            cpvs_data = cpvs()
            cpv_code = single_record.text
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
# Onsite Field -None
# Onsite Comment -to take lot_details click on "ELENCO LOTTI" in page details
    try:
        clk1 = WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.LINK_TEXT,'ELENCO LOTTI')))
        page_details.execute_script("arguments[0].click();",clk1)
    except:
        pass
    time.sleep(5)
    
    
        # Onsite Field -None
        # Onsite Comment -if lot_title is not present then take local_title as lot_title

    try:
        notice_url1 = page_details.find_element(By.CSS_SELECTOR, 'div.message.label.width-100.font-s.pad-btm-15px.truncate-word > a').get_attribute("href")
        fn.load_page(page_details1,notice_url1,80)
        logging.info(notice_url1)
        try:
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'div.content-panel').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in notice_text".format(type(e).__name__))
            pass

        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = page_details1.find_element(By.XPATH, "//*[contains(text(),'Oggetto')]//following::div[1]").text.split("Oggetto")[1].split("\n")[0]
        try:
            lot_details_data.lot_title_english = GoogleTranslator(source='it', target='en').translate(lot_details_data.lot_title)
        except:
            pass
        try:
            lot_details_data.lot_description = page_details1.find_element(By.XPATH, "//*[contains(text(),'Descrizione')]//following::div[1]").text
            lot_details_data.lot_description_english = GoogleTranslator(source='it', target='en').translate(lot_details_data.lot_description)
        except:
            pass
        
        # Onsite Field -CIG
        # Onsite Comment -None

        try:
            lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.cig > div.pad-btm-10px').text
        except Exception as e:
            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
            pass

        try:
            lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div.pad-btm-10px').text
            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR,"classification-first-level > div > div > div > div:nth-child(2) > div > span"):
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = single_record.text.split('-')[0]
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -click on "Classificazione" to take cpvs
   
    
    try:
        clk4 =  WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'REQUISITI DI PARTECIPAZIONE')))
        page_details.execute_script("arguments[0].click();",clk4)     
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'builder-tab:nth-child(6)').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text".format(type(e).__name__))
        pass
    
    try:
        clk5 =  WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'COMUNICAZIONI')))
        page_details.execute_script("arguments[0].click();",clk5)     
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'builder-tab:nth-child(8) > div').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text".format(type(e).__name__))
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
page_details = Doc_Download.page_details
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ausschreibungen-suedtirol.it/index/index/locale/it_IT"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            cookie_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' td:nth-child(2) > input[type=button]')))
            page_main.execute_script("arguments[0].click();",cookie_click)
        except:
            pass

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#Contenuto > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#Contenuto > table > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#Contenuto > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#Contenuto > table > tbody > tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
    page_details.quit()
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
