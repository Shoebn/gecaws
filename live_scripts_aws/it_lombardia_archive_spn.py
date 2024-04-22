from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_lombardia_archive_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
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
SCRIPT_NAME = "it_lombardia_archive_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    notice_data.script_name = 'it_lombardia_archive_spn'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.additional_source_name = 'ARIA'

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        codice_gara = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if codice_gara=='.':
            codice_gara = codice_gara.replace('.','')
        else:
            codice_gara =codice_gara
    except:
        pass
    
    try:
        if codice_gara!='':
            local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            notice_data.local_title = local_title.replace(codice_gara,'').replace('-','').replace('_','').replace('-','').strip()
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        else:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute("href")
        fn.load_page(page_details, notice_data.notice_url, 80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('=')[1].strip()
        except:
            try:
                notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
        publish_date = re.findall('\d+/\d+/\d{4}', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(11)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_lombardia_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount_data = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount_data)
        notice_data.est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(notice_data.est_amount)
        if "€" in est_amount_data:
            notice_data.netbudgetlc = notice_data.est_amount
            notice_data.netbudgeteuro= notice_data.est_amount
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    try:
        Select(WebDriverWait(page_details, 12).until(EC.element_to_be_clickable((By.XPATH, '//select[@class="paginationCustomButton"]')))).select_by_value('200')
    except:
        pass
    time.sleep(3)
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > section > div').get_attribute("outerHTML")
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_data.category = page_details.find_element(By.XPATH,'//*[contains(text(),"CATEGORIE MERCEOLOGICHE:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[@id="only-one"]/section[1]/div/article[2]//a').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'AMBITO DELLA PROCEDURA:')]//following::div[1]").text        
        if "Procedura per lavori" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "Procedura per forniture/servizi" in notice_data.contract_type_actual or "Procedura per incarichi a liberi professionisti" in notice_data.contract_type_actual or "Procedure per concessioni" in notice_data.contract_type_actual or "Procedure per concorsi pubblici di progettazione" in notice_data.contract_type_actual or "Procedure per servizi sociali e altri servizi" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Procedura per forniture" in notice_data.contract_type_actual or "Procedura per dispositivi medici" in notice_data.contract_type_actual or "Procedura per forniture/servizi ferroviari" in notice_data.contract_type_actual or "Procedura per farmaci" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH,'//*[contains(text(),"STAZIONE APPALTANTE:")]//following::div[1]').text
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass

    try:
        lenth = page_details.find_element(By.XPATH, '//*[@id="j_idt161:j_idt233"]/a[last()]').text
    except:
        lenth = ''
    time.sleep(2)
    
    try:
        if lenth == '':
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#result > tbody > tr'):
                try:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number
                    try:
                        lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
                    except:
                        try:
                            lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
                        except Exception as e:
                            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                            pass
    
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                    
                    try:
                        lot_grossbudget_data = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
                        lot_grossbudget_lc = re.sub("[^\d\.\,]", "", lot_grossbudget_data)
                        if "€" in lot_grossbudget_data:
                            lot_details_data.lot_netbudget_lc = float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
                            lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
                    except Exception as e:
                        logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                        pass
                    
                    try:
                        lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'AMBITO DELLA PROCEDURA:')]//following::div[1]").text

                        if "Procedura per lavori" in lot_details_data.lot_contract_type_actual:
                            lot_details_data.contract_type = "Works"
                        elif "Procedura per forniture/servizi" in lot_details_data.lot_contract_type_actual or "Procedura per incarichi a liberi professionisti" in lot_details_data.lot_contract_type_actual or "Procedure per concessioni" in lot_details_data.lot_contract_type_actual or "Procedure per concorsi pubblici di progettazione" in lot_details_data.lot_contract_type_actual or "Procedure per servizi sociali e altri servizi" in lot_details_data.lot_contract_type_actual:
                            lot_details_data.contract_type = "Service"
                        elif "Procedura per forniture" in lot_details_data.lot_contract_type_actual or "Procedura per dispositivi medici" in lot_details_data.lot_contract_type_actual or "Procedura per forniture/servizi ferroviari" in lot_details_data.lot_contract_type_actual or "Procedura per farmaci" in lot_details_data.lot_contract_type_actual:
                            lot_details_data.contract_type = "Supply"
                    except Exception as e:
                        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                        pass
    
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
                except:
                    pass
        else:
            for i in range(1, int(lenth) + 1):
                lot_number = 1
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#result > tbody > tr'):
                    try:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
    
                        try:
                            lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
                        except:
                            try:
                                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
                            except Exception as e:
                                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                                pass
    
                        lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                        lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
    
    
                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "", lot_grossbudget_lc)
                            lot_details_data.lot_netbudget_lc = float(lot_grossbudget_lc.replace('.', '').replace(',', '.').strip())
                        except Exception as e:
                            logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                            pass
                        
                        try:
                            lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'AMBITO DELLA PROCEDURA:')]//following::div[1]").text
                            if "Procedura per lavori" in lot_details_data.lot_contract_type_actual:
                                lot_details_data.contract_type = "Works"
                            elif "Procedura per forniture/servizi" in lot_details_data.lot_contract_type_actual or "Procedura per incarichi a liberi professionisti" in lot_details_data.lot_contract_type_actual or "Procedure per concessioni" in lot_details_data.lot_contract_type_actual or "Procedure per concorsi pubblici di progettazione" in lot_details_data.lot_contract_type_actual or "Procedure per servizi sociali e altri servizi" in lot_details_data.lot_contract_type_actual:
                                lot_details_data.contract_type = "Service"
                            elif "Procedura per forniture" in lot_details_data.lot_contract_type_actual or "Procedura per dispositivi medici" in lot_details_data.lot_contract_type_actual or "Procedura per forniture/servizi ferroviari" in lot_details_data.lot_contract_type_actual or "Procedura per farmaci" in lot_details_data.lot_contract_type_actual:
                                lot_details_data.contract_type = "Supply"
                        except Exception as e:
                            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                            pass
                        
    
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                    except:
                        pass
                try:
                    next_btn = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, str(i + 1))))
                    next_btn.click()
                except:
                    pass
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__))
        pass

    try:
        Allegati_click = page_details.find_element(By.XPATH, '//img[@class="icon-copy"]')
        page_details.execute_script("arguments[0].click();", Allegati_click)
        time.sleep(5)
    except:
        pass
        
    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="j_idt146"]/article/a'):
            try:
                attachments_data = attachments()
                try:
                    file_type = single_record.text
                    if '.' in file_type:
                        attachments_data.file_type = single_record.text.split('.')[-1]
                    else:
                        attachments_data.file_type = 'zip'
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass
    
                attachments_data.file_name = single_record.text
                
                attachments_data.external_url = single_record.click()
                time.sleep(5)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            except:
                pass
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')

# ----------------------------------------- Main Body
arguments = ['--incognito', 'ignore-certificate-errors', 'allow-insecure-localhost', '--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = Doc_Download.page_details
page_details.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%d/%m/%Y')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.sintel.regione.lombardia.it/eprocdata/sintelSearch.xhtml']
    url_retry = 1
    for url in urls:
        fn.load_page(page_main, url, 10)
        logging.info('----------------------------------')
        logging.info(url)
        
        time.sleep(2)
        page_main.find_element(By.XPATH, '//div[@id="auctionStateArrow"]').click()
        lst = [0,1,3,7,8,9,11,13]
        for no in lst:
            pp_btn = page_main.find_elements(By.XPATH, '//ul[@id="auctionStatus"]//li')[no]
            pp_btn.click()
            time.sleep(3)
        
        page_main.find_element(By.XPATH, '//div[@id="auctionStateArrow"]').click()
        time.sleep(2)
        
        page_main.find_element(By.XPATH, '/html/body/section/div/div/form/div/div[2]/div/div[8]/div[1]/div/button').click()
        time.sleep(2)
        
        select_month = Select(page_main.find_element(By.XPATH,'//*[@id="ui-datepicker-div"]/div/div/select[1]'))
        select_month.select_by_value('0')
        time.sleep(2)
        
        select_month = Select(page_main.find_element(By.XPATH,'//*[@id="ui-datepicker-div"]/div/div/select[2]'))
        select_month.select_by_value('2022')
        time.sleep(2) 
        
        dates = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ui-datepicker-div"]/table/tbody/tr[1]/td[7]/a')))
        page_main.execute_script("arguments[0].click();", dates)
        time.sleep(3)
        
        #************************************************************************************to date
        
        page_main.find_element(By.XPATH, '/html/body/section/div/div/form/div/div[2]/div/div[8]/div[2]/div/button').click()
        time.sleep(2)
        
        select_month = Select(page_main.find_element(By.XPATH,'//*[@id="ui-datepicker-div"]/div/div/select[1]'))
        select_month.select_by_value('2')
        time.sleep(2)
        
        select_month = Select(page_main.find_element(By.XPATH,'//*[@id="ui-datepicker-div"]/div/div/select[2]'))
        select_month.select_by_value('2024')
        time.sleep(2) 
        
        dates = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ui-datepicker-div"]/table/tbody/tr[5]/td[4]/a')))
        page_main.execute_script("arguments[0].click();", dates)
        time.sleep(3)

        try:
            page_main.find_element(By.XPATH, '//input[@value="Applica"]').click()
        except:
            page_main.find_element(By.XPATH, '//input[@value="Applica"]').click()
        time.sleep(7)

        for i in  range(1,5):
            i = page_main.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        select_record = Select(page_main.find_element(By.XPATH,'/html/body/div[10]/div/div/div/form/select'))
        select_record.select_by_value('200')
        time.sleep(2)
        
        for page_no in range(2,50):#50
            page_check = WebDriverWait(page_main,180).until(EC.presence_of_element_located((By.XPATH, '//*[@id="result"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                time.sleep(2)
                tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break   
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
                    
                if notice_count == 50:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0

            try:
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT, str(page_no))))
                page_main.execute_script("arguments[0].click();", next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="result"]/tbody/tr'), page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:" + str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
