from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_altoad_archive_ca"
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
tnotice_count = 0
SCRIPT_NAME = "it_altoad_archive_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global tnotice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_altoad_archive_ca'
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
        
    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'
    notice_data.notice_type = 7
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Data di pubblicazione esito
    # Onsite Comment -None

    try:                                                                   
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.publishedAt").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is None:
        return
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
   
    # Onsite Field -None
    # Onsite Comment -Split title from "Oggetto"

    try:
        title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').text
        local_title = re.sub("\d{6}\/\d{4}","",title).split('(')[0].strip()
        notice_data.local_title = local_title
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.related_tender_id = re.findall('\d+/\d+', title)[0]
    except:
        pass 
    
    # Onsite Field -split "Procedura negoziata senza previa pubblicazione, Affidamento diretto" such type from "oggetto"
    # Onsite Comment -None
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'span.process-type').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_altoad_ca_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject >a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "(//dt[contains('Cig:,CIG:,CIG/SMART CIG:',text())])[3]//following::dd[1]").text
    except:
        notice_data.notice_no = notice_data.notice_url.split('id/')[1].split('/idL')[0].strip()
    notice_data.tender_id = notice_data.notice_no

    try:
        notice_contract_type = page_details.find_element(By.XPATH,"//*[contains(text(),'Tipo di appalto:')]//following::dd[1]").text
        notice_data.contract_type_actual = page_details.find_element(By.XPATH,"//*[contains(text(),'Tipo di appalto:')]//following::dd[1]").text
        if 'Servizi' in notice_contract_type or 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'pubblici' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
      
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="Contenuto"]').get_attribute("outerHTML")                     
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    # Onsite Field -Data Inizio
    # Onsite Comment -None
    try:
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Data Inizio")]//following::dd[1]').text
        tender_contract_start_date = re.findall('\d+/\d+/\d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass

    # Onsite Field -Data ultimazione
    # Onsite Comment -None

    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Data ultimazione")]//following::dd[1]').text
        tender_contract_end_date = re.findall('\d+/\d+/\d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass

    
    try:
        grossbudget_data = page_details.find_element(By.XPATH, '''//*[contains(text(),'Importo a base di gara (comprensivo di costi di sicurezza e ulteriori componenti non ribassabili):')]//following::dd[1]''').text
        grossbudgetlc = grossbudget_data.split('€ ')[1]
        notice_data.netbudgetlc = float(grossbudgetlc.replace('.','').replace(',','.').strip())
        if "€ " in grossbudget_data:
            grossbudgeteuro = grossbudgetlc
            notice_data.netbudgeteuro =float(grossbudgeteuro.replace('.','').replace(',','.').strip())
        elif "al netto di IVA" in grossbudget_data:
            netbudgeteuro = grossbudgetlc
            notice_data.netbudgeteuro =float(netbudgeteuro.replace('.','').replace(',','.').strip())
    except:
        pass
 
    try:              
        customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -split "buyer" from "Oggetto"
        customer_details_data.org_country = 'IT'
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text.split('(')[0].strip()
        try:
            customer_main_activity = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text
            if '-' in customer_main_activity:
                customer_details_data.customer_main_activity = customer_details_data.org_name.split('-')[1].split('\n')[0].strip()
            else:
                pass
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -just select " Organo competente per le procedure di ricorso:" for org address

        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, '#Contenuto').text
            if 'Organo competente per le procedure di ricorso:' in org_address:
                customer_details_data.org_address = org_address.split('Organo competente per le procedure di ricorso:')[1].split('Telefono:')[0]
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
               
        # Onsite Field -None
        # Onsite Comment -just select " Organo competente per le procedure di ricorso:" for "org phone"

        try:
            org_phone = page_details.find_element(By.CSS_SELECTOR, '#Contenuto').text
            if 'Telefono:' in org_phone:
                customer_details_data.org_phone = org_phone.split('Telefono:')[1].strip()
            else:
                pass
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Responsabile unico del Procedimento: ')]//following::dd[1]").text.strip()    
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="Contenuto"]'):
            cpvs_data = cpvs()
            # Onsite Field -Codice CPV
            # Onsite Comment -split " Codice CPV" from the path
            cpvs_data.cpv_code = single_record.find_element(By.CSS_SELECTOR,'div > b').text.split('-')[0].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        class_codes_at_source = ''
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="Contenuto"]'):
            class_codes_at_source += single_record.find_element(By.CSS_SELECTOR,'div > b').text.split('-')[0].strip()
            class_codes_at_source += ','
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
        notice_data.cpv_at_source = notice_data.class_codes_at_source
        logging.info(notice_data.class_codes_at_source)
    except:
        pass
        
    try:
        for file_name in page_details.find_elements(By.CSS_SELECTOR, '#Contenuto > div:nth-child(3) > table.genericList.attachmentsList > tbody > tr'):
            attachments_data = attachments()
            attachments_data.file_name = file_name.find_element(By.CSS_SELECTOR, 'td.document').text.strip()
            try:
                attachments_data.file_size = file_name.find_element(By.CSS_SELECTOR, 'td.document').text.split('(')[1].split(')')[0].strip()
            except:
                pass
            attachments_data.external_url = file_name.find_element(By.CSS_SELECTOR, ' td.document > a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in file_name: {}".format(type(e).__name__))
        pass
    
    
    try:
        lot_details_data = lot_details()

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        lot_details_data.contract_start_date = notice_data.tender_contract_start_date
        lot_details_data.contract_end_date = notice_data.tender_contract_end_date
        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
        lot_details_data.contract_type = notice_data.notice_contract_type
        try:
            lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Tempo di completamento dell")]//following::dd[1]').text
            notice_data.contract_duration = lot_details_data.contract_duration
        except:
            pass

        lot_details_data.lot_number = 1

        try:
            for single_record in page_details.find_elements(By.XPATH, '//*[@id="Contenuto"]'):
                lot_cpvs_data = lot_cpvs()

                lot_cpvs_data.lot_cpv_code = single_record.find_element(By.CSS_SELECTOR,'div > b').text.split('-')[0].strip()
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass

        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td:nth-child(3) > ul > li'): 
            award_details_data = award_details()
            
            try:
                bidder =  WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'td:nth-child(3) > ul > li')))
                bidder1=len(bidder)
            except:
                pass

            award_details_data.bidder_name = single_record.text.split(',')[0].strip()
            try:
                award_details_data.address = single_record.text.split(',')[1].strip()
            except:
                pass
            try:
                netawardvalue = page_details.find_element(By.CSS_SELECTOR, '#list-contractors td:nth-child(4)').text
                netawardvaluelc = netawardvalue.split('€ ')[1].split('(')[0].replace('.','').replace(',','.')
                netawardvaluelc = re.sub("[^\d\.\,]", "",netawardvaluelc)
            except:
                pass
            
            try:
                part_value = float(netawardvaluelc) / bidder1
            except:
                pass
            
            try:
                award_details_data.netawardvaluelc = float(part_value)
                if "€ " in netawardvalue:
                    award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
            except:
                pass

            try:
                award_date = page_details.find_element(By.CSS_SELECTOR, '#list-contractors td:nth-child(5)').text
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                lot_details_data.lot_award_date=award_details_data.award_date
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass
                
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        if lot_details_data.award_details != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)

    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo a base di gara (comprensivo di costi di sicurezza e ulteriori componenti non ribassabili):")]//following::dd[1]').text.split('€')[1]
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
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

try:
    th = date.today() - timedelta(1)
    threshold = '2022/01/01'
    logging.info("Scraping from or greater than: " + threshold)
    for page_no in range(1,3080):#3080
        url = 'https://www.bandi-altoadige.it/awards/list-public/advancedSearch/1/page/'+str(page_no)+'/?keywords=&status=&type=&tenderProcedure=&organization=&organizationUnit=&ocp=&publishedAt%5Bfrom%5D=01%2F01%2F2022&publishedAt%5Bto%5D=01%2F01%2F2024&awardedAt%5Bfrom%5D=&awardedAt%5Bto%5D=&expiredAt=&recordNumber=50&submitButton=Cerca&advancedSearch=1'
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[3]/div[2]/form[2]/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[3]/div[2]/form[2]/div[2]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
    
                if notice_count == 50:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
