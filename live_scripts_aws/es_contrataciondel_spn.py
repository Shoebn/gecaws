from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_contrataciondel_spn"
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
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "es_contrataciondel_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'es_contrataciondel_spn'
    
    notice_data.main_language = 'ES'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    if types == 3 or types == 5:
        notice_data.notice_type = 4
    elif types ==2 or types==4:
        notice_data.notice_type = 3
    elif types==11 or types== 13:
        notice_data.notice_type = 16

    notice_data.publish_date = datetime.strptime(from_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
    logging.info(notice_data.publish_date)
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)> div:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)> div:nth-child(1) > a > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text 
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)> div:nth-child(1)').text
        if 'Suministros' in notice_contract_type:
            notice_data.notice_contract_type='Supply'
        elif 'Servicios' in notice_contract_type or 'Patrimonial' in notice_contract_type:
            notice_data.notice_contract_type='Service'
        elif 'Obras' in notice_contract_type or 'Administrativo especial' in notice_contract_type or 'Gestión de Servicios Públicos'  in notice_contract_type or 'Concesión de Servicios' in notice_contract_type or 'Concesión de Obras Públicas ' in notice_contract_type or 'Concesión de Obras' in notice_contract_type or 'Colaboración entre el sector público y sector privado' in notice_contract_type or 'Privado' in notice_contract_type:
            notice_data.notice_contract_type='Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass 
    
    try:
        customer_details_data = customer_details()

        customer_details_data.org_country = 'ES'
        customer_details_data.org_language = 'ES'
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text 
                    
        try:
            customer_detail_url =tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)> a').get_attribute('href')
            fn.load_page(page_details,customer_detail_url,80)
        except:
            pass
        
        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#FLYParent').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Street:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Town:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone no.:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Web address of contracting agency:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Activity")]//following::li[2]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data) 
    except:
        pass
    
    clk_url = tender_html_element.find_element(By.XPATH,'td/div/a[2]').get_attribute('href')
    page_main.execute_script("window.open('');")
    page_main.switch_to.window(page_main.window_handles[1])
    page_main.get(clk_url)
    time.sleep(5)
    
    try:
        notice_data.notice_url = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#viewns_Z7_AVEQAI930OBRD02JPMTPG21006_\:form1\:URLgenera'))).get_attribute('href')
    except:
         notice_data.notice_url=url   
    logging.info(notice_data.notice_url)
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.CellContentSkinTopUnlayered-H-Container_3').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass  
    
    try:
        notice_data.netbudgetlc=page_main.find_element(By.XPATH, '//*[contains(text(),"Presupuesto base de licitación sin impuestos")]//following::li[1]').text.split(' Euros')[0]
        notice_data.netbudgetlc=float(notice_data.netbudgetlc.replace(',','').strip())
    except:
        pass

    try:
        notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Objeto del contrato")]//following::li[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass    
 
    try:
        notice_data.local_description =notice_summary_english
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Valor estimado del contrato:")]//following::li[1]').text
        notice_data.grossbudgetlc=re.sub("[^\d\.\,]", "", notice_data.grossbudgetlc)
        notice_data.grossbudgetlc = float(notice_data.grossbudgetlc.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass 

    try:
        notice_data.est_amount =notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:              
        cpvs_data = cpvs()
        cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Código CPV")]//following::li[1]').text
        cpvs_data.cpv_code = re.sub("[^\d]","",cpv_code)
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#myTablaDetalleVISUOE > tbody > tr'):
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            if file_name != '':
                attachments_data = attachments()
                attachments_data.file_name = file_name

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)>div>a:nth-child(3)').get_attribute('href')   
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)  #myTablaDetalleVISUOE > tbody > tr:nth-child(1) > td.documentosPub.padding0punto2 > div > a:nth-child(3)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#viewns_Z7_AVEQAI930OBRD02JPMTPG21006_\:form1\:TableEx1_Aux > tbody > tr > td > table > tbody > tr '):
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            if file_name != '':
                attachments_data = attachments()             
                attachments_data.file_name = file_name

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a:nth-child(1)').get_attribute('href')   
                attachments_data.attachments_cleanup() 
                notice_data.attachments.append(attachments_data)

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#myTablaDetallePliegosPlatAgreVISUOE > tbody > tr'):
            file_name = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > div').text
            if file_name != '':
                attachments_data = attachments()             
                attachments_data.file_name = file_name
                attachments_data.file_type=attachments_data.file_name.split(".")[-1]

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' div > a').get_attribute('href')   
                attachments_data.attachments_cleanup() 
                notice_data.attachments.append(attachments_data)

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    page_main.close()
    time.sleep(2)
    page_main.switch_to.window(page_main.window_handles[0])
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    if notice_data.notice_deadline is None and notice_data.publish_date is None:
        return
  
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

arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://contrataciondelestado.es/wps/portal/!ut/p/b1/jY7LDoIwFES_xQ8w99KWIksECkUUlIfSDWFhDIbHxvj9VuPWyuwmOSczoKBZWw5HdFzKOFxATd2zv3WPfp664d0Vb1mY-b6ICW4KGiBJg6risa6RrYHGBJBlvk19Vid1zgsZIcpYBGll2Vrny3z8EQ__-WdQZoR8AdPFD2D4cIjn8QqNxpzWq8OjJ12K2fakh5J8X-YRsRAZlNDsYFSDEK68s85bvQDJVfkI/dl4/d5/L2dBISEvZ0FBIS9nQSEh/pw/Z7_AVEQAI930OBRD02JPMTPG21004/act/id=0/p=javax.servlet.include.path_info=QCPjspQCPbusquedaQCPFormularioBusqueda.jsp/551169209159/-/'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        index=[2,3,4,5,11,13]
        for types in index:
            try:
                select_fr = Select(page_main.find_element(By.XPATH,'//*[@id="viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:estadoLici"]'))
                select_fr.select_by_index(types)
            except:
                pass
            
            try:
                from_date=th.strftime('%d-%m-%Y')
                datefield = page_main.find_element(By.CSS_SELECTOR,'#viewns_Z7_AVEQAI930OBRD02JPMTPG21004_\:form1\:textMinFecAnuncioMAQ2').clear()
                datefield = page_main.find_element(By.CSS_SELECTOR,'#viewns_Z7_AVEQAI930OBRD02JPMTPG21004_\:form1\:textMinFecAnuncioMAQ2')
                datefield.click()
                datefield.send_keys(from_date)
            except:
                pass

            try:
                clk=  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.ID,'viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:button1')))
                page_main.execute_script("arguments[0].click();",clk)
            except:
                pass

            try:
                for page_no in range(1,10):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="myTablaBusquedaCustom"]/tbody/tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="myTablaBusquedaCustom"]/tbody/tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="myTablaBusquedaCustom"]/tbody/tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break

                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break

                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break

                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:footerSiguiente"]')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="myTablaBusquedaCustom"]/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
