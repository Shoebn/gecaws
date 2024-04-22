from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_comprasnet"
log_config.log(SCRIPT_NAME)
import re
import jsons
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
SCRIPT_NAME = "br_comprasnet"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'br_comprasnet'
    notice_data.main_language = 'PT'  
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2   
    notice_data.notice_type = 4   
    notice_data.notice_url = url
    
    try:
        url1 = tender_html_element.find_element(By.CSS_SELECTOR, 'input.texfield2').get_attribute('onclick')
        url1=url1.split('?')[1].split("');")[0]
        notice_data.notice_url='http://comprasnet.gov.br/ConsultaLicitacoes/download/download_editais_detalhe.asp?'+url1
        fn.load_page(page_details,notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
                                                                    
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "tr:nth-child(2) > td.tex3 > table > tbody").text.split('Entrega da Proposta:')[1]
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
     
    try:
        res=page_details.find_element(By.XPATH, '/html/body/table[2]/tbody/tr[2]/td/table[2]/tbody').text
    except:
        pass
        
    try:
        notice_data.notice_no=page_details.find_element(By.CSS_SELECTOR,' tr > td > p > span.mensagem').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td.tex3 > table').text
        notice_data.notice_summary_english = GoogleTranslator(source='pt', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text = page_details.find_element(By.XPATH, '/html/body/table[2]/tbody/tr[2]/td/table[2]').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr:nth-child(2) > td > table:nth-child(2)'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'BR'
    
            try:
                customer_details_data.org_name = single_record.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(2) > td > table:nth-child(2) > tbody > tr:nth-child(1) table > tbody > tr:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_fax = single_record.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td.tex3 > table > tbody').text.split('Fax:')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_address = single_record.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(2) > td > table:nth-child(2) > tbody > tr:nth-child(2) > td.tex3').text.split('Endereço:')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.org_phone = single_record.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(2) > td > table:nth-child(2) > tbody > tr:nth-child(2) > td.tex3').text.split('Telefone:')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_title=fn.get_string_between(res,'Objeto:','Edital a partir de:')
        notice_data.notice_title = GoogleTranslator(source='pt', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = fn.get_string_between(res,'Objeto:','Edital a partir de:').split(':')[1].split('-')[0].strip()
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
        
    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > table:nth-child(3) > tbody > tr:nth-child(2) > td > table:nth-child(2) > tbody > tr:nth-child(3) > td.tex3 > table > tbody > tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            
            lot_details_data.lot_title=single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2) > span.tex3b').text
            lot_details_data.lot_title_english = GoogleTranslator(source='pt', target='en').translate(lot_details_data.lot_title)  
            
            try:                                                                                                                             #Unidade de fornecimento:
                lot_details_data.lot_quantity=float(single_record.find_element(By.CSS_SELECTOR,'tbody > tr td:nth-child(2) > span.tex3').text.split('Quantidade:')[1].split('\n')[0])  
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass
    
    page_main.refresh()   
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    fromth = th.strftime("%d/%m/%Y")
    toth = date.today().strftime("%d/%m/%Y")
    try:
        for page in range(1,100):
            url='http://comprasnet.gov.br/ConsultaLicitacoes/ConsLicitacao_Relacao.asp?numprp=&dt_publ_ini='+str(fromth)+'&dt_publ_fim='+str(toth)+'&chkModalidade=1,2,3,20,5,99&chk_concor=31,32,41,42,49&chk_pregao=1,2,3,4&chk_rdc=1,2,3,4&optTpPesqMat=M&optTpPesqServ=S&chkTodos=-1&chk_concorTodos=-1&chk_pregaoTodos=-1&txtlstUf=&txtlstMunicipio=&txtlstUasg=&txtlstGrpMaterial=&txtlstClasMaterial=&txtlstMaterial=&txtlstGrpServico=&txtlstServico=&txtObjeto=&numpag='+str(page)+''     
            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url)
            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table[2]/tbody/tr[3]/td[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table[2]/tbody/tr[3]/td[2]/form')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table[2]/tbody/tr[3]/td[2]/form')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                   
                    if notice_count == 50:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
            except:
                logging.info('No new record')
                break
    except Exception as e:
        logging.info("Exception in page_num : {}".format(type(e).__name__))
        pass

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
