from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ph_philgeps_ca"
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
SCRIPT_NAME = "ph_philgeps_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()

    notice_data.script_name = 'ph_philgeps_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'PHP'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Published Date
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Published Date")]//following::div[1]').text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Award Notice No
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Award Notice No")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Notice Title")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Notice Title
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Approved Budget
    # Onsite Comment -None

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Approved Budget")]//following::div[1]').text
        netbudgetlc = re.sub("[^\d\.\,]", "",netbudgetlc)
        netbudgetlc = netbudgetlc.replace(',','').strip()
        notice_data.netbudgetlc = float(netbudgetlc)
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -Approved Budget
    # Onsite Comment -None

    try:
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass       
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ext-gen30 > table > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    
    # Onsite Field -Classification
    # Onsite Comment -Note:Replece("Goods=Supply","Civil Works=Works")

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Classification")]//following::div[1]').text
        if "Civil Works" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        elif "Goods" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Award Type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Award Type")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Delivery Period
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Delivery Period")]//following::div[1]|//*[contains(text(),"Contract Duration:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Funding Source
    # Onsite Comment -None

    try:
        notice_data.source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Funding Source")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Mode
    # Onsite Comment -Note: Take data before first '-'

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Mode")]//following::div[1]').text.strip()
        type_of_procedure_actual = notice_data.type_of_procedure_actual.replace('(Sec. 53.9)','').strip()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/ph_philgeps_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract No.:")]//following::div[1]').text.strip() 
        if related_tender_id == "N/A":
            pass
        else:
            notice_data.related_tender_id = related_tender_id
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Effectivity Date:")]//following::div[1]').text
        tender_contract_start_date =re.findall('\d+-\w+-\d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass


    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract End Date:")]//following::div[1]').text
        tender_contract_end_date = re.findall('\d+-\w+-\d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Date Created:")]//following::div[1]''').text
        dispatch_date = re.findall('\d+-\w+-\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = page_details.find_element(By.XPATH, '/html/body/div[3]/div/div/div/div/div/div[2]/div/div[2]/div/div/div/table/tbody/tr/td[2]/div/div/div/div[1]/div/div/div[1]/div').text

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '/html/body/div[3]/div/div/div/div/div/div[2]/div/div[2]/div/div/div/table/tbody/tr/td[2]/div/div/div/div[1]/div/div/div[2]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        # Onsite Field -Contact Person
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Contact Person:")])[1]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        # Onsite Field -Area Of Delivery
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Area Of Delivery")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'PH'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -View Documents
# Onsite Comment -None

    try:
        clk1 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a#ext-comp-1039.x-form-field")))
        clk1.location_once_scrolled_into_view
        clk1.click()
        time.sleep(5)
    except:
        try:
            clk1 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a#ext-comp-1035.x-form-field")))
            clk1.location_once_scrolled_into_view
            clk1.click()
            time.sleep(5)
        except:
            pass    
    
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody:nth-child(2) > tr.x-tree-node-el.x-tree-node-expanded > td > a > span')))
    except:
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tbody > tr.x-tree-node-ct > td > table > tbody a'):
            attachments_data = attachments()
        # Onsite Field -Document Name
        # Onsite Comment -Note:split file_name.eg.,"BAC_RES_295.pdf" don't take ".pdf" in file_name.

            attachments_data.file_name = single_record.text.split(".")[0]
            
        # Onsite Field -Document Name
        # Onsite Comment -Note:split the extention (like ".pdf" / ".doc" / ".jpg" / ".jpeg") from "Document Name" field

            try:
                attachments_data.file_type = single_record.text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            # Onsite Field -Document Name
            # Onsite Comment -None
            
            external = single_record.click()
            time.sleep(5)
            external_url = page_details.find_element(By.XPATH, '//object').get_attribute("data")
            attachments_data.external_url = external_url
            close_click = page_details.find_element(By.XPATH, '/html/body/div[14]/div[1]/div/div/div/div[1]').click()
            time.sleep(2)
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        clk1 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"Close")))
        clk1.location_once_scrolled_into_view
        clk1.click()
        time.sleep(5)
    except:
        pass  
    
# Onsite Field -Line Items
# Onsite Comment -None

    try:          
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.contract_type = notice_contract_type
        # Onsite Field -Line Items > Item No
        # Onsite Comment -None

        try:
            lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'td.x-grid3-col.x-grid3-cell.x-grid3-td-0.x-grid3-cell-first').text
        except Exception as e:
            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
            pass

        # Onsite Field -Line Items > Product/Service Name
        # Onsite Comment -None

        try:
            lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, ' td.x-grid3-col.x-grid3-cell.x-grid3-td-1 > div').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Line Items > Budget
        # Onsite Comment -None

        try:
            lot_netbudget_lc = page_details.find_element(By.CSS_SELECTOR, ' td.x-grid3-col.x-grid3-cell.x-grid3-td-2.x-grid3-cell-last > div').text
            lot_netbudget_lc = re.sub("[^\d\.\,]", "",lot_netbudget_lc)
            lot_netbudget_lc = lot_netbudget_lc.replace(',','').strip()
            lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
        except Exception as e:
            logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
            pass

        # Onsite Field -Classification
        # Onsite Comment -Note:Replece("Goods=Supply","Civil Works=Works")

        try:
            award_details_data = award_details()

                # Onsite Field -Awardee
                # Onsite Comment -None

            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Awardee")]//following::div[1]').text

            try:
                award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::div[1]').text
            except:
                pass

            try:
                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Award Date")]//following::div[1]').text
                award_date = re.findall('\d+-\w+-\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d-%b-%Y').strftime('%Y/%m/%d')
            except:
                pass
            
            try:
                netawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Amount:")]//following::div[1]').text
                netawardvaluelc = re.sub("[^\d\.\,]", "",netawardvaluelc)
                netawardvaluelc = netawardvaluelc.replace(',','').strip()
                award_details_data.netawardvaluelc = float(netawardvaluelc)
            except Exception as e:
                logging.info("Exception in netawardvaluelc: {}".format(type(e).__name__))
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
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://notices.philgeps.gov.ph/GEPSNONPILOT/Tender/RecentAwardNoticeUI.aspx?menuIndex=3&DirectFrom=RecentAwardDetail"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dgSearchResult"]/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dgSearchResult"]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dgSearchResult"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    if notice_count == 50:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="dgSearchResult"]/tbody/tr[2]'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
   
    output_json_file.copyFinalJSONToServer(output_json_folder)
