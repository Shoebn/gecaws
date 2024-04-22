from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_contractaciopublica_ca"
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
SCRIPT_NAME = "es_contractaciopublica_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'es_contractaciopublica_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.main_language = 'ES'
    notice_data.procurement_method = 0
    notice_data.notice_type = 7

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'app-resultats-cerca-avancada > div > div > a').text 
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    time.sleep(3)

    try:       
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.d-flex > span").text 
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    time.sleep(3)
    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'a.fw-bold.text-black.text-decoration-none.fs-4'))).get_attribute("href")  
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:   
        accept_all = WebDriverWait(page_details, 5).until(EC.element_to_be_clickable((By.XPATH,"(//button[@class='btn btn-primary'])")))
        page_details.execute_script("arguments[0].click();",accept_all)
    except Exception as e:
        logging.info("Exception in Expedients_search: {}".format(type(e).__name__))

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > app-root > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
     
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::div[1]').text  
        if 'Work projects' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Supplies' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            pass 
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    if 'Framework of bidding companies and classification of offers' in notice_data.notice_text:
        try:              
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-avaluacio-empreses-licitadores-lot > div > div > div > div'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                
                lot_details_data.lot_title  = notice_data.local_title
                lot_details_data.lot_title_english = notice_data.notice_title

                try:
                    lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div > div:nth-child(2) > div.col-md-8').text
                    lot_details_data.lot_actual_number = lot_actual_number.split(')')[1]
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                    lot_details_data.lot_contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass

                try:
                    bidder_name = single_record.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > div.col-md-8').text
                    if len(bidder_name)>5:
                        award_details_data = award_details()

                        award_details_data.bidder_name = bidder_name
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    else:
        try:
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR,'app-taula-contractes > ngc-table > div > table > tbody >  tr.cdk-row.fila-expandible.font-size-sm'): 
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                try:
                    lot_details_data.lot_title  = single_record.find_element(By.CSS_SELECTOR,'td.cdk-cell.cdk-column-descripcio').text
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except Exception as e:
                    logging.info("Exception in lot_title: {}".format(type(e).__name__)) 
                    pass


                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'td.cdk-cell.cdk-column-expedient').text   
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__)) 
                    pass

                try:
                    clk=single_record.find_element(By.CSS_SELECTOR,'button.btn.btn-sm.btn-icon').click()
                except:
                    clk=single_record.find_element(By.CSS_SELECTOR,' svg.bi.bi-chevron-down').click()
                time.sleep(2)

                lot_text = page_details.find_element(By.CSS_SELECTOR,'td.cdk-cell.p-2.cdk-column-expandedDetail.collapse.show').text

                contract_start_date = fn.get_string_between(lot_text,'Start of implementation date:','End of implementation date:') 
                contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')                

                contract_end_date = fn.get_string_between(lot_text,'End of implementation date:','Award date:') 
                contract_end_date = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')                

                lot_award_date = fn.get_string_between(lot_text,'Award date:','Company awarded the tender:') 
                lot_award_date = re.findall('\d+/\d+/\d{4}',lot_award_date)[0]
                lot_details_data.lot_award_date = datetime.strptime(lot_award_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')  

                lot_netbudget = fn.get_string_between(lot_text,'(excluding VAT):','Value of the contract awarded (including VAT):')
                lot_netbudget = lot_netbudget.split('€')[0].strip()
                lot_netbudget = lot_netbudget.replace(',','').strip() 
                lot_details_data.lot_netbudget = float(lot_netbudget)

                lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget

                lot_grossbudget = lot_text.split("(including VAT):")[1].split("\n")[1]
                lot_grossbudget = lot_grossbudget.split('€')[0].strip()
                lot_grossbudget = lot_grossbudget.replace(',','').strip()
                lot_details_data.lot_grossbudget = float(lot_grossbudget)

                lot_details_data.lot_grossbudget_lc = lot_details_data.lot_grossbudget

                try:
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                    lot_details_data.lot_contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass

                try:
                    award_details_data = award_details()
                    award_details_data.bidder_name = lot_text.split('Company awarded the tender:')[1].split('\n')[1]

                    award_date = fn.get_string_between(lot_text,'Award date:','Company awarded the tender:') 
                    award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%Y').strftime('%Y/%m/%d')  

                    award_details_data.grossawardvalueeuro = lot_details_data.lot_grossbudget
                    award_details_data.grossawardvaluelc = lot_details_data.lot_grossbudget

                    award_details_data.netawardvalueeuro = lot_details_data.lot_netbudget
                    award_details_data.netawardvaluelc = lot_details_data.lot_netbudget

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass

                lot_cpvs_data = lot_cpvs()
                lot_cpv_code=fn.get_string_between(lot_text,'CPV:','Start of implementation')
                lot_cpvs_data.lot_cpv_code = lot_cpv_code.split('-')[0].strip()
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)

                try:
                    cpv_at_source = ''
                    lot_details_data.lot_cpv_at_source = lot_cpvs_data.lot_cpv_code
                except:
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1

                try:
                    clk=single_record.find_element(By.CSS_SELECTOR,' button.btn.btn-sm.btn-icon').click()
                except:
                    clk=single_record.find_element(By.CSS_SELECTOR,' svg.bi.bi-chevron-up').click()
                time.sleep(2)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    try:
        tender_announcement_click = WebDriverWait(page_details, 5).until(EC.element_to_be_clickable((By.XPATH,"/html/body/app-root/main/app-detall-publicacio/div[4]/div[1]/app-navegacio-fases/div/ul/li[1]/div/a")))
        page_details.execute_script("arguments[0].click();",tender_announcement_click)
        time.sleep(3)
    except:
        pass

    try:   
        Further_information_Subject = WebDriverWait(page_details, 5).until(EC.element_to_be_clickable((By.XPATH,"(//button[@class='btn font-size-sm p-0 ms-auto text-decoration-underline'])[2]")))  
        page_details.execute_script("arguments[0].click();",Further_information_Subject)
    except Exception as e:
        logging.info("Exception in Expedients_search: {}".format(type(e).__name__))
    time.sleep(2)
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Description")])[1]//following::div[1]').text        
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)  
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated value of contract")]//following::div[1]').text  
        est_amount = est_amount.split('€')[0].strip()
        est_amount = est_amount.replace(',','').strip()
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '(//*[contains(text(),"Basic estimate for tender")])[1]//following::div[1]').text    
        netbudgetlc = netbudgetlc.split('€')[0].strip()
        netbudgetlc = netbudgetlc.replace(',','').strip()
        notice_data.netbudgetlc = float(netbudgetlc)
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    try:
        netbudgeteuro = page_details.find_element(By.XPATH, '(//*[contains(text(),"Basic estimate for tender")])[1]//following::div[1]').text  
        netbudgeteuro = netbudgeteuro.split('€')[0].strip()
        netbudgeteuro = netbudgeteuro.replace(',','').strip()
        notice_data.netbudgeteuro = float(netbudgeteuro)        
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass

    try:
        vat = page_details.find_element(By.XPATH, '(//*[contains(text(),"VAT")])[1]//following::div[1]').text
        if len(vat)>1:
            vat = vat.split('%')[0].strip()
            vat = vat.replace(',','').strip()
            notice_data.vat = float(vat)        
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Basic estimate for tender including VAT")]//following::div[1]').text  

        grossbudgetlc = grossbudgetlc.split('€')[0].strip()
        grossbudgetlc = grossbudgetlc.replace(',','').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc) 
        
        notice_data.grossbudgeteuro = notice_data.grossbudgetlc
        
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    notice_data.class_at_source = 'CPV'
    
    try:
        notice_data.contract_number = page_details.find_element(By.CSS_SELECTOR, '(//*[contains(text(),"Expedient code")])[1]//following::span[1]').text 
    except Exception as e:
        logging.info("Exception in contract_number: {}".format(type(e).__name__))
        pass

    try:              
        cpvs_data = cpvs()

        try:
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::div[1]').text 
            if len(cpv_code)>5:
                cpv_code = cpv_code.split('-')[0]
                cpvs_data.cpv_code = cpv_code
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.cpv_at_source = cpvs_data.cpv_code
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    try:   
        Further_information_Procurement = WebDriverWait(page_details, 5).until(EC.element_to_be_clickable((By.XPATH,"(//button[@class='btn font-size-sm p-0 ms-auto text-decoration-underline'])[1]")))  
        page_details.execute_script("arguments[0].click();",Further_information_Procurement)
    except Exception as e:
        logging.info("Exception in Expedients_search: {}".format(type(e).__name__))
    time.sleep(2)

    try:              
        customer_details_data = customer_details()

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'app-resultats-cerca-avancada div.d-flex.flex-column.gap-1 a').text 
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'ES'
        customer_details_data.org_language = 'ES'

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal address")]//following::div[1]').text 
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Locality")]//following::div[1]').text 
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Post code")]//following::div[1]').text 
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS (Nomenclature of Territorial Units for Statistics)")]//following::div[1]').text  
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Email address")])[1]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Web address")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

        try:
            contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact persons")]//following::div[1]').text 
            if len(contact_person)>5 :
                customer_details_data.contact_person = contact_person.split('Name:')[1].split('\n')[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Main activity")]//following::div[1]').text 
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-md-8 > div.d-flex'):
            attachments_data = attachments()

            external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button"))) 
            page_details.execute_script("arguments[0].click();",external_url)
            time.sleep(25)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 

            file_name = single_record.text    
            if len(file_name)>5:
                file_name = file_name.split('.')
                attachments_data.file_name = '.'.join(file_name[:-1])
                attachments_data.file_type = file_name[-1]

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://contractaciopublica.gencat.cat/ecofin_pscp/AppJava/en_GB/search.pscp?pagingPage=0&reqCode=searchCn&aggregatedPublication=false&sortDirection=1&pagingNumberPer=10&lawType=2"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)


        try:
            Accept_cookies = page_main.find_element(By.XPATH,"(//button[@class='btn btn-primary'])[2]").click()
            time.sleep(3)
            logging.info("Accept_cookies clicked")
        except:
            pass

        try:   
            Expedients_search = WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.XPATH,"(//button[@class='btn btn-primary'])")))
            page_main.execute_script("arguments[0].click();",Expedients_search)
            time.sleep(3)
            logging.info("Expedients_search clicked")
        except Exception as e:
            logging.info("Exception in Expedients_search: {}".format(type(e).__name__))
            pass

        try:   
            File_under_assessment = WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.XPATH,"(//label[@class='form-check-label'])[6]"))) 
            page_main.execute_script("arguments[0].click();",File_under_assessment)
            time.sleep(3)
            logging.info("File_under_assessment clicked")
        except Exception as e:
            logging.info("Exception in File_under_assessment: {}".format(type(e).__name__))
            pass

        try:   
            Adjudication = WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.XPATH,"(//label[@class='form-check-label'])[7]"))) 
            page_main.execute_script("arguments[0].click();",Adjudication)
            time.sleep(3)
            logging.info("Adjudication clicked")
        except Exception as e:
            logging.info("Exception in Adjudication: {}".format(type(e).__name__))
            pass

        try:   
            Apply_filters  = WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.XPATH,"(//button[@class='btn btn-primary w-100'])[1]"))) 
            page_main.execute_script("arguments[0].click();",Apply_filters)
            time.sleep(3)
            logging.info("Apply_filters clicked")
        except Exception as e:
            logging.info("Exception in Apply_filters: {}".format(type(e).__name__))
            pass
            
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div'))).text  
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div')))  
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div')))[records]  
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Next')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div'),page_check))
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
