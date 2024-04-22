from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_contrat_ca"
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
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "es_contrat_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -Enter todays date in feild "Fecha publicación entre"> "Buscar" to get live data  and  select "Adjudicada", "Parcialmente Adjudicada","Resolución Provisional","Resuelta" in field "Estado" in tender_html_page to get contract_award data
    notice_data.script_name = 'es_contrat_ca'
  
    notice_data.main_language = 'ES'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 7
    
    # Onsite Field -Estado
    # Onsite Comment -None
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass   
    # Onsite Field -Expediente
    # Onsite Comment -None
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)> div:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Expediente
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)> div:nth-child(1) > a > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo de Contrato
    # Onsite Comment -Replace the following keywords with ("Suministros = supply" ,"Servicios = srevices","Obras = works","Administrativo especial = works","Privado= works","Gestión de Servicios Públicos = works","Concesión de Servicios = works" ,"Concesión de Obras Públicas = works","Concesión de Obras = works","Colaboración entre el sector público y sector privado = works")

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)> div:nth-child(1)').text
        if "Suministros" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Servicios" in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Obras" in notice_contract_type or "Colaboración entre el sector público y sector privado" in notice_contract_type or 'Administrativo especial' in notice_contract_type or 'Privado' in notice_contract_type or 'Gestión de Servicios Públicos' in notice_contract_type or 'Concesión de Servicios' in notice_contract_type or 'Concesión de Obras Públicas' in notice_contract_type or 'Concesión de Obras' in  notice_contract_type:
            notice_data.notice_contract_type = "Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'ES'
        customer_details_data.org_country = 'ES'
        # Onsite Field -Órgano de Contratación
        # Onsite Comment -None

        customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text.strip()
        
        try:
            fr= tender_html_element.find_element(By.CSS_SELECTOR, '#myTablaBusquedaCustom > tbody > tr> td> a').get_attribute("href")                     
            fn.load_page(page_details,fr,80)
        except:
            pass
        # Onsite Field -Street:
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Street:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Town:
#         # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Town:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Postcode:
#         # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Phone no.:
#         # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone no.:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Email:
#         # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Fax:
#         # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::li[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Web address of contracting agency:
#         # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Web address of contracting agency:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Activity
#         # Onsite Comment -None

        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Activity")]//following::li[2]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
    # Onsite Field -Expediente
    # Onsite Comment -None
    try:   
        url=WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(1)> div:nth-child(1) > a'))).click()
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.CellContentSkinTopUnlayered-H-Container_3').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    
    try:              
    # Onsite Field -Código CPV
    # Onsite Comment -None
        cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Código CPV")]//following::li[1]').text
        cpvss = re.findall('\d{8}',cpv_code)
        for cpv in cpvss:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Publicación en plataforma")]//following::div[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} \d{2}:\d{2}:\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except:        
        try:
            publish_date = page_main.find_element(By.CSS_SELECTOR, "#myTablaDetallePublicacionesPlatAgreVISUOE > tbody > tr:nth-child(1) > td:nth-child(1) > div").text
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    logging.info(notice_data.publish_date) 
        
    
    # Onsite Field -Objeto del contrato
    # Onsite Comment -None

    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Objeto del contrato")]//following::li[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Valor estimado del contrato:
    # Onsite Comment -None

    try:
        grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Valor estimado del contrato:")]//following::li[1]').text
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace(',','').strip())
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        netbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Presupuesto base de licitación sin impuestos")]//following::li[1]').text
        netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
        notice_data.netbudgetlc = float(netbudgetlc.replace(',','').strip())
    except:
        pass

    
    try:
        notice_data.notice_url = page_main.find_element(By.CSS_SELECTOR, '#viewns_Z7_AVEQAI930OBRD02JPMTPG21006_\:form1\:URLgenera').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#myTablaDetalleVISUOE > tbody > tr'):
            
        # Onsite Field -Documento
        # Onsite Comment -'tr > td > table > tbody > tr > td:nth-child(2) > span' "Documento"
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td.tipoDocumento.padding0punto2 > div').text
            if file_name is not None and file_name !='':
                attachments_data = attachments()
                attachments_data.file_name = file_name
            
        # Onsite Field -Ver documentos
        # Onsite Comment -'td > a:nth-child(1)' "Ver" take both this selector in attachments
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td.documentosPub.padding0punto2 > div > a:nth-child(3)').get_attribute('href')   
            
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
             
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#viewns_Z7_AVEQAI930OBRD02JPMTPG21006_\:form1\:TableEx1_Aux > tbody > tr > td > table > tbody > tr'):
            
        # Onsite Field -Documento
        # Onsite Comment -'tr > td > table > tbody > tr > td:nth-child(2) > span' "Documento"
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

            if file_name is not None and file_name !='':

                attachments_data = attachments()
                attachments_data.file_name = file_name
            
        # Onsite Field -Ver documentos
        # Onsite Comment -'td > a:nth-child(1)' "Ver" take both this selector in attachments
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute('href')   
            
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
             
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -Expediente
        # Onsite Comment -None

        try:
            lot_details_data.lot_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Lote / Descripción")]//following::li[1]').text
        except:
            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
        lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        lot_details_data.contract_type = notice_data.notice_contract_type 

        try:
            lot_cpvs_data = lot_cpvs()
            lot_cpvs_data.lot_cpv_code = cpvs_data.cpv_code
            lot_cpvs_data.lot_cpvs_cleanup()
            lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass    

        try:
                # Onsite Field -Adjudicatario
                # Onsite Comment -None
            bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Adjudicatario")]//following::li[1]').text
            if bidder_name is not None and bidder_name !='':
                award_details_data = award_details()
                award_details_data.bidder_name = bidder_name

                    # Onsite Field -Importe de Adjudicación
                    # Onsite Comment -None
                try:
                    grossawardvaluelc = page_main.find_element(By.XPATH, '//*[contains(text(),"Importe de Adjudicación")]//following::li[1]').text
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','').strip())
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass
                    # Onsite Field -Adjudicación
                    # Onsite Comment -take award_date only where the field name "Documento" > "Adjudicación" is written
                    
                try:
                    award_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Publicación en plataforma")]//following::div[1]').text
                    award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                    lot_details_data.lot_award_date = award_details_data.award_date
                except Exception as e:
                    logging.info("Exception in award_date: {}".format(type(e).__name__))
                    pass

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
        back_clk=WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#enlace_volver')))
        page_main.execute_script("arguments[0].click();",back_clk)
        WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="myTablaBusquedaCustom"]/tbody/tr'))).text
    except:
        pass
    time.sleep(5)
      
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
        time.sleep(3)
        index=[6,7,8,9]
        for i in index:
            select_fr = Select(page_main.find_element(By.XPATH,'//*[@id="viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:estadoLici"]'))
            select_fr.select_by_index(i)

            from_date=th.strftime('%d-%m-%Y')
            datefield1 = page_main.find_element(By.CSS_SELECTOR,'#viewns_Z7_AVEQAI930OBRD02JPMTPG21004_\:form1\:textMinFecAnuncioMAQ2').clear()
            time.sleep(2)
            datefield = page_main.find_element(By.CSS_SELECTOR,'#viewns_Z7_AVEQAI930OBRD02JPMTPG21004_\:form1\:textMinFecAnuncioMAQ2')
            datefield.click()
            datefield.send_keys(from_date)
            time.sleep(3)

            try:
                clk=  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:button1"]')))
                page_main.execute_script("arguments[0].click();",clk)
                time.sleep(5)
            except:
                pass
            try:
                for page_no in range(1,11):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="myTablaBusquedaCustom"]/tbody/tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="myTablaBusquedaCustom"]/tbody/tr')))
                    length = len(rows)
                    for records in range(1,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="myTablaBusquedaCustom"]/tbody/tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break

                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break
        

                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[@id='viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:footerSiguiente']")))
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
    
