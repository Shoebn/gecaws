from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_novara_archive_ca"
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
SCRIPT_NAME = "it_novara_archive_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_novara_archive_ca'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7

# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []

    # Onsite Field -Titolo :
    # Onsite Comment -None

    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text.split("Titolo :")[1].strip()
        if " CUP:" in local_title or "CIG:" in local_title or " CIG"  in local_title:
            notice_data.local_title = local_title.split("CUP:")[0].split("CIG:")[0].split("CIG")[0].strip()
        else:
            notice_data.local_title = local_title
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.split("Tipologia appalto :")[1].strip()
        if "Servizi" in notice_contract_type:
            notice_data.notice_contract_type="Service"
        elif  "Lavori" in notice_contract_type:
            notice_data.notice_contract_type="Works"
        elif  "Forniture" in notice_contract_type:
            notice_data.notice_contract_type="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tipologia appalto :
    # Onsite Comment -

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.split("Tipologia appalto :")[1].strip()
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CIG:
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.text.split("CIG : ")[1].split("\n")[0].strip()
    except:
        try:
            notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text.split("Titolo :")[1].split("CIG")[1].strip()
            notice_data.notice_no = re.findall('[A-Za-z\d]+',notice_no)[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
            
    # Onsite Field -Data pubblicazione esito :
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.text.split("Data pubblicazione esito :")[1].split("\n")[0]
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Stato :
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.text.split("Stato :")[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Riferimento procedura :
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.text.split("Riferimento procedura :")[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -add also this clicks in notice_text:1)click on "div.list-action > a.bkg.table" in tender_html_element."main > div > div" use this selector for notice_text. 2)click on "//*[contains(text(),'Lotti')]//following::a[1]" and "//*[contains(text(),'Altri atti e documenti')]" in page_details."main > div > div" use this selector for notice_text.
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"URL di Pubblicazione su www.serviziocontrattipubblici.it")]//following::td[17]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'
    
    
    notice_data.class_at_source = "CPV"
    
    try:
        CPV_URLS = WebDriverWait(tender_html_element, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.list-action > a.bkg.table'))).get_attribute("href")                     
        logging.info(CPV_URLS)
        fn.load_page(page_details1,CPV_URLS,100)
        time.sleep(3)
    except:
        pass

    try:              
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get cpv_details.

        cpv_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
        cpv_code = re.findall('\d{8}',cpv_code)[0]
        cpvs_data = cpvs()
        cpvs_data.cpv_code = cpv_code

        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__))
        pass
    
      # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
    # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get lot_cpv_details.

    try:
        cpv_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
        cpv_at_source = re.findall('\d{8}',cpv_code)[0]
        notice_data.cpv_at_source = cpv_at_source
        logging.info(notice_data.cpv_at_source)
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'COMUNE DI NOVARA'
        customer_details_data.org_parent_id = '1335742'
        customer_details_data.org_language = 'IT'
        customer_details_data.org_country = 'IT'
        # Onsite Field -Responsabile unico procedimento :
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[3]/div[2]').text.split("RUP :")[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        # Onsite Field -Tipo di Amministrazion
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element.

        try:
            customer_details_data.type_of_authority_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione")]//following::td[4]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Comune Sede di Gara
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element.

        try:
            customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Comune Sede di Gara")]//following::td[6]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Indirizzo Sede di Gara
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element.

        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Indirizzo Sede di Gara")]//following::td[7]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div:nth-child(7) > ul > li > a'))).get_attribute("href")                     
        logging.info(lot_url)
        fn.load_page(page_details2,lot_url,100)
        time.sleep(3)
    except:
        pass
    
# Onsite Field -None
# Onsite Comment -click on "//*[contains(text(),'Lotti')]//following::a[1]" in page_details to take lot_details.
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number= 1
        # Onsite Field -Titolo :
        # Onsite Comment -1.split after "CIG :".

        try:
            lot_details_data.lot_actual_number = page_details2.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(2)').text.split("CIG:")[1].strip()
        except Exception as e:
            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
            pass

        # Onsite Field -Titolo :
        # Onsite Comment -1.split after "Titolo :".

        lot_details_data.lot_title = page_details2.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(2)').text.split("Titolo :")[1].split("CIG:")[0].strip()

        # Onsite Field -Importo a base di gara : 
        # Onsite Comment -1.split after "Importo a base di gara : ".

        try:
            lot_netbudget_lc = page_details2.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(3)').text.split("Importo a base di gara :")[1].strip()
            lot_netbudget_lc = re.sub("[^\d\.\,]","",lot_netbudget_lc)
            lot_details_data.lot_netbudget_lc =float(lot_netbudget_lc.replace('.','').replace(',','.').strip())
        except Exception as e:
            logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
            pass

        # Onsite Field -Importo a base di gara : 
        # Onsite Comment -1.split after "Importo a base di gara : ".

        lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc

        # Onsite Field -Tipologia appalto :
        # Onsite Comment -split after "Tipologia appalto :"

        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual

        # Onsite Field -Tipologia appalto :
        # Onsite Comment -1)split after "Tipologia appalto :".	2)Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply','Altro = pass none')

        lot_details_data.contract_type = notice_data.notice_contract_type

        # Onsite Field -Data aggiudicazione :
        # Onsite Comment -None

        try:
            lot_award_date = page_details2.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(6)').text
            lot_award_date = re.findall('\d+/\d+/\d{4}',lot_award_date)[0]
            lot_details_data.lot_award_date = datetime.strptime(lot_award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
            pass

        award_details_data = award_details()

    # Onsite Field -Ditta aggiudicataria :
    # Onsite Comment -None

        award_details_data.bidder_name = page_details2.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(4)').text.split("Ditta aggiudicataria :")[1].strip()
        award_details_data.award_date = lot_details_data.lot_award_date

    # Onsite Field -Importo aggiudicazione :
    # Onsite Comment -None

        try:
            netawardvaluelc = page_details2.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(5)').text.split("Importo aggiudicazione :")[1].strip()
            netawardvaluelc = re.sub("[^\d\.\,]","",netawardvaluelc)
            award_details_data.netawardvaluelc =float(netawardvaluelc.replace('.','').replace(',','.').strip())
            award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
        except Exception as e:
            logging.info("Exception in netawardvaluelc: {}".format(type(e).__name__))
            pass


        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    
# Onsite Field -None
# Onsite Comment -take attachments after clicking on "div:nth-child(8) > ul > li > a (Atti e documenti)" in page detils
    try:
        attach = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li > a').get_attribute('href')
        if "downloadDocumentoPubblico.action" in attach:
            try:              
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li > a'):
                    attachments_data = attachments()
                # Onsite Field -Documentazione esito di gara
                # Onsite Comment -1.take in text format.
    
                    attachments_data.file_name = single_record.text
    
                # Onsite Field -Documentazione esito di gara
                # Onsite Comment -None
    
                    attachments_data.external_url = single_record.get_attribute('href')
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
                pass
        else:
            attach_url_click = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li > a'))).get_attribute("href")                     
            logging.info(attach_url_click)
            fn.load_page(page_details4,attach_url_click,100)
            time.sleep(3)
            
            try:              
                for single_record in page_details4.find_elements(By.CSS_SELECTOR, 'div.dettaglio-pratica-rght.span6 > table > tbody > tr')[1:]:
                    attachments_data = attachments()
                # Onsite Field -Documentazione esito di gara
                # Onsite Comment -1.take in text format.
    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text
                    
                # Onsite Field -Documentazione esito di gara
                # Onsite Comment -None
    
                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute('href')
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
                pass
    except:
        pass

    try:
        action_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li > form'))).get_attribute("action")                     
        logging.info(action_url)
        fn.load_page(page_details5,action_url,100)

        try:              
            for single_record in page_details5.find_elements(By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li > a'):
                attachments_data = attachments()
            # Onsite Field -Documentazione esito di gara
            # Onsite Comment -1.take in text format.

                attachments_data.file_name = single_record.get_attribute('title')

            # Onsite Field -Documentazione esito di gara
            # Onsite Comment -None

                attachments_data.external_url = single_record.get_attribute('href')
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments5: {}".format(type(e).__name__)) 
            pass
        
    except:
        pass
    try:
        attach_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div:nth-child(8) > ul > li > a"))).get_attribute("href")                     
        logging.info(attach_url)
        fn.load_page(page_details3,attach_url,100)
        time.sleep(3)
    except:
        pass
    
    try:
        for single_record in page_details3.find_elements(By.CSS_SELECTOR, 'div.detail-section > div > ul > li > a '):
            attachments_data = attachments()
    # Onsite Field -Documentazione esito di gara
    # Onsite Comment -1.take in text format.

            attachments_data.file_name = single_record.text
           
        # Onsite Field -Documentazione esito di gara
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments3: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_details2 = fn.init_chrome_driver(arguments)
page_details3 = fn.init_chrome_driver(arguments)
page_details4 = fn.init_chrome_driver(arguments)
page_details5 = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = '2022/01/01'
    logging.info("Scraping from or greater than: " + threshold)
    
    urls = ["https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/listAllInCorso.action&currentFrame=7"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        page_main.find_element(By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/form[1]/fieldset/div[4]/div/img').click()
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="model.dataPubblicazioneDa"]').send_keys('01/01/2022')
        time.sleep(2)
        page_main.find_element(By.XPATH,'//*[@id="model.dataPubblicazioneA"]').send_keys('15/12/2023')
        time.sleep(2)
        page_main.find_element(By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/form[1]/fieldset/div[6]/input[1]').click()
        time.sleep(5)
        for page_no in range(1,300):#5
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
                extract_and_save_notice(tender_html_element)

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#pagination-navi > input.nav-button.nav-button-right")))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.list-item'),page_check))
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
    page_details1.quit()
    page_details2.quit()
    page_details3.quit()
    page_details4.quit()
    page_details5.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)