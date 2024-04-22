from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ch_simap_ca"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ch_simap_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'ch_simap_ca'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CH'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'CHF'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    
    notice_text = tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(2)').text
    except:
        pass
 
    try:
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(1)').text
        notice_data.publish_date = datetime.strptime(publish_date, '%d.%m.%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except:
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').get_attribute('href')
    except:
        pass
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').click()
    except:
        pass
    try:
        notice_data.notice_text += notice_text
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR,'#Formcontent > form').get_attribute('href')
    except:
        pass
    try:
        notice_text1 = page_main.find_element(By.CSS_SELECTOR,'#Formcontent > form').text
    except:
        pass
    
    if 'Offizieller Name und Adresse des Auftraggebers' in notice_text1:
        notice_data.main_language = 'DE'
    elif 'Nom officiel et adresse du pouvoir adjudicateur' in notice_text1:
        notice_data.main_language = 'FR'
    elif 'Nome ufficiale e indirizzo del committente' in notice_text1:
        notice_data.main_language = 'IT'
    elif 'Official name and address of the contracting authority' in notice_text1:
        notice_data.main_language = 'EN'
    
    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH,'div.result_head').text.aplit('|')[1].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__)) 
        pass
    
    try:  
        class_codes_at_source = ''
        class_title_at_source = ''
        cpv_at_source = ''

        for code in page_main.find_elements(By.XPATH, '//*[contains(text(),"CPV:")]//ancestor::tbody[1]/tr'):
            cpv_code = code.text
            class_title_at_source += cpv_code.split('-')[1].strip()

            cpv_regex = re.compile(r'\d{8}')
            cpv_code_list = cpv_regex.findall(cpv_code)[0]
            cpvs_data = cpvs()

            class_codes_at_source += cpv_code_list
            class_codes_at_source += ','

            cpv_at_source += cpv_code_list
            cpv_at_source += ','

            cpvs_data.cpv_code = cpv_code_list
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)

        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')

        notice_data.class_title_at_source = class_title_at_source.rstrip(',')        

        notice_data.cpv_at_source = cpv_at_source.rstrip(',')        
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        
        try:
            award_details_data = award_details()
            try:
                code=['Datum:','Date']
                for award in code:
                    if award in notice_text1:
                        try:
                            award_date = re.findall(award+'(.+?)\n', notice_text1)[0]
                            award_date = re.findall('\d+.\d+.\d{4}',award_date)[0]
                            award_details_data.award_date = datetime.strptime(award_date,'%d.%m.%Y').strftime('%Y/%m/%d')
                        except:
                            pass
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass
            
            try:
                code=['Name:','Nom:','Cognome:']
                for bidder_name in code:
                    if bidder_name in notice_text1:
                        try:
                            award_details_data.bidder_name = re.findall(bidder_name+'(.+?)\n', notice_text1)[0]
                            award_details_data.bidder_name=award_details_data.bidder_name.split(',')[0]
                        except:
                            pass
            except Exception as e:
                logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                pass
            try:
                code=['Name:','Nom:','Cognome:','Price']
                for bidder_address in code:
                    if bidder_address in notice_text1:
                        try:
                            award_details_data.address = re.findall(bidder_address+'(.+?)\n', notice_text1)[0]
                        except:
                            pass
            except Exception as e:
                logging.info("Exception in bidder_address: {}".format(type(e).__name__))
                pass
            try:
                code=['Preis','Prix','Prezzo']
                for cost in code:
                    if cost in notice_text1:
                        try:
                            grossawardvaluelc = re.findall(cost+'(.+?)\n', notice_text1)[0]
                        except:
                            pass
                        grossawardvaluelc=GoogleTranslator(source='auto', target='en').translate(grossawardvaluelc)
                        grossawardvaluelc=grossawardvaluelc.split('CHF ')[1].split('with')[0]
                        try:
                            grossawardvaluelc = grossawardvaluelc.replace(',','')
                        except:
                            pass
                        award_details_data.grossawardvaluelc = float(grossawardvaluelc)
            except Exception as e:
                logging.info("Exception in bidder_address: {}".format(type(e).__name__))
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
        try:
            notice_data.type_of_procedure_actual = re.findall(r'Verfahrensart\n(.+?)\n',notice_text1)[0]
        except:
            notice_data.type_of_procedure_actual = re.findall(r'Type of proceduren(.+?)\n',notice_text1)[0]
        
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/ch_simap_procedure.csv",type_of_procedure_actual)
    except:
        try:
            notice_data.type_of_procedure_actual = re.findall(r'Tipo di proceduran(.+?)\n',notice_text1)[0]
            notice_data.type_of_procedure_actual = re.findall(r'Mode de procédure choisi\n(.+?)\n',notice_text1)[0]
            type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/ch_simap_procedure.csv",type_of_procedure_actual)  
        except:
            try:
                notice_data.type_of_procedure_actual = re.findall(r'Mode de procédure choisi\n(.+?)\n',notice_text1)[0]
                type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
                notice_data.type_of_procedure = fn.procedure_mapping("assets/ch_simap_procedure.csv",type_of_procedure_actual)
            except Exception as e:
                logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
                pass
    try:
        try:
            notice_data.contract_type_actual = re.findall(r'Auftragsart\n(.+?)\n',notice_text1)[0]
        except:
            try:
                notice_data.contract_type_actual = re.findall(r'Genre de marché\n(.+?)\n',notice_text1)[0]
            except:
                try:
                    notice_data.contract_type_actual = re.findall(r'Tipo di commessa\n(.+?)\n',notice_text1)[0]
                except:
                    notice_data.contract_type_actual = re.findall(r'Type of order\n(.+?)\n',notice_text1)[0]
        if 'Dienstleistungsauftrag' in notice_data.contract_type_actual or 'Marché de services' in notice_data.contract_type_actual or 'Commessa di servizi' in notice_data.contract_type_actual or 'Service' in notice_data.contract_type_actual or 'Competition' in notice_data.contract_type_actual or 'Order for services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        if 'Lieferauftrag' in notice_data.contract_type_actual or 'Wettbewerb' in notice_data.contract_type_actual or 'Marché de fournitures' in notice_data.contract_type_actual or 'Marché de travaux de construction' in notice_data.contract_type_actual or 'Supply order' in notice_data.contract_type_actual or 'Delivery order' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        if 'Bauauftrag' in notice_data.contract_type_actual or 'Travaux' in notice_data.contract_type_actual or 'Commessa edile' in notice_data.contract_type_actual or 'Construction contract' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass    
    
    try:
        try:
            notice_data.local_description = re.findall(r'Gegenstand und Umfang des Auftrags:(.+?)\n',notice_text1)[0]
        except:
            try:
                notice_data.local_description = re.findall(r'Brève description(.+?)\n',notice_text1)[0]
            except:
                try:
                    notice_data.local_description = re.findall(r'Subject and scope of the contract(.+?)\n',notice_text1)[0]
                except:
                    notice_data.local_description = re.findall(r'Oggetto e entità della commessa(.+?)\n',notice_text1)[0]
                    
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass 
    
    try:
        code=['Meldungsnummer','Numéro de la publication']
        for related_tender_id in code:
            if related_tender_id in notice_text1:
                try:
                    notice_data.related_tender_id = re.findall(related_tender_id+'(.+?)\n', notice_text1)[0]
                except:
                    pass
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    
    try:       
        
        customer_details_data = customer_details()
        try:
            code=['Bedarfsstelle/Vergabestelle','Service demandeur/Entité adjudicatrice','Servizio richiedente/Ente aggiudicatore:','Contracting authority/Authority of assignment']
            for org_name in code:
                if org_name in notice_text1:
                    customer_details_data.org_name = re.findall(org_name+'(.+?)\n', notice_text1)[0]
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
                    
        try:
            code=['Beschaffungsstelle/Organisator','Service organisateur/Entité organisatrice',"Servizio d'acquisto/Organizzatore:","Procurement authority/Organizer:"]
            for address in code:
                if address in notice_text1:
                    try:
                        customer_details_data.org_address = re.findall(address+'(.+?)\n', notice_text1)[0]
                    except:
                        pass
        except Exception as e:
            logging.info("Exception in address: {}".format(type(e).__name__))
            pass
        
        try:
            code=['Art des Auftraggebers','Genre de pouvoir adjudicateur','Tipo di procedura','Type of contracting authority']
            for type_of_authority_code in code:
                if type_of_authority_code in notice_text1:
                    try:
                        customer_details_data.type_of_authority_code = re.findall(type_of_authority_code+'\n(.+?)\n', notice_text1)[0]
                    except:
                        pass
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = fn.get_email(customer_details_data.org_address)
        except:
            pass
        try:
            customer_details_data.org_phone = customer_details_data.org_address.split('Telefon:')[1].split(',')[0]
        except:
            try:
                customer_details_data.org_phone = customer_details_data.org_address.split('Téléphone:')[1].split(',')[0]
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__)) 
                pass

        customer_details_data.org_country = 'CH'
        customer_details_data.org_language = notice_data.main_language
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.simap.ch/shabforms/COMMON/application/applicationGrid.jsp?template=2&view=1&page=/MULTILANGUAGE/simap/content/start.jsp"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        clk=page_main.find_element(By.XPATH,'//*[@id="formShab"]/div[2]/a[4]').click()
        time.sleep(5)
        try:
            for page_no in range(2,10): #5
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#resultList > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#resultList > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#resultList > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#pagin > tbody tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
