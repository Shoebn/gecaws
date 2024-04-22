from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_start_archive_spn"
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
tnotice_count = 0
SCRIPT_NAME = "it_start_archive_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
Doc_Download2 = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)

output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.procurement_method = 2
    notice_data.script_name = 'it_start_archive_spn'
    notice_data.main_language = 'IT'
    notice_data.class_at_source = 'CPV'
        
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
        
    notice_data.currency = 'EUR'
    notice_data.notice_type = 4
    notice_data.document_type_description = 'Bandi e avvisi'


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td.amount').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(notice_data.est_amount)
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -Importo (al netto dell’IVA):
    # Onsite Comment -None
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'span.protocolId').text
        notice_data.tender_id = notice_data.notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
  

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,360)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        details = WebDriverWait(page_details, 180).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.page-nav > div > a'))).text
        while True:
            click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.page-nav > div > a')))
            page_details.execute_script("arguments[0].click();",click)
            time.sleep(4)
            break
    except:
        pass
    
    
    try:
        publish_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Data pubblicazione:")]//following::span[1]''').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    
    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo (al netto dell’IVA):")]//following::span[1]').text
        netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
        notice_data.netbudgetlc = netbudgetlc.replace('.','').replace(',','.').strip()
        notice_data.netbudgetlc = float(notice_data.netbudgetlc)
        notice_data.netbudgeteuro = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/tendering-app/div[2]/ng-component/ng-component').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    
    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "li:nth-child(2) > span.stats-value").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:               
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.list-detail-view.sortable'):
            attachments_data = attachments()
            try:
                file_type = single_record.find_element(By.CSS_SELECTOR,'div.pad-left-20px > div > a').text
                if 'pdf' in file_type:
                    attachments_data.file_type = 'pdf'
                elif 'PDF' in file_type:
                    attachments_data.file_type = 'pdf'
                elif 'zip' in file_type:
                    attachments_data.file_type = 'zip'
                elif 'ZIP' in file_type:
                    attachments_data.file_type = 'zip'
                elif 'DOCX' in file_type:
                    attachments_data.file_type = 'DOCX'
                elif 'docx' in file_type:
                    attachments_data.file_type = 'docx'
                elif 'XLS' in file_type:
                    attachments_data.file_type = 'XLS'
                elif 'xlsx' in file_type:
                    attachments_data.file_type = 'xlsx'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.pad-left-20px > h3').text.strip()
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div.pad-left-20px > div > a')
            page_details.execute_script("arguments[0].click();",attachments_data.external_url)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

            try:
                attachments_data.file_size = single_record.text.split('Dimensione:')[1].split('\n')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text.split('-')[0]
        try:
            customer_main_activity = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text.replace(customer_details_data.org_name,'').replace('-','').strip()
            customer_details_data.customer_main_activity = customer_main_activity
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
            
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Responsabile unico del procedimento:")]//following::span[1]').text
        except:
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, " div.tender-description").text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Scelta del contraente:")]//following::span[1]').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_start_spn_procedure.csv",type_of_procedure_actual)
    except:
        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '''//*[contains(text(),'Indagine di mercato "aperta"')]//following::span[1]''').text
            type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/it_start_spn_procedure.csv",type_of_procedure_actual)   
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass
    
    
    try:
        earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"Costi di sicurezza non soggetti a ribasso (al netto dell’IVA):")]//following::span[1]').text
        earnest_money_deposit = re.sub("[^\d\.\,]", "", earnest_money_deposit)
        notice_data.earnest_money_deposit = earnest_money_deposit.replace('.','').replace(',','.').strip()
    except:
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.contractType').text
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td.contractType').text
        if 'Servizi' in notice_contract_type or 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Lavori pubblici' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
                          
    try: 
        page_details1_url = page_details.find_element(By.CSS_SELECTOR, 'div.form-builder-header ul > li:nth-child(2) > a').get_attribute("href")
        fn.load_page_expect_xpath(page_details1,page_details1_url,'/html/body/tendering-app/div[2]/ng-component/ng-component/div[2]/div/form/builder-tabs/builder-tab[2]/div/div/classification-tab/builder-subtabs/builder-subtab/div/div/classification-first-level/div/div/div',180)
        try:
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'classification-first-level > div > div > div').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'classification-first-level > div > div > div > div:nth-child(2) > div'):
            cpvs_data = cpvs()
            cpvs_data.cpv_code = single_record.find_element(By.CSS_SELECTOR, 'span').text.split('-')[0].strip()
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
            
        try:
            class_codes_at_source = ''
            for singlerecord in page_details1.find_elements(By.CSS_SELECTOR, 'classification-first-level > div > div > div > div:nth-child(2) > div'):
                class_codes_at_source += singlerecord.find_element(By.CSS_SELECTOR, 'span').text.split('-')[0].strip()
                class_codes_at_source += ','
            notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
            notice_data.cpv_at_source = notice_data.class_codes_at_source
            logging.info(notice_data.class_codes_at_source)
        except:
            pass
        
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__))
        pass
    
    try: 
        Elenco_lotti = page_details.find_element(By.CSS_SELECTOR, 'div.form-builder-header ul > li:nth-child(4) > a').text
        if 'ELENCO LOTTI' in Elenco_lotti:
            page_details2_url = page_details.find_element(By.CSS_SELECTOR, 'div.form-builder-header ul > li:nth-child(4) > a').get_attribute("href")
            fn.load_page_expect_xpath(page_details2,page_details2_url,'/html/body/tendering-app/div[2]/ng-component/ng-component/div[2]/div/form/builder-tabs/builder-tab[4]/div/div/lots-manager/div/div[2]/div/ul/li',180)

            try:
                notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, 'li.lot-item-container').get_attribute("outerHTML")
            except Exception as e:
                logging.info("Exception in notice_text: {}".format(type(e).__name__))
                pass

            lot_number = 1
            for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'li.lot-item-container'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual


                try:
                    lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'lot-item > div:nth-child(4) > div.pad-btm-10px').text
                    lot_netbudget_lc = re.sub("[^\d\.\,]", "", lot_netbudget_lc)
                    lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace('.','').replace(',','.').strip())
                    lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'lot-item div.lot-item-name a').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'lot-item > div.cig.text-align-center.width-20 > div.pad-btm-10px').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                try:
                    for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'classification-first-level > div > div > div > div:nth-child(2) > div'):
                        lot_cpvs_data = lot_cpvs()
                        lot_cpvs_data.lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'span').text.split('-')[0].strip()
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs_data: {}".format(type(e).__name__))
                    pass

                page_details3_url = page_details2.find_element(By.CSS_SELECTOR, 'lot-item > div.border-right.width-20 > div > div.message.label.width-100.font-s.pad-btm-15px.truncate-word > a').get_attribute("href")
                fn.load_page_expect_xpath(page_details3,page_details3_url,'/html/body/tendering-app/div[2]/ng-component/lot-create/div[3]/div/div/div/form/builder-subtabs/builder-subtab[1]/div/div/lot-subject-info/div[1]/div[2]/div',180)
                notice_data.notice_text += page_details3.find_element(By.CSS_SELECTOR, 'body > tendering-app > div.content-panel > ng-component > lot-create > div.no-errors > div').get_attribute('outerHTML')
                try:
                    contract_duration = page_details3.find_element(By.XPATH,"//*[contains(text(),'affidamento in giorni (al netto di rinnovi e ripetizioni)')]//following::div[1]").text
                    lot_details_data.contract_duration = "Durata dell'affidamento in giorni (al netto di rinnovi e ripetizioni) "+contract_duration
                    notice_data.contract_duration = lot_details_data.contract_duration
                except:
                    pass

                try:
                    lot_details_data.lot_description = page_details3.find_element(By.XPATH,"//*[contains(text(),'Descrizione')]//following::div[1]").text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except:
                    pass

                try:
                    lot_criteria_click = page_details3.find_element(By.CSS_SELECTOR, 'body > tendering-app > div.content-panel > ng-component > lot-create > div.no-errors > div > div > div > form > builder-subtabs > div > div > ul > li:nth-child(2) > a')
                    page_details3.execute_script("arguments[0].click();",lot_criteria_click)
                    WebDriverWait(page_details3, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > tendering-app > div.content-panel > ng-component > lot-create > div.no-errors > div > div > div > form > builder-subtabs > builder-subtab:nth-child(3) > div > div > lot-offer-configuration > div > div.box-content.collapsible-content > div > div:nth-child(1) > div.form-label'))).text
                except:
                    pass

                try:
                    single_record = page_details3.find_element(By.XPATH, '/html/body/tendering-app/div[2]/ng-component/lot-create/div[3]/div/div/div/form/builder-subtabs/builder-subtab[2]/div/div/lot-offer-configuration/div/div[2]/div/div[3]')
                    title =[]
                    for data in single_record.find_elements(By.CSS_SELECTOR, 'div.form-label'):
                        title.append(data.text)
                    weight = []
                    for data1 in single_record.find_elements(By.CSS_SELECTOR, 'div.form-element.pad-btm-10px'):
                        weight.append(data1.text)
                    for criteria_title, criteria_weight in zip(title, weight):


                        lot_criteria_data = lot_criteria()

                        lot_criteria_data.lot_criteria_title = criteria_title.strip()
                        if 'economico' in lot_criteria_data.lot_criteria_title.lower():
                            lot_criteria_data.lot_is_price_related = True

                        lot_criteria_weight = criteria_weight.strip()
                        lot_criteria_data.lot_criteria_weight =int(lot_criteria_weight)

                        if lot_criteria_data.lot_criteria_weight > 0:
                            lot_criteria_data.lot_criteria_cleanup()
                            lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria_data: {}".format(type(e).__name__))
                    pass  

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass  

    try:
        page_details4_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Requisiti di partecipazione")]').get_attribute("href")
        fn.load_page(page_details4,page_details4_url,220)
        notice_data.notice_text += page_details4.find_element(By.CSS_SELECTOR, 'builder-tabs > builder-tab:nth-child(6) > div').get_attribute('outerHTML')
        for single_record in page_details4.find_elements(By.CSS_SELECTOR, 'div.list-detail-view.document-request-info-obsolete'):
            try:
                attachments_data = attachments()
    
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div h3').text
                external_url = single_record.find_element(By.CSS_SELECTOR, 'div > ul > li > a')
                page_details4.execute_script("arguments[0].click();",external_url)
                file_dwn = Doc_Download2.file_download()
                attachments_data.external_url = str(file_dwn[0])
                
                try:
                    file_type = single_record.find_element(By.CSS_SELECTOR,'div > div > div > ul > li > a').text
                    if 'pdf' in file_type:
                        attachments_data.file_type = 'pdf'
                    elif 'PDF' in file_type:
                        attachments_data.file_type = 'pdf'
                    elif 'zip' in file_type:
                        attachments_data.file_type = 'zip'
                    elif 'ZIP' in file_type:
                        attachments_data.file_type = 'zip'
                    elif 'DOCX' in file_type:
                        attachments_data.file_type = 'DOCX'
                    elif 'docx' in file_type:
                        attachments_data.file_type = 'docx'
                    elif 'doc' in file_type:
                        attachments_data.file_type = 'doc'
                    elif 'XLS' in file_type:
                        attachments_data.file_type = 'XLS'
                    elif 'xlsx' in file_type:
                        attachments_data.file_type = 'xlsx'
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                try:
                    attachments_data.file_size = single_record.text.split('Dimensione:')[1].split('\n')[0]
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)

            except:
                pass
    except:
        pass
             
             
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
page_details1 = fn.init_chrome_driver(arguments)
page_details2 = fn.init_chrome_driver(arguments)
page_details3 = fn.init_chrome_driver(arguments)
page_details4 = Doc_Download2.page_details

try:
    th = date.today() - timedelta(1)
    threshold = '2022/01/01'
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://start.toscana.it/initiatives/list/advancedSearch/true'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        page_main.find_element(By.CSS_SELECTOR,'#publishedFrom').send_keys('01/01/2022')
        time.sleep(3)
        page_main.find_element(By.CSS_SELECTOR,'#publishedUntil').send_keys('01/01/2024')
        time.sleep(3)
        page_main.find_element(By.CSS_SELECTOR,'#nuts').click()
        time.sleep(5)
        page_main.find_element(By.CSS_SELECTOR,'#filter').click()
        time.sleep(5)
        
        for page_no in range(2,700):
            page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Contenuto"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                if notice_count == 50:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0

            try:   
                next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li:nth-child(12) > a')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr'),page_check))
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
