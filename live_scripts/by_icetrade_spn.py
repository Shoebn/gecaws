from gec_common.gecclass import *
import logging
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
SCRIPT_NAME = "by_icetrade_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'by_icetrade_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BY'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'BYR'
    notice_data.main_language = 'RU'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.est_amount = re.findall(r'\d{1,3}(?:[ ,]\d{3})*(?:\.\d+)?',est_amount)[0]
        if ' ' in notice_data.est_amount:
            notice_data.est_amount =notice_data.est_amount.replace(' ','')
        if ',' in notice_data.est_amount:
            notice_data.est_amount =notice_data.est_amount.replace(',','')
        notice_data.est_amount=float(notice_data.est_amount)
        notice_data.netbudgetlc=notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    try:
        notice_data.notice_url  = notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1) a").get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Краткое описание предмета закупки")]//following::td[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        pass
    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Отрасль')]//following::td[1]").text
        notice_data.contract_type_actual = notice_data.contract_type_actual.split(' > ')[1]
        notice_data.contract_type_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        notice_data.notice_contract_type = notice_data.contract_type_actual
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = org_name
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH,'//*[contains(text(),"заказчика")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__)) 
            pass        
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH,'//*[contains(text(),"заказчика")]//following::td[1]').text.split('каб.')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
            pass
        try:
            org_email = page_details.find_element(By.XPATH,'//*[contains(text(),"заказчика")]//following::td[1]').text
            customer_details_data.org_email = fn.get_email(org_email)
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__)) 
            pass

        customer_details_data.org_country = 'BY'
        customer_details_data.org_language = 'RU'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        for lot_id in range(1,15):

            lot_number= page_details.find_element(By.CSS_SELECTOR,'#lotRow'+str(lot_id)+'>td:nth-child(1)')
            if lot_number != '' or lot_number is not None:
                lot_details_data = lot_details()
                
                try:
                    lot_number_1= page_details.find_element(By.CSS_SELECTOR,'#lotRow'+str(lot_id)+'>td:nth-child(1)').text
                    lot_details_data.lot_number = int(lot_number_1)
                except:
                    pass
                
                try:
                    lot_details_data.lot_title= page_details.find_element(By.CSS_SELECTOR,'#lotRow'+str(lot_id)+'>td:nth-child(2)').text
                    lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except:
                    pass
                try:
                    lot_netbudget_lc = page_details.find_element(By.CSS_SELECTOR,'#lotRow'+str(lot_id)+'>td:nth-child(3)').text.split(',')[1]
                    lot_details_data.lot_netbudget_lc =re.findall(r'\d+(?: \d+)*',lot_netbudget_lc)[0]
                    lot_details_data.lot_netbudget_lc =lot_details_data.lot_netbudget_lc.replace(' ','')
                    lot_details_data.lot_netbudget_lc =float(lot_details_data.lot_netbudget_lc)
                except Exception as e:
                    logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__)) 
                    pass
                try:
                    lot_quantity = page_details.find_element(By.CSS_SELECTOR,'#lotRow'+str(lot_id)+'>td:nth-child(3)').text.split(',')[0]
                    lot_quantity = re.findall(r'\d{1,9}(?:[ ,]\d{3})*(?:\.\d+)?',lot_quantity)[0]
                    lot_details_data.lot_quantity =lot_details_data.lot_quantity(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__)) 
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
            else:
                pass
                
    except Exception as e:
        logging.info("Exception in lots: {}".format(type(e).__name__)) 
        pass
        
    try:             
        for single_record in page_details.find_elements(By.XPATH,'//*[contains(text(),"Документы")]//following::tr/td/p/a'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.get_attribute('href')

            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR,'#auctBlock > div').get_attribute('outerHTML')
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = webdriver.ChromeOptions()
options.add_extension("Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
page_main = webdriver.Chrome(options=options)
time.sleep(20)


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    urls = ['https://icetrade.by/search/auctions?search_text=&search=%D0%9D%D0%B0%D0%B9%D1%82%D0%B8&zakup_type[1]=1&zakup_type[2]=1&auc_num=&okrb=&company_title=&establishment=0&period=&created_from=&created_to=&request_end_from=&request_end_to=&t[Trade]=1&t[eTrade]=1&t[Request]=1&t[singleSource]=1&t[Auction]=1&t[Other]=1&t[contractingTrades]=1&t[socialOrder]=1&t[negotiations]=1&r[1]=1&r[2]=2&r[7]=7&r[3]=3&r[4]=4&r[6]=6&r[5]=5&sort=num%3Adesc&onPage=100&p=',
           'https://icetrade.by/search/foreign?sort=num%3Adesc&onPage=100&p='] 
    for url2 in urls:
        for page_no in range(1,10):
            url= url2 + str(page_no)
            fn.load_page(page_main, url)
            logging.info('----------------------------------')           
            logging.info(url)

            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#auctions-list > tbody > tr:nth-child(2)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#auctions-list > tbody > tr')))
                length = len(rows)                                                                              
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#auctions-list > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
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
