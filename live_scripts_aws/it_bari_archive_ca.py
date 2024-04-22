from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_bari_archive_ca"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "it_bari_archive_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
   
    notice_data.script_name = 'it_bari_archive_ca'
    notice_data.main_language = 'IT'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.currency = 'EUR'
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'
    
#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


#2)for cpv
#Case 1 : Tender CPV given, but lot CPV not given, than it will not be repeated in Lots.
#Case 2: Tender CPV not given, lots CPV Given. it will be repeated in Tender CPV comma separated.
#Case 3: Tender CPV given, lot CPV also given, In this case also lot CPVs will be repeated in Tender CPV comma separated. But in this make sure that Tender CPV should be first followed by lot CPVs.


    # Onsite Field -Titolo :
    # Onsite Comment -1.split after "Titolo : ".
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    #click on "div.list-action > a.bkg.table" in tender_html_element to get additional_tender_url.
    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> URL DI PUBBLICAZIONE SU WWW.SERVIZIOCONTRATTIPUBBLICI.IT
    # Onsite Comment -None
    try:
        notice_data.notice_no = tender_html_element.text.split("CIG : ")[1].split("\n")[0].strip().strip()
    except:
        try:
            notice_data.notice_no = tender_html_element.text.split("CIG ")[1].split("\n")[0].strip().strip()
        except:
            pass

        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text.split("Titolo :")[1].strip()
        notice_data.local_title = notice_data.local_title.lower()
        if 'cig' in notice_data.local_title:
            notice_data.local_title = notice_data.local_title.split('cig')[0]
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -1.split after "Tipologia appalto : "	2.Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply').

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.split("Tipologia appalto :")[1].strip()
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione esito :
    # Onsite Comment -1.split after "Data pubblicazione esito :".

    try:
        publish_date = tender_html_element.text.split('Data pubblicazione esito :')[1].split('\n')[0]
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Riferimento procedura :
    # Onsite Comment -1.split after "Riferimento procedura :".

    try:
        notice_data.related_tender_id = tender_html_element.text.split("Riferimento procedura :")[1].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Stato :
    # Onsite Comment -1.split after "Stato :".

    try:
        notice_data.document_type_description = tender_html_element.text.split('Stato :')[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ext-container > div.container.two-columns-right-menu > div > div.column.content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bkg.table').get_attribute("href")                     
        fn.load_page(page_details1,notice_url,80)
        logging.info(notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))

    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#ext-container > div.container.two-columns-right-menu > div > div.column.content > div').get_attribute("outerHTML")                     
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        # Onsite Field -Stazione appaltante :
        # Onsite Comment -1.split after "Stazione appaltante :".

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(1)').text.split("Stazione appaltante :")[1].strip()
        
        # Onsite Field -RUP :
        # Onsite Comment -1.split after "RUP :".

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Stazione appaltante")]//following::div[2]').text.split("RUP : ")[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> TIPO DI AMMINISTRAZIONE
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get type_of_authority_code.

        try:
            customer_details_data.type_of_authority_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione")]//following::td[4]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> COMUNE SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get type_of_authority_code.

        try:
            customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Comune Sede di Gara")]//following::td[6]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> INDIRIZZO SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get type_of_authority_code.

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

        #if "#tableIndicizzazione > tbody > tr > td:nth-child(8)" in this field "SI" is given then take the amount under "VALORE IMPORTO A BASE ASTA" field grab in netbudgetlc and netbudgeteuro.  and if "#tableIndicizzazione > tbody > tr > td:nth-child(8)" in this field "NO" is given then take the amount under "VALORE IMPORTO A BASE ASTA" field grab in grossbudgetlc and grossbudgeteuro.    
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
        # Onsite Comment -if "SENZA IMPORTO" under this field "NO" is given then only grab the amount.

    try:
        Senza_Importo = page_details1.find_element(By.XPATH, '//*[contains(text(),"Senza Importo")]//following::td[8]').text
        est_amount_data = page_details1.find_element(By.XPATH, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount_data).replace('.','').replace(',','.').strip()
        notice_data.est_amount =float(est_amount)
        if 'NO' in Senza_Importo:
            if "€" in est_amount_data:
                notice_data.grossbudgetlc = notice_data.est_amount
                notice_data.grossbudgeteuro = notice_data.est_amount
        if 'SI' in Senza_Importo:
            if "€" in est_amount_data:
                notice_data.netbudgetlc = notice_data.est_amount
                notice_data.netbudgeteuro = notice_data.est_amount
    except:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#tableIndicizzazione > tbody > tr > td:nth-child(15)'):
            cpvs_data = cpvs()
            cpv_code = single_record.text
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        cpv_at_source = ''
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#tableIndicizzazione > tbody > tr > td:nth-child(15)'):
            cpv_code = single_record.text
            cpv_at_source += re.findall('\d{8}',cpv_code)[0]
            cpv_at_source += ','
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass

        #ref_url:"https://portaleappalti.comune.bari.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/view.action&currentFrame=7&codice=L23010&_csrf=CKWAEJN1M28YN55DTZ9KRYC821DQ12CF"
        # Onsite Field -Documentazione esito di gara
        # Onsite Comment -1.take in text format.

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            if 'javascript' in external_url:
                attachments2_url = single_record.find_element(By.CSS_SELECTOR, 'form').get_attribute("action")
                fn.load_page(page_details4,attachments2_url,80)
                try:
                    notice_data.notice_text += page_details4.find_element(By.CSS_SELECTOR, '#ext-container > div.container.two-columns-right-menu > div > div.column.content > div').get_attribute("outerHTML")                     
                except:
                    pass  
                for single_record in page_details4.find_elements(By.CSS_SELECTOR, 'div.detail-section.first-detail-section > div > ul > li > a'):
                    attachments_data = attachments()
                    attachments_data.external_url = single_record.get_attribute('href')
                    attachments_data.file_name = single_record.text
                    
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
                    
            else:
                attachments_data.external_url = external_url
                
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        attach_url = WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.LINK_TEXT, "Altri atti e documenti"))).get_attribute("href")                     
        logging.info(attach_url)
        fn.load_page(page_details2,attach_url,80)
        time.sleep(3)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#ext-container > div.container.two-columns-right-menu > div > div.column.content > div').get_attribute("outerHTML")                     
    except:
        pass
        
    # ref_url:"https://portaleappalti.comune.bari.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/view.action&currentFrame=7&codice=PN23022&_csrf=CKWAEJN1M28YN55DTZ9KRYC821DQ12CF"        
    #         Onsite Field -Documentazione esito di gara
    #         Onsite Comment -1.take in text format.

    try:
        for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'div.detail-section > div > ul > li > a'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_url = WebDriverWait(page_details, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div:nth-child(7) > ul > li > a'))).get_attribute("href")                     
        logging.info(lot_url)
        fn.load_page(page_details3,lot_url,80)
        time.sleep(3)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details3.find_element(By.CSS_SELECTOR, '#ext-container > div.container.two-columns-right-menu > div > div.column.content > div').get_attribute("outerHTML")                     
    except:
        pass
    
    try: 
        lot_number=1
        for single_record in page_details3.find_elements(By.CSS_SELECTOR, 'div.detail-section'):
            lot_details_data = lot_details() 
            lot_details_data.lot_number = lot_number

            lot_title = single_record.text.split("Titolo :")[1].split('\n')[0].strip()
            if 'CIG' in lot_title:
                lot_details_data.lot_title = lot_title.split('CIG')[0].strip()
            else:
                lot_details_data.lot_title = lot_title
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text.split("CIG:")[1].strip()
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            try:
                lot_grossbudget_data = single_record.text.split("Importo a base di gara :")[1].split("\n")[0].strip()
                if "€" in lot_grossbudget_data:
                    lot_grossbudget = lot_grossbudget_data.split("€")[0].strip()
                    lot_grossbudget = re.sub("[^\d\.\,]", "", lot_grossbudget)
                    lot_details_data.lot_netbudget_lc  = float(lot_grossbudget.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc 
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
            
            try:
                lot_award_date = single_record.text.split("Data aggiudicazione :")[1].split('\n')[0].strip()
                lot_award_date1 = datetime.strptime(lot_award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                lot_details_data.lot_award_date = lot_award_date1
            except:
                pass
                            
            try:
                for data in page_details1.find_elements(By.CSS_SELECTOR, '#tableIndicizzazione > tbody > tr'):
                    single_record1=data.text
                    if lot_details_data.lot_actual_number in single_record1 and lot_details_data.lot_actual_number != None and lot_details_data.lot_actual_number != '':

                        try:
                            contract_type = data.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                            lot_details_data.lot_contract_type_actual = contract_type
                            if 'SERVIZI' in contract_type:
                                lot_details_data.contract_type = 'Service'
                            elif ' LAVORI' in contract_type:
                                lot_details_data.contract_type = 'Works'
                            elif 'FORNITURE' in contract_type:
                                lot_details_data.contract_type = 'Supply'
                            else:
                                pass 
                        except Exception as e:
                            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                            pass

                        try:
                            for cpv in data.find_elements(By.CSS_SELECTOR, 'td:nth-child(15)'):
                                lot_cpvs_data = lot_cpvs()
                                lot_cpv_code = cpv.text
                                lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0] 
                                lot_cpvs_data.lot_cpvs_cleanup()
                                lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        except Exception as e:
                            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                            pass
                        try:
                            award_date = data.find_element(By.CSS_SELECTOR, 'td:nth-child(13)').text
                            award_date1 = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                        except:
                            pass
                        if 'lot_details_data.lot_award_date ' == '':

                            try:
                                lot_details_data.lot_award_date = lot_award_date1
                            except:
                                try:
                                    lot_details_data.lot_award_date = award_date1
                                except:
                                    pass
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            
            try:
                award_details_data = award_details()

                    # Onsite Field -Ditta aggiudicataria :
                    # Onsite Comment -1.split after "Ditta aggiudicataria :".
                
                award_details_data.bidder_name = single_record.text.split("Ditta aggiudicataria :")[1].split('\n')[0].strip()
                
                try:
                    grossawardvaluelc = single_record.text.split("Importo aggiudicazione :")[1].split('€')[0].strip()
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc).replace('.','').replace(',','.').strip()
                    grossawardvaluelc =float(grossawardvaluelc)
                    award_details_data.netawardvaluelc=grossawardvaluelc
                    award_details_data.netawardvalueeuro  = grossawardvaluelc
                except:
                    try:
                        grossawardvaluelc = data.find_element(By.CSS_SELECTOR, 'td:nth-child(10)').text
                        grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc).replace('.','').replace(',','.').strip()
                        grossawardvaluelc =float(grossawardvaluelc)
                        award_details_data.netawardvaluelc=grossawardvaluelc
                        award_details_data.netawardvalueeuro =grossawardvaluelc
                    except:
                        pass
                    
                try:
                    award_date = single_record.text.split("Data aggiudicazione :")[1].split('\n')[0].strip()
                    award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                except:
                    try:
                        award_details_data.award_date = award_date1
                    except:
                        pass
                    
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
                
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details2 = fn.init_chrome_driver(arguments)
page_details3 = fn.init_chrome_driver(arguments)
page_details4 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://portaleappalti.comune.bari.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/listAllInCorso.action&currentFrame=7"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        page_main.find_element(By.XPATH,'//*[@id="ext-container"]/div[7]/div/div[1]/div[2]/form[1]/fieldset/div[4]/div/img').click()
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="model.dataPubblicazioneDa"]').send_keys('01/01/2022')
        time.sleep(2)
        page_main.find_element(By.XPATH,'//*[@id="model.dataPubblicazioneA"]').send_keys('06/11/2023')
        time.sleep(2)
        DisplayLength = Select(page_main.find_element(By.CSS_SELECTOR,'#model\.iDisplayLength'))
        DisplayLength.select_by_index(3)
        time.sleep(2)
        page_main.find_element(By.XPATH,'//*[@id="ext-container"]/div[7]/div/div[1]/div[2]/form[1]/fieldset/div[6]/input[1]').click()
        time.sleep(5)
        for page_no in range(1,200):
            page_check = WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count == 50:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0
                
            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR ,"#pagination-navi > input.nav-button.nav-button-right")))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.list-item'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
