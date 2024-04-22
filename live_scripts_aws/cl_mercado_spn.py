from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cl_mercado_spn"
log_config.log(SCRIPT_NAME)
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
from selenium.webdriver.support.ui import Select
from deep_translator import GoogleTranslator
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cl_mercado_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
Doc_Download1 = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cl_mercado_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CL'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.main_language = 'ES'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.class_at_source = 'UNSPSC'
    
    notice_data.document_type_description = "Publicada"
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-6.id-licitacion').text.split('ID Licitación:')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no : {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > a > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, ' div.lic-bloq-footer > div > div:nth-child(1) > strong').text
    except:
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.lic-block-body > div:nth-child(1) > a").get_attribute("onclick").split("('")[1].split("')")[0].strip()
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#frmABM_Productos > div.FichaLight').get_attribute("outerHTML")                     
        except:
            pass

        try:#27-02-2024 1:42:28
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha de Publicación:")]//following::span[1]').text
            publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            try:
                publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div.lic-block-body > div:nth-child(3) > div:nth-child(2)').text
                publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            currency = page_details.find_element(By.XPATH, '//*[contains(text(),"Moneda")]//following::div[1]').text
            if 'American dollar' in currency:
                notice_data.currency = 'AUD'
            elif 'Peso Chileno' in currency:
                notice_data.currency = 'USD'
        except Exception as e:
            logging.info("Exception in currency: {}".format(type(e).__name__))
            pass

        try:#11-03-2024 15:00:00
            notice_deadline = page_details.find_element(By.XPATH, '''//*[contains(text(),"Fecha de Cierre:")]//following::span[1]''').text
            notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        try:
            notice_data.tender_quantity = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > table > tbody > tr:nth-child(1) > td:nth-child(2)').text
        except Exception as e:  
            logging.info("Exception in tender_quantity: {}".format(type(e).__name__))
            pass

        try: 
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción")]//following::span[1]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:
            for single_record in page_details.find_elements(By.XPATH, '(//*[contains(text(),"Criterios de evaluación")])[2]//following::tbody[1]/tr')[1:]:
                tender_criteria_data = tender_criteria()

                tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                if "Precio" in tender_criteria_data.tender_criteria_title:
                    tender_criteria_data.tender_is_price_related = True
                tender_criteria_weight =single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.replace('%','').strip()
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.tender_contract_number = page_details.find_element(By.XPATH, '//*[contains(text(),"N° de contrato:")]//following::div[1]').text
        except Exception as e:  
            logging.info("Exception in tender_contract_number: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'CL'
            customer_details_data.org_language = 'ES'
            customer_details_data.org_name = org_name

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Nombre de responsable de pago:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"e-mail de responsable de pago")]//following::span[1]').text.rstrip('.')
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Tiempo del Contrato")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        try:
            source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Fuente de financiamiento:")]//following::span[1]').text
            notice_data.source_of_funds = GoogleTranslator(source='auto', target='en').translate(source_of_funds)
        except Exception as e:
            logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
            pass

        try:
            est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Monto Total Estimado:")]//following::span[1]').text
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace(',','').strip())
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass 

        try:
            for code in page_details.find_elements(By.XPATH, '//*[contains(text(),"Cod:")]//following::span[1]'):
                data = code.text.strip()
                cpv_codes_list = fn.CPV_mapping("assets/cl_mercado_unspsccode.csv",data)
                for each_cpv in cpv_codes_list:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = each_cpv
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass

        try:
            class_title_at_source = ''
            for data in page_details.find_elements(By.CSS_SELECTOR, 'tbody > tr:nth-child(1) > td:nth-child(2) > div > table > tbody > tr:nth-child(1)'):
                class_title_at_source += data.text
                class_title_at_source += ','
            notice_data.class_title_at_source = class_title_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
            pass
        
        try:
            url = page_details.find_element(By.CSS_SELECTOR, "#imgAdjuntos").get_attribute("onclick").split("('..")[1].split("','")[0].strip()
            notice_url = "https://www.mercadopublico.cl/Procurement/Modules"+url
            fn.load_page(page_details1,notice_url,80)
            logging.info(notice_url)

            try:
                notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#form1 > table').get_attribute("outerHTML")                     
            except:
                pass

            try:              
                for single_record in page_details1.find_elements(By.XPATH, '//*[contains(text(),"Anexos Ingresados:")]//following::table[1]/tbody/tr')[1:]:
                    attachments_data = attachments()

                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
                        pass

                    external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(7) > input")))
                    page_details1.execute_script("arguments[0].click();",external_url)
                    time.sleep(2)
                    file_dwn = Doc_Download1.file_download()
                    attachments_data.external_url = str(file_dwn[0])

                    try:
                        attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                    except:
                        pass
                    
                    try:
                        attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.replace(attachments_data.file_type,'').strip()
                    except:
                        pass
                    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.replace(attachments_data.file_type,'').strip()
                    
                    if attachments_data.external_url != None:
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
                pass
        except:
            pass
        
        try:
            data = page_details.find_element(By.XPATH, '//*[@id="IdAntecedentes"]')
            for clicks in data.find_elements(By.CSS_SELECTOR, 'td:nth-child(1) >input'):
                clicks.click()
                time.sleep(5)
                try:
                    iframe = page_details.find_element(By.CSS_SELECTOR,'iframe.fancybox-iframe')
                    page_details.switch_to.frame(iframe)
                except:
                    pass

                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#grdAttachment > tbody > tr')[1:]:
                    attachments_data = attachments()

                    external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," td:nth-child(5) > input")))
                    page_details.execute_script("arguments[0].click();",external_url)
                    time.sleep(2)
                    file_dwn = Doc_Download.file_download()
                    attachments_data.external_url = str(file_dwn[0])

                    try:
                        attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                    except:
                        pass
                    
                    try:
                        attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.replace(attachments_data.file_type,'').strip()
                    except:
                        pass
                    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text.replace(attachments_data.file_type,'').strip()

                    if attachments_data.external_url != None:
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)

                attch_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#lblClose")))
                page_details.execute_script("arguments[0].click();",attch_click)
                time.sleep(5)
        except Exception as e:
            logging.info("Exception in attachments_data_2: {}".format(type(e).__name__))
            pass

    except Exception as e:  
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
page_details1 = Doc_Download1.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.mercadopublico.cl/Home/BusquedaLicitacion"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            iframe = page_main.find_element(By.CSS_SELECTOR,'#form-iframe')
            page_main.switch_to.frame(iframe)
        except:
            pass
        
        time.sleep(5)
        select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'#ordenarpor'))
        select_fr.select_by_index(4)
        time.sleep(5)
        try:
            for page_no in range(1,50):#50
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#searchResults > div:nth-child(3) > div:nth-child(3)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#searchResults > div:nth-child(3) > div')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#searchResults > div:nth-child(3) > div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#searchResults > div.col-xs-12 > div > ul > a.next-pager > li')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#searchResults > div:nth-child(3) > div:nth-child(3)'),page_check))
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
