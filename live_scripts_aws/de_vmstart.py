from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_vmstart"
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
SCRIPT_NAME = "de_vmstart"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_vmstart'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)


    notice_data.main_language = 'DE'


    notice_data.currency = 'EUR'


    notice_data.procurement_method = 2


    notice_data.notice_type = 4

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.tender').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td.tenderType").text.split(", ")[1]
        type_of_procedure_actual_en = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/de_vmstart_procedure.csv",type_of_procedure_actual_en)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.tenderDeadline").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    details = tender_html_element
    page_main.execute_script("arguments[0].click();",details)

    try:
        notice_data.notice_text += WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.ID,'printarea'))).get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    notice_data.document_type_description = 'Notice'

    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"Vergabenummer:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:    
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_main.find_element(By.XPATH, '//*[contains(text()," CPV-Code Hauptteil")]//following::td[1]').text
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        customer_details_data = customer_details()

        customer_details_data.org_country = 'DE'

        customer_details_data.org_language = 'DE'

        try:
            customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text.split('\n')[0]
        except:
            try:
                customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Beschaffer")]//following::td[1]').text.split('\n')[0]
            except:
                try:
                    customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td').text.split('\n')[0]
                except Exception as e:
                    logging.info("Exception in org_name: {}".format(type(e).__name__))

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text.replace('\n',' ')
        except:
            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td').text.replace('\n',' ')
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass


        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefonnummer:")]//following::td[1]|//*[contains(text(),"Telefon:")]//following::td[1]').text
        except:
            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td').text.split('Telefon:')[1].split("\n")[0]
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-Mail-Adresse:")]//following::td[1]|//*[contains(text(),"E-Mail:")]//following::td[1]').text.strip()
        except:
            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td').text.split('E-Mail:')[1].split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]|//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text.split('Fax:')[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Faxnummer:")]//following::td').text
            except Exception as e: 
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td[1]|//*[contains(text(),"Name und Anschrift:")]//following::td[1]').text.split("\n")[0].split(":")[1].split(',')[0]
        except:
            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Name und Adressen")]//following::td').text.split("\n")[0].split(":")[1]
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        

        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"NUTS-Code:")]//following::td').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except:
        pass

    try:
        tender_criteria_data = tender_criteria()
        tender_criteria_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Zuschlagskriterien")]//following::td').text
        tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)        
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Geschätzter Wert")]//following::td').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    

    try:
        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags:")]//following::td').text
        except:
            notice_data.local_description=''

        if notice_data.local_description == "":
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Umfang der Leistung:")]//following::td[1]').text
    except:
        pass
    

    try:
        local_des = page_main.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td[1]').text
        notice_data.local_description+= local_des
    except:
        pass

    try:
        notice_data.notice_summary_english = notice_data.local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.notice_summary_english)
    except:
        try:
            notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Bezeichnung des Auftrags:")]//following::td').text
        except:
            try:
                notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Kurze Beschreibung:")]//following::td').text
            except:
                try:
                    notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Umfang der Leistung:")]//following::td').text
                except:
                    notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Art der Leistung:")]//following::td').text

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.notice_summary_english)
    except:
        pass

    try:
        single_record = page_main.find_element(By.ID, 'printarea')
        lots = single_record.text.split("II.2) Beschreibung")
        lot_number = 1
        for lot in lots:
            if 'Bezeichnung des Auftrags:' in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number =  lot_number

                try:
                    lot_details_data.lot_title = lot.split('Bezeichnung des Auftrags:')[1].split('\n')[0]
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except Exception as e:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))

                try:
                    notice_contract_type = page_main.find_element(By.XPATH, "//*[contains(text(),'Art des Auftrags')]//following::td").text
                    lot_details_data.contract_type = GoogleTranslator(source='auto', target='en').translate(notice_contract_type)
                    if 'delivery order' in lot_details_data.contract_type:
                        lot_details_data.contract_type = 'Supply'
                    elif 'Public Works' in lot_details_data.contract_type:
                        lot_details_data.contract_type = 'Works'
                    elif 'services' in lot_details_data.contract_type:
                        lot_details_data.contract_type = 'Service'
                    elif 'construction' in lot_details_data.contract_type:
                        lot_details_data.contract_type = 'Works'
                    else:
                        pass
                except:
                    pass

                try:
                    notice_data.notice_contract_type = lot_details_data.contract_type
                except:
                    pass

                try:
                    lot_details_data.lot_description = lot.split('Beschreibung der Beschaffung')[1].split('II.2.5)')[0]
                    lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except:
                    lot_details_data.lot_description = notice_data.notice_title


                try:
                    lot_details_data.lot_nuts = lot.split('NUTS-Code:')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

                try:
                    contract_start_date_text = lot.split('Beginn: ')[1].split(' Ende: ')[0]
                    contract_start_date = re.findall('\d+.\d+.\d{4}',contract_start_date_text)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d.%m.%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass


                try:
                    contract_end_date_text = lot.split('Ende: ')[1].split('\n')[0]
                    contract_end_date = re.findall('\d+.\d+.\d{4}',contract_end_date_text)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d.%m.%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass


                try:
                    lot_criteria_data = lot_criteria()
                    lot_criteria_title = lot.split('Zuschlagskriterien')[1].split('\n')[1].split('\n')[0]
                    lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria_title {}".format(type(e).__name__))
                    pass


                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpv_code = lot.split('Weitere(r) CPV-Code(s)')[1].split('\n')[0]
                    cpv_regex = re.compile(r'\d{8}')
                    lot_cpvs_data.lot_cpv_code  = cpv_regex.findall(lot_cpv_code)
                    lot_cpvs_data.lot_cpv_code = str(lot_cpvs_data.lot_cpv_code)
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

    try:
        attachment_page_url = page_main.find_element(By.LINK_TEXT,'Unterlagen zur Ansicht herunterladen').get_attribute('href')
        fn.load_page(page_details,attachment_page_url,50)
        attachments_data = attachments()
        attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'a.zipDownload').get_attribute('href')
        attachments_data.file_name  = page_details.find_element(By.CSS_SELECTOR, 'div.content.border > div > div:nth-child(7) > h4').text
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    page_main.back()
    time.sleep(2)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody')))

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://vergabe.vmstart.de/NetServer/PublicationSearchControllerServlet?function=SearchPublications&Gesetzesgrundlage=All&Category=InvitationToTender&thContext=publications"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,9):#9
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div/div/div/div/div[2]/div[3]/div[2]/ul/li[5]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(10)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/div/div/div/div[2]/div[2]/table[1]/tbody'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))

finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
