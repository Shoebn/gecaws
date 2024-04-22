#NOTE- click on "RDO Aperte(0)" 
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_acquistinretepaopen_spn"
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
import gec_common.Doc_Download_VPN
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_acquistinretepaopen_spn"
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_acquistinretepaopen_spn'

    notice_data.currency = 'EUR'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'IT'
    
    # Onsite Field -N.GARA
    # Onsite Comment -also take notice_no from notice url
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -BANDO
    # Onsite Comment -None
    
    # Onsite Field -AREA MERCEOLOGICA
    # Onsite Comment -None

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data e ora inizio presentazione offerte
    
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-1.ng-scope > div > div').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div > p > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
         

    try:
        published_date = WebDriverWait(page_details, 20).until(EC.presence_of_element_located((By.XPATH, "(//*[contains(text(),'Data e ora inizio presentazione offerte')])[2]//following::p[1]"))).text
        p_date = re.findall('\d+/\d+/\d{4}',published_date)[0]
        publish_time = re.findall('\d+:\d+',published_date)[0]
        publish_date = p_date + ' ' + publish_time
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        deadline = page_details.find_element(By.XPATH, "(//*[contains(text(),'Data e ora termine ultimo ricezione offerte')])[2]//following::p[1]").text
        deadline_date = re.findall('\d+/\d+/\d{4}',deadline)[0]
        deadline_time = re.findall('\d+:\d+',deadline)[0]
        notice_deadline = deadline_date + ' ' + deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -SCADE IL
    # Onsite Comment -None
    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div.titoloiniziativa.col-sm-9.col-xs-12 > h1').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '''//*[contains(text(),'Descrizione RdO:')]//following::p''').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descrizione
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bandi/Categorie oggetto della RdO: ----------- split data from "Bandi/Categorie oggetto della RdO:" till "dash "-""
    # Onsite Comment -BENI- Supply, SERVIZI- Services 

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),'Bandi/Categorie ')]//following::p[1]''').text.split(' - ')[0].strip()
        if 'BENI' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'SERVIZI' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            pass    
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bandi/Categorie oggetto della RdO:
    # Onsite Comment -None

    
    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[3]/div"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#page-complete').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Ente committente:
    # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '''//*[contains(text(),'Ente committente:')]//following::p[1]''').text

        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#sezione_lotti > div.boxLottiBando.col-sm-12.col-xs-12.nopadding.margin-top-20.ng-scope.borderME-left > div > div'):
            if 'Lotto' in single_record.text:
                lot_number = 1
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

            # Onsite Field -CODICE CIG
            # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div > div:nth-child(2)').text
                notice_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                try:
                    lot_netbudget = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(5)').text
                    lot_netbudget = re.sub("[^\d\.\,]","",lot_netbudget)
                    lot_details_data.lot_netbudget = float(lot_netbudget.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
                except Exception as e:
                    logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
            else:
                lot_number = 1
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
            # Onsite Field -None
            # Onsite Comment -None

                lot_details_data.lot_title = notice_data.local_title
                notice_data.is_lot_default = True
                lot_details_data.lot_title_english = notice_data.notice_title
            # Onsite Field -CODICE CIG
            # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -None
            # Onsite Comment -None

                try:
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                except Exception as e:
                    logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                    pass

        # Onsite Field -Bandi/Categorie oggetto della RdO: ----------- split data from "Bandi/Categorie oggetto della RdO:" till "dash "-""
        # Onsite Comment -BENI- Supply, SERVIZI- Services 

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass


                try:
                    lot_netbudget = single_record.find_element(By.CSS_SELECTOR,'div:nth-child(4)').text
                    lot_netbudget = re.sub("[^\d\.\,]","",lot_netbudget)
                    lot_details_data.lot_netbudget = float(lot_netbudget.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
                except Exception as e:
                    logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    
# ********************************************---FORMAT - 1****************************************************************

    try:  
        document_scroll = page_details.find_element(By.XPATH,'//*[@id="all-page"]/div[3]/div/div/div/div[7]/div[1]')
        page_details.execute_script("arguments[0].scrollIntoView(true);", document_scroll)
        time.sleep(4)
            
        document_click = WebDriverWait(page_details, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#all-page > div:nth-child(3) > div > div > div > div:nth-child(7) > div.col-sm-5.col-lg-4.col-xs-12.semibold.docGara.cursor.ng-scope.borderTab')))
        page_details.execute_script("arguments[0].click();",document_click)
        time.sleep(10)
                                                                                                                        #all-page > div:nth-child(3) > div > div > div > div:nth-child(6) > div:nth-child(3) > div
        for single_record in WebDriverWait(page_details, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#all-page > div:nth-child(3) > div > div > div > div:nth-child(7) > div:nth-child(3) > div'))):
            attachments_data = attachments()
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span > strong').text
        
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            external_url = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span ').click()
            time.sleep(2)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span > div').text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
        try:
            document_scroll = page_details.find_element(By.XPATH,'//*[@id="all-page"]/div[3]/div/div/div/div[6]/div[1]')
            page_details.execute_script("arguments[0].scrollIntoView(true);", document_scroll)
            time.sleep(4)
            
            document_click = WebDriverWait(page_details, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#all-page > div:nth-child(3) > div > div > div > div:nth-child(6) > div.col-sm-5.col-lg-4.col-xs-12.semibold.docGara.cursor.ng-scope.borderTab')))
            page_details.execute_script("arguments[0].click();",document_click)
            time.sleep(10)
                                                                                                                            
            for single_record in WebDriverWait(page_details, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#all-page > div:nth-child(3) > div > div > div > div:nth-child(6) > div:nth-child(3) > div'))):
                attachments_data = attachments()
            # Onsite Field -click on "RICHIESTE PARTECIPANTI"
            # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span > strong').text

            # Onsite Field -click on "RICHIESTE PARTECIPANTI"
            # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

                external_url = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span ').click()
                time.sleep(2)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])


            # Onsite Field -click on "RICHIESTE PARTECIPANTI"
            # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span > div').text.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        
# ********************************************---FORMAT - 2****************************************************************
    
    try:                                                                                    
        attchment_click = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#all-page > div:nth-child(3) > div > div > div > div:nth-child(7) > div:nth-child(2)')))
        page_details.execute_script("arguments[0].click();",attchment_click)
        time.sleep(4)
        
        for single_record in WebDriverWait(page_details, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#all-page > div:nth-child(3) > div > div > div > div:nth-child(7) > div:nth-child(3) > div'))):
            attachments_data = attachments()
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span > strong').text
  
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            external_url = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span ').click()
            time.sleep(2)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span > div').text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
        try:
            attchment_click = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#all-page > div:nth-child(3) > div > div > div > div:nth-child(6) > div:nth-child(2)')))
            page_details.execute_script("arguments[0].click();",attchment_click)
            time.sleep(4)

            for single_record in WebDriverWait(page_details, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#all-page > div:nth-child(3) > div > div > div > div:nth-child(6) > div:nth-child(3) > div'))):
                attachments_data = attachments()
            # Onsite Field -click on "RICHIESTE PARTECIPANTI"
            # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span > strong').text

            # Onsite Field -click on "RICHIESTE PARTECIPANTI"
            # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

                external_url = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span ').click()
                time.sleep(2)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])


            # Onsite Field -click on "RICHIESTE PARTECIPANTI"
            # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span > div').text.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=AB#!/%23post_call_position#post_call_position"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        rdo_aperte_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#checkbox3')))
        page_main.execute_script("arguments[0].click();",rdo_aperte_click)
        time.sleep(10)
        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div '))).text
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div ')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div ')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div '),page_check))
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
