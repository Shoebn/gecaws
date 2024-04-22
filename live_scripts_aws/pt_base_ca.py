
#click on "Pesquisa avançada" next >>>  click on Contrats(contracts) from top left box>>> select dates "Data da publicação" >>> next click on "Pesquisar"

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pt_base_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "pt_base_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()

    notice_data.script_name = 'pt_base_ca'
    notice_data.main_language = 'PT'
    notice_data.currency = 'EUR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.class_at_source = 'CPV'

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_no = notice_data.notice_url.split('&id=')[1].strip()
    except:
        pass
    # Onsite Field -Publicação
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Objeto do contrato
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo de procedimento
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.type_of_procedure = fn.procedure_mapping("assets/pt_base_ca_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Preço contratual
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try: 
        notice_data.local_description = page_details.find_element(By.XPATH, '''//*[contains(text(),'Descrição')]//following::td[4]''').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try: 
        notice_data.local_description += page_details.find_element(By.XPATH, '''//*[contains(text(),'Objeto do contrato')]//following::td[1]''').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Tipos de contrato
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),'Tipos de contrato')]//following::td[1]''').text
        contract_type_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        if "Acquisition of movable assets" in contract_type_actual or 'Leasing of movable assets' in contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Public works concession" in contract_type_actual or 'Public works contracts' in contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "Acquisition of services" in contract_type_actual or "Concession of public services" in contract_type_actual:
            notice_data.notice_contract_type = "Service"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.b-body-screen > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Peças do procedimento")])[3]//following::a[1]''').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__)) 
        pass

    try:             
        customer_details_data = customer_details()
        customer_details_data.org_country = 'PT'
        customer_details_data.org_language = 'PT' 
    # Onsite Field -Adjudicante
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        cpv_at_source = ''
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '''//*[contains(text(),'CPVs')]//following::td[1]''').text.split('-')[0].strip()
        cpv_at_source += cpvs_data.cpv_code
        cpv_at_source += ','
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    try:
        lots_url = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Peças do procedimento')])[3]//following::td/a''').get_attribute("href")          
        fn.load_page(page_details1,lots_url,80)
    except Exception as e:
        logging.info("Exception in lots_url: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_check = page_details1.find_element(By.CSS_SELECTOR, 'table#grdGridBasePriceLotList_tbl.VortalGrid > tbody > tr').text
        lot_number = 1
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'table#grdGridBasePriceLotList_tbl.VortalGrid > tbody > tr')[2:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
    # Onsite Field -Objeto do contrato
    # Onsite Comment -None
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td#grdGridBasePriceLotListtd_thColumnLotName').text

            try:
                lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td#grdGridBasePriceLotListtd_thColumnLotExpectedDuration').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
            
    # Onsite Field -Tipos de contrato
    # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
            try: 
                lot_award_date = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Data do contrato')]//following::td[1])[2]''').text
                lot_details_data.lot_award_date = datetime.strptime(lot_award_date, '%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                pass

            try: 
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '''//*[contains(text(),'CPVs')]//following::td[1]''').text.split('-')[0].strip()

                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)        
            except Exception as e:
                logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
                pass
        
            try:
                lot_cpv_at_source = ''
                lot_cpv_at_source = page_details.find_element(By.XPATH, '''//*[contains(text(),'CPVs')]//following::td[1]''').text.split('-')[0].strip()
                lot_details_data.lot_cpv_at_source = re.sub("[^\d]","",lot_cpv_at_source)
                notice_data.cpv_at_source += ','
                notice_data.cpv_at_source += lot_details_data.lot_cpv_at_source
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__)) 
                pass
        

            try:
                award_details_data = award_details()

                # Onsite Field -Adjudicatário
                # Onsite Comment -None

                award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

                # Onsite Field -Data do contrato
                # Onsite Comment -None
                try:
                    award_date = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Data do contrato')])[1]//following::td[17]''').text
                    award_date = re.findall('\d+-\d+-\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d-%m-%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in award_date: {}".format(type(e).__name__))
                    pass
                # Onsite Field -Prazo de execução
                # Onsite Comment -None

                # try:
                #     grossawardvalueeuro = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Preço contratual')]//following::td[1])[2]''').text
                #     grossawardvalueeuro = re.sub("[^\d\.\,]", "", grossawardvalueeuro)
                #     award_details_data.grossawardvalueeuro = float(grossawardvalueeuro.replace('.','').replace(',','.').strip())
                #     award_details_data.grossawardvaluelc = award_details_data.grossawardvalueeuro
                # except Exception as e:
                #     logging.info("Exception in grossawardvalueeuro: {}".format(type(e).__name__))
                #     pass

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            if lot_details_data.award_details !=[]:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
    except:
        try:
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
    # Onsite Field -Objeto do contrato
    # Onsite Comment -None

            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english = notice_data.notice_title
            
            try:
                lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td#grdGridBasePriceLotListtd_thColumnLotExpectedDuration').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

    # Onsite Field -Tipos de contrato
    # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
            try: 
                lot_award_date = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Data do contrato')]//following::td[1])[2]''').text
                lot_details_data.lot_award_date = datetime.strptime(lot_award_date, '%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Descrição')])[1]//following::td[4]''').text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            try: 
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '''//*[contains(text(),'CPVs')]//following::td[1]''').text.split('-')[0].strip()

                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)        
            except Exception as e:
                logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
                pass
        
            try:
                lot_cpv_at_source = ''
                lot_cpv_at_source = page_details.find_element(By.XPATH, '''//*[contains(text(),'CPVs')]//following::td[1]''').text.split('-')[0].strip()
                lot_details_data.lot_cpv_at_source = re.sub("[^\d]","",lot_cpv_at_source)
                notice_data.cpv_at_source += ','
                notice_data.cpv_at_source += lot_details_data.lot_cpv_at_source
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__)) 
                pass
        

            try:
                award_details_data = award_details()

                # Onsite Field -Adjudicatário
                # Onsite Comment -None

                award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

                # Onsite Field -Data do contrato
                # Onsite Comment -None
                try:
                    award_date = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Data do contrato')])[1]//following::td[17]''').text
                    award_date = re.findall('\d+-\d+-\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d-%m-%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in award_date: {}".format(type(e).__name__))
                    pass
                # Onsite Field -Prazo de execução
                # Onsite Comment -None

                # try:
                #     grossawardvalueeuro = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Preço contratual')]//following::td[1])[2]''').text
                #     grossawardvalueeuro = re.sub("[^\d\.\,]", "", grossawardvalueeuro)
                #     award_details_data.grossawardvalueeuro = float(grossawardvalueeuro.replace('.','').replace(',','.').strip())
                #     award_details_data.grossawardvaluelc = award_details_data.grossawardvalueeuro
                # except Exception as e:
                #     logging.info("Exception in grossawardvalueeuro: {}".format(type(e).__name__))
                #     pass

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            if lot_details_data.award_details !=[]:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
    
    # Onsite Field -CPVs
    # Onsite Comment -None


    try:              
        attachments_data = attachments()
    # Onsite Field -Documentos
    # Onsite Comment -None

        attachments_data.file_name = page_details.find_element(By.XPATH, '''//*[contains(text(),'Documentos')]//following::td[1]''').text.split('.')[0].strip()
    # Onsite Field -Documentos
    # Onsite Comment -None

        try:
            attachments_data.file_type = page_details.find_element(By.XPATH, '''//*[contains(text(),'Documentos')]//following::td[1]''').text.split('.')[1].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass


    # Onsite Field -Documentos
    # Onsite Comment -None

        attachments_data.external_url = page_details.find_element(By.XPATH, '''//*[contains(text(),'Documentos')]//following::td[1]/a''').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) +str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments)
 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos&texto=&tipo=0&tipocontrato=0&cpv=&aqinfo=&adjudicante=&adjudicataria=&sel_price=price_c1&desdeprecocontrato=&ateprecocontrato=&desdeprecoefectivo=&ateprecoefectivo=&desdeprazoexecucao=&ateprazoexecucao=&sel_date=date_c1&desdedatacontrato=&atedatacontrato=&desdedatapublicacao=&atedatapublicacao=&desdedatafecho=&atedatafecho=&pais=0&distrito=0&concelho=0"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="advanced_contratos"]'))).click()
        time.sleep(2) 
        
        pp_btn = Select(page_main.find_element(By.XPATH,'//*[@id="sel_date"]')) 
        pp_btn.select_by_index(1) 
        time.sleep(5) 
        
        date_data = th.strftime('%Y-%m-%d')
        yest_date = page_main.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div/div/div/form[1]/div[2]/div[2]/div[2]/div[7]/div/input[1]').clear()
        yest_date = page_main.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div/div/div/form[1]/div[2]/div[2]/div[2]/div[7]/div/input[1]').send_keys(date_data)
        time.sleep(5)
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search_contratos2"]'))).click()
        time.sleep(2)
        
        try:
            for page_no in range(1,100):#100
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="no-more-tables-mx767"]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="no-more-tables-mx767"]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="no-more-tables-mx767"]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                    if notice_count == 50:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'''//*[@id="page_'''+str(page_no)+'''"]''')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="no-more-tables-mx767"]/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    page_details1.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
