from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_sicilia_archive_ca"
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
SCRIPT_NAME = "it_sicilia_archive_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_sicilia_archive_ca'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7


#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []
    
    # Onsite Field -Titolo :
    # Onsite Comment -1.split after "Titolo : ".

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text.split(':')[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -1.split after "Tipologia appalto :".

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.split(':')[1].strip()
        if "Servizi" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Service"
        elif "Lavori" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Works"
        elif "Forniture" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -add also this clicks in notice_text:	1)"//*[contains(text(),'Lotti')]//following::a[1]" ,"//*[contains(text(),'Altri atti e documenti')]" and "Bando di gara" from page_details.
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.portgare-view').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

#ref_url:"https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/view.action&currentFrame=7&codice=G00568&_csrf=C31Y91CUL02YSS1EX3GR77LU5GG22P8A"    
    # Onsite Field -Titolo :
    # Onsite Comment -1.split after "CIG:"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Dati generali")]//following::div[1]').text.split('CIG:')[1].split('-')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione esito :
    # Onsite Comment -1.split after "Data pubblicazione esito :"

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Dati generali")]//following::div[3]').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Riferimento procedura :
    # Onsite Comment -1.split after "Riferimento procedura :".

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Dati generali")]//following::div[5]').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Stato :
    # Onsite Comment -1.split_after "Stato : ".

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Dati generali")]//following::div[4]').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
    # Onsite Field -Stazione appaltante :
    # Onsite Comment -1.split after "Stazione appaltante :".

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(1)').text.split(':')[1].strip()
    # Onsite Field -RUP :
    # Onsite Comment -1.split after "RUP :".

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"RUP : ")]/..').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.detail-section.last-detail-section > div > ul > li > a'):
            attachments_data = attachments()
        # Onsite Field -Documentazione esito di gara
        # Onsite Comment -None

            attachments_data.file_name = single_record.text
        # Onsite Field -Documentazione esito di gara
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        Lotti_url = page_details.find_element(By.XPATH, "(//*[contains(text(),'Lotti')])[2]").get_attribute("href")                     
        fn.load_page(page_details1,Lotti_url,80)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'div.column.content').get_attribute("outerHTML")                     
    except:
        pass
    
    try:    
        est_amount = page_details1.find_element(By.XPATH, '''//*[contains(text(),"Dati procedura o lotti")]//following::div[2]''').text.split(":")[1].split('€')[0].strip()
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc  = notice_data.est_amount
        notice_data.netbudgeteuro  = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in notice_data.netbudgetlc: {}".format(type(e).__name__))
        pass
        
    

#here are 2 ref_url for lot_details.	1)"https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewLotti.action&currentFrame=7&codice=G00568&ext=&_csrf=ERBZGNBTPR3XCOUU6P4NIXDVFT3M6HUM"	2)"https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewLotti.action&currentFrame=7&codice=G00581&ext=&_csrf=C2ILT0H3NE031GZP1ZR2GCF0YT7X102R"    
# Onsite Field -None
# Onsite Comment -None
                 
    lots = page_details1.find_element(By.XPATH, '//*[contains(text(),"Dati procedura o lotti")]//following::div[1]').text
    if 'CIG' in lots:
        try:
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
    
    
    #format-1	ref_url:"https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewLotti.action&currentFrame=7&codice=G00568&ext=&_csrf=ERBZGNBTPR3XCOUU6P4NIXDVFT3M6HUM"            
        # Onsite Field -None
        # Onsite Comment -1.split after "CIG:".
    
            lot_actual = page_details1.find_element(By.XPATH, '//*[contains(text(),"Dati procedura o lotti")]//following::div[1]').text
            if 'CIG :' in lot_actual:
                cig_numbers = re.findall(r'CIG : ([A-Z0-9]+)', lot_actual)[0]
                lot_details_data.lot_actual_number= cig_numbers
        # Onsite Field -Titolo :
        # Onsite Comment -1.split after "Titolo :"
    
            lot_details_data.lot_title = page_details1.find_element(By.XPATH, '//*[contains(text(),"Dati procedura o lotti")]//following::div[1]').text.split(':')[1].strip()
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
            lot_details_data.contract_type = notice_data.notice_contract_type
        # Onsite Field -Importo a base di gara :
        # Onsite Comment -1.split after "Importo a base di gara : "
    
            try:
                lot_grossbudget = page_details1.find_element(By.XPATH, '//*[contains(text(),"Dati procedura o lotti")]//following::div[2]').text
                lot_grossbudget = re.sub("[^\d\.\,]", "", lot_grossbudget)
                lot_details_data.lot_netbudget = float(lot_grossbudget.replace('.','').replace(',','.').strip())
                lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
    
        # Onsite Field -None16.190.540,06 €
        # Onsite Comment -None
    
            try:
                award_details_data = award_details()
    
                # Onsite Field -Ditta aggiudicataria :
                # Onsite Comment -1.split after "Ditta aggiudicataria :".
    
                award_details_data.bidder_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Dati procedura o lotti")]//following::div[3]').text.split(':')[1].strip()
                # Onsite Field -Data aggiudicazione :
                # Onsite Comment -1.split after "Data aggiudicazione : ".
                try:
                    award_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Data aggiudicazione :")]/..').text
                    award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                except:
                    pass
                # Onsite Field -Importo aggiudicazione :
                # Onsite Comment -1.split after "Importo aggiudicazione :".
                try:
                    grossawardvaluelc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Importo aggiudicazione : ")]/..').text.split(':')[1].strip()
                    grossawardvaluelc = re.sub("[^\d\.\,]", "", grossawardvaluelc)
                    award_details_data.netawardvaluelc = float(grossawardvaluelc.replace('.','').replace(',','.').strip())
                    award_details_data.netawardvalueeuro = award_details_data.grossawardvaluelc
                except:
                    pass
                # Onsite Field -Importo aggiudicazione :16.190.540,06 €
                # Onsite Comment -1.split after "Importo aggiudicazione :".
    
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details1: {}".format(type(e).__name__))
                pass
    
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details1: {}".format(type(e).__name__)) 
            pass
    else:
        try:
            lot_number = 1
            for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.detail-section.first-detail-section.last-detail-section')[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
    
    #format-2	ref_url:"https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewLotti.action&currentFrame=7&codice=G00581&ext=&_csrf=C2ILT0H3NE031GZP1ZR2GCF0YT7X102R"            
        # Onsite Field -None  # h3.detail-section-title
        # Onsite Comment -None
    
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text.split('CIG:')[1].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number2: {}".format(type(e).__name__))
                    pass
    
        # Onsite Field -Titolo :
        # Onsite Comment -1.split after "Titolo :".
    
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text.split(':')[1].split('- CIG')[0].strip()
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                try:
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except:
                    pass
        # Onsite Field -Importo a base di gara :
        # Onsite Comment -1.split after "Importo a base di gara :".
    
                try:
                    lot_grossbudget = page_details1.find_element(By.XPATH, '//*[contains(text(),"Importo a base di gara :")] /..').text.split(':')[1].strip()
                    lot_grossbudget = re.sub("[^\d\.\,]", "", lot_grossbudget)
                    lot_details_data.lot_netbudget = float(lot_grossbudget.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
                except Exception as e:
                    logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                    pass
    
    
                try:
                    award_details_data = award_details()
                    
                    # Onsite Field -Importo aggiudicazione :
                    # Onsite Comment -1.split after "Importo aggiudicazione :".
                
                    try:
                        grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(3)').text
                        grossawardvaluelc = re.sub("[^\d\.\,]", "", grossawardvaluelc)
                        award_details_data.netawardvaluelc = float(grossawardvaluelc.replace('.','').replace(',','.').strip())
                        award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc  
                    except:
                        pass

                    # Onsite Field -Ditta aggiudicataria :
                    # Onsite Comment -1.split after "Ditta aggiudicataria :".
                    try:
                        bidder_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div > div').text
                    except:
                        bidder_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(5)').text
                    
                    if ':' in bidder_name:
                        award_details_data.bidder_name = bidder_name.split(':')[1].split('\n')[0].strip()
                    else:
                        award_details_data.bidder_name = bidder_name.split('Ditte aggiudicatarie')[1].split('\n')[1].strip()
                    
                    # Onsite Field -Data aggiudicazione :
                    # Onsite Comment -1.split after "Data aggiudicazione :".
                    try:
                        award_date = page_details1.find_element(By.XPATH, '//*[contains(text(),"Dati procedura o lotti")]//following::div[4]').text.split(':')[1].strip()
                        award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                    except:
                        pass
                    

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
    
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
        except Exception as e:
            logging.info("Exception in lot_details2: {}".format(type(e).__name__)) 
            pass

    try:
        documenti_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Altri atti e documenti')]").get_attribute("href")
        fn.load_page(page_details2,documenti_url,80)
        time.sleep(3)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, 'div.column.content').get_attribute("outerHTML")                     
    except:
        pass
    
    try:              
        for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'div.detail-section > div > ul > li  > a'):
            attachments_data = attachments()
        
        #click on "//*[contains(text(),'Altri atti e documenti')]" in page_detail to take lot_details.
        # Onsite Field -Documenti
        # Onsite Comment -None

            attachments_data.file_name = single_record.text
        # Onsite Field -Documenti
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
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

try:
    th = date.today() - timedelta(1)
    threshold = '2022/01/01'
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_esiti_lista.wp?_csrf=KD7GFCQFLGRFC0P3K40YMQA6H71ZO6QL"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        page_main.find_element(By.XPATH,'//*[@id="ext-container"]/div[7]/div/div[1]/div[2]/form[1]/fieldset/div[4]/div/img').click()
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="model.dataPubblicazioneDa"]').send_keys('01/01/2022')
        time.sleep(2)
        DisplayLength = Select(page_main.find_element(By.CSS_SELECTOR,'#model\.iDisplayLength'))
        DisplayLength.select_by_index(3)
        time.sleep(2)
        page_main.find_element(By.XPATH,'//*[@id="ext-container"]/div[7]/div/div[1]/div[2]/form[1]/fieldset/div[6]/input[1]').click()
        time.sleep(5)
        for page_no in range(1,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ext-container"]/div[7]/div/div[1]/div[2]/form/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div[7]/div/div[1]/div[2]/form/div')))
            length = len(rows)
            for records in range(2,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div[7]/div/div[1]/div[2]/form/div')))[records]
                extract_and_save_notice(tender_html_element)

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="pagination-navi"]/input[8]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ext-container"]/div[7]/div/div[1]/div[2]/form/div'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)