from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_portaldecompras"
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
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_portaldecompras"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -# 1) go to the following url as follows : "https://www.portaldecompras.sc.gov.br/#/busca-detalhada"
# 2) select "Todas as situações" drop-down menu and go to  "publicado" option
# 3) then click on "Pesquisar"  below button 
    notice_data.script_name = 'br_portaldecompras'
    notice_data.main_language = 'PT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'BRL'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.notice_url = url
    
 
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -Descrição do Objeto
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Processo
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' th:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        publish_text =tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(5)').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_text)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date1: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_deadline =tender_html_element.find_element(By.CSS_SELECTOR, ' th:nth-child(6)').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline1: {}".format(type(e).__name__))
        pass
        
    try:              
        customer_details_data = customer_details()
        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(3)').text
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
            
        
    # Onsite Field -Natureza
    # Onsite Comment -split notice_contract_type from the given selector and Replace following keywords with given respective keywords ('Materiais = Supply ','Serviços = Service',' Alienações = Service', 'Obras = Works')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(2)').text
        if 'Materiais' in notice_data.notice_contract_type:
            notice_data.notice_contract_type='Supply'
        elif 'Serviços' in notice_data.notice_contract_type or 'Alienações' in notice_data.notice_contract_type:
            notice_data.notice_contract_type='Service'
        elif 'Obras' in notice_data.notice_contract_type:
            notice_data.notice_contract_type='Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'th:nth-child(8)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    if publish_text == "":
        try:
            icon_clk = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.icon'))).click()
            icon_clk = page_main.current_url
            notice_data.notice_url = "https://www.portaldecompras.sc.gov.br/#/pagina-documentos-edital/"+str(icon_clk.split('/')[-1].strip())+"/true"
            fn.load_page(page_details,notice_data.notice_url,180)
            page_details.refresh()
            time.sleep(5)
            WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'(//h5)[2]'))).text
            publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Data da Publicação")]//following::th[5]').text
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date2: {}".format(type(e).__name__))
            pass
        
        try:
            notice_deadline = page_main.find_element(By.XPATH, '//*[contains(text(),"Encerramento")]//following::th[3]').text
            notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline2: {}".format(type(e).__name__))
            pass
    
        try:
            back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[@class="icon"])[2]'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in back_clk: {}".format(type(e).__name__))
            pass
        try:
            drop_down = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > app-root > section.noprint > app-busca-detalhada > div > form > div.form > div:nth-child(4) > div'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in drop_down: {}".format(type(e).__name__))
            pass

        try:
            index_data = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Concluído")]//parent::span')))
            index_data.click()
            time.sleep(5)       
        except Exception as e:
            logging.info("Exception in index_data: {}".format(type(e).__name__))
            pass
        
        try:
            To_look_for = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Pesquisar")]//parent::span'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in To_look_for: {}".format(type(e).__name__))
            pass
        
    if index==list_index[1]:
        icon_clk = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.icon'))).click()
        icon_clk = page_main.current_url
        notice_data.notice_url = "https://www.portaldecompras.sc.gov.br/#/pagina-documentos-edital/"+str(icon_clk.split('/')[-1].strip())+"/true"
        fn.load_page(page_details,notice_data.notice_url,180)
        page_details.refresh()
        time.sleep(5)
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'(//h5)[2]'))).text

        
        try:
            back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/section[1]/app-pagina-processo/div/div[3]/div[6]/button[1]'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in back_clk2: {}".format(type(e).__name__))
            pass
        try:
            drop_down = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > app-root > section.noprint > app-busca-detalhada > div > form > div.form > div:nth-child(4) > div'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in drop_down2: {}".format(type(e).__name__))
            pass
        try:
            index_data = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Em andamento")]//parent::span')))
            index_data.click()
            time.sleep(5)       
        except Exception as e:
            logging.info("Exception in index_data2: {}".format(type(e).__name__))
            pass
        
        try:
            To_look_for = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Pesquisar")]//parent::span'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in To_look_for2: {}".format(type(e).__name__))
            pass
        
    elif index==list_index[2]:
        icon_clk = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.icon'))).click()
        icon_clk = page_main.current_url
        notice_data.notice_url = "https://www.portaldecompras.sc.gov.br/#/pagina-documentos-edital/"+str(icon_clk.split('/')[-1].strip())+"/true"
        fn.load_page(page_details,notice_data.notice_url,180)
        page_details.refresh()
        time.sleep(5)
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'(//h5)[2]'))).text

        
        try:
            back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/section[1]/app-pagina-processo/div/div[3]/div[6]/button[1]'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in back_clk3: {}".format(type(e).__name__))
            pass
        try:
            drop_down = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > app-root > section.noprint > app-busca-detalhada > div > form > div.form > div:nth-child(4) > div'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in back_clk3: {}".format(type(e).__name__))
            pass
        try:
            index_data = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Publicado")]//parent::span')))
            index_data.click()
            time.sleep(5)       
        except Exception as e:
            logging.info("Exception in index_data3: {}".format(type(e).__name__))
            pass
        
        try:
            To_look_for = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Pesquisar")]//parent::span'))).click()
            time.sleep(2)
        except Exception as e:
            logging.info("Exception in To_look_for3: {}".format(type(e).__name__))
            pass
        
    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Nome do Arquivo")]//following::tr'):
            attachments_data = attachments()
            
            external_url = single_record.text
            while True:
                external_url = single_record.find_element(By.CSS_SELECTOR, '''div.icon''').click()
                time.sleep(5)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url= (str(file_dwn[0]))
                time.sleep(5)
                break
                
            if attachments_data.external_url != '':
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, '''span.linkName''').text.split('.')[-1].strip()
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, '''span.linkName''').text.split(attachments_data.file_type)[0].strip()
                


            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
page_details = Doc_Download.page_details
page_details.maximize_window()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.portaldecompras.sc.gov.br/#/busca-detalhada"] 
    for url in urls:
        fn.load_page_expect_xpath(page_main, url, '//*[@id="mat-option-1"]/span')
        logging.info('----------------------------------')
        logging.info(url)
        
        
        list_index = ['Concluído','Em andamento','Publicado']
        for index in list_index:
        
            try:
                drop_down = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > app-root > section.noprint > app-busca-detalhada > div > form > div.form > div:nth-child(4) > div'))).click()
                time.sleep(2)
            except:
                pass

            try:
                index_data = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"'+index+'")]//parent::span')))
                index_data.click()
                time.sleep(5)       
            except:
                pass
            try:
                To_look_for = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Pesquisar")]//parent::span'))).click()
                time.sleep(2)
            except:
                pass

            try:
                for page_no in range(1,10):#10
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/section[1]/app-busca-detalhada/div/div/div[1]/div/table/tbody/tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/section[1]/app-busca-detalhada/div/div/div[1]/div/table/tbody/tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/section[1]/app-busca-detalhada/div/div/div[1]/div/table/tbody/tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#paginationDesktop > div > div:nth-child(3) > mat-icon')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/section[1]/app-busca-detalhada/div/div/div[1]/div/table/tbody/tr'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
            
            
                    try:
                        new_search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//button[1])[1]')))
                        page_main.execute_script("arguments[0].click();",new_search)
                        time.sleep(5)
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'body > app-root > section.noprint > app-busca-detalhada > div > form > div.form > div:nth-child(4) > div')))
                    except:
                        pass
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
