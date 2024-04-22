from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cy_eprocurement_spn"
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cy_eprocurement_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'cy_eprocurement_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CY'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.main_language = 'EL'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(5)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) a').get_attribute("href") 
    except:
        pass
        
    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        time.sleep(3)
        logging.info(notice_data.notice_url)
    
        try:
            cookies_close_click_2 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="cookieModalConsent"]'))).click()  
            time.sleep(3)
        except:
            pass
        
        try:
            if notice_data.publish_date == None or notice_data.publish_date == '':
                publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Ημερομηνία δημοσίευσης/πρόσκλησης:")]//following::dd[1]').text
                notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    return
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Content > dl').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Περιγραφή")]//following::dd[1]').text  
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Μοναδικός Αριθμός Διαγωνισμού")]//following::dd[1]').text  
        except:
            try:
                notice_data.notice_no = notice_data.notice_url.split('=')[1].strip()
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass    

        try:
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description) 
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass

        try:
            notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Τύπος Σύμβασης")]//following::dd[1]').text 

            if 'Προμήθειες' in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'

            elif 'Υπηρεσίες' in notice_contract_type:
                notice_data.notice_contract_type = 'Service'

            elif 'Έργα' in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Τύπος Σύμβασης")]//following::dd[1]').text  
        except Exception as e:
            logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
            pass

        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Διαδικασία:")]//following::dd[1]').text  
            type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/cy_eprocurement_spn_procedure.csv",type_of_procedure_actual)  
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

        try:
            document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Ημερομηνία Αποσφράγισης Προσφορών")]//following::dd[1]').text  
            document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass    

        try:
            est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Εκτιμώμενη Αξία (EUR)")]//following::dd[1]').text  
            notice_data.est_amount = float(est_amount.replace('.',''))
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass

        try:
            grossbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"Εκτιμώμενη Αξία")]').text
            if 'EUR' in grossbudgeteuro:
                notice_data.grossbudgeteuro = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in grossbudgeteuro: {}".format(type(e).__name__))
            pass

        try:
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass    

        try:
            category = ''
            test_category = page_details.find_element(By.XPATH, '//*[contains(text(),"Κωδικοί CPV")]//following::dd[1]').text 
            test_category = test_category.split('\n')
            for itrator in test_category:
                category += itrator.split('-')[1].strip()
                category += ','

                cpvs_data = cpvs()
                cpvs_data.cpv_code = itrator.split('-')[0].strip()
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
            notice_data.category = category.rstrip(',')
        except Exception as e:
            logging.info("Exception in notice_url_1: {}".format(type(e).__name__))
            pass

        try:
            notice_url_1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Όνομα Αναθέτουσας Αρχής:")]//following::dd[1]/a').get_attribute("href")   
            fn.load_page(page_details1,notice_url_1,80)
            logging.info(notice_url_1)
            time.sleep(3)
        except Exception as e:
            logging.info("Exception in notice_url_1: {}".format(type(e).__name__))
            pass

        try:
            cookies_close_click_3 = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="cookieModalConsent"]'))).click()  
            time.sleep(3)
        except:
            pass

        try:              
            customer_details_data = customer_details()

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3)').text 


            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Κωδικοί NUTS")]//following::dd[1]').text 
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.contact_person = page_details1.find_element(By.XPATH, '//*[contains(text(),"Αρχικά Αναθέτουσας Αρχής")]//following::dd[1]').text  
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Διεύθυνση:")]//following::dd[1]').text 
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Ταχυδρομικός Κώδικας")]//following::dd[1]').text 
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Πόλη:")]//following::dd[1]').text  
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Διεύθυνση η-Ταχυδρομείου (email)")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Αριθμός Τηλεφώνου")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Αριθμός Τηλεομοιοτυπικού")]//following::dd[1]').text  
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.type_of_authority_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Είδος Αναθέτουσας Αρχής")]//following::dd[1]').text  
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass            

            try:
                customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Δικτυακός Τόπος")]//following::dd[1]').text  
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'CY'
            customer_details_data.org_language = 'EL'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:              
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td._T01_10'):
                attachments_data = attachments()
                attachments_data.file_type = 'PDF'

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a > img').get_attribute("title") 

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass


        try:              
            lots = page_details.find_element(By.CSS_SELECTOR, '#Content > dl').text
            lots = lots.split('Όνομα τμήματος')

            lot_number = 1

            for lot in lots[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_title = lot.split('\n')[1]

                try:
                    if '-' in lot:
                        lot_details_data.lot_actual_number = lot_details_data.lot_title.split('-')[0].strip()
                    elif ':' in lot:
                        lot_details_data.lot_actual_number = lot_details_data.lot_title.split(':')[0].strip()
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual


                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass    
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.eprocurement.gov.cy/epps/viewCFTSAction.do?title=&uniqueId=&contractAuthority=&status=cft.status.tender.submission&status=cft.status.tender.submission&contractType=&contractType=&cpcCategory=&cpcCategory=&procedure=&procedure=&submissionFromDate=&submissionUntilDate=&description=&description=&CPVCodes=&cpvLabels=&estimatedValueMin=&estimatedValueMax=&publicationInvitationFromDate='+today+'&publicationInvitationUntilDate='+today+'&tenderOpeningFromDate=&tenderOpeningUntilDate="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            cookies_close_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="cookieModalConsent"]'))).click()
            time.sleep(2)
        except:
            pass
        
        try:
            filter_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'th.extra > a'))).click()    
            time.sleep(2)
        except:
            pass
        
        try:
            information_area_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CFTResults > div.tableSet > div > p:nth-child(2) > label > input'))).click()    
            time.sleep(2)
        except:
            pass
        
        try:
            condition_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CFTResults > div.tableSet > div > p:nth-child(3) > label > input'))).click()    
            time.sleep(2)
        except:
            pass
        
        try:
            limit_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CFTResults > div.tableSet > div > p:nth-child(4) > label > input'))).click()    
            time.sleep(2)
        except:
            pass
        
        try:
            pdf_announcement_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CFTResults > div.tableSet > div > p:nth-child(5) > label > input'))).click()    
            time.sleep(2)
        except:
            pass
        
        try:
            date_of_assignment_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CFTResults > div.tableSet > div > p:nth-child(6) > label > input'))).click()    
            time.sleep(2)
        except:
            pass
        index_list = [2,3,9,10,11]
        for itrator in index_list:
            per_page = Select(page_main.find_element(By.ID, 'Status'))
            per_page.select_by_index(itrator)
            time.sleep(5)
            test_click =  WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#button_line > p > input:nth-child(1)'))).click() 
            time.sleep(2)
            try:
                for page_no in range(1,10):
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="T01"]/tbody/tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break
    
                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
    
                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CFTResults > div.Pagination > p:nth-child(2) > button:nth-child(5)')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="T01"]/tbody/tr'),page_check))
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
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
