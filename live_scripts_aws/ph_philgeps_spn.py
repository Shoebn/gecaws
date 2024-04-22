from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ph_philgeps_spn"
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
import gec_common.Doc_Download


#Note : Below is the identified format for lot .. "https://notices.philgeps.gov.ph/GEPSNONPILOT/Tender/SplashBidNoticeAbstractUI.aspx?menuIndex=3&refID=10119026&Result=3"


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "ph_philgeps_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'ph_philgeps_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PH'
    notice_data.performance_country.append(performance_country_data)
    

    notice_data.currency = 'PHP'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.main_language = 'EN'
    
    # Onsite Field -Publish
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+ [apAP][mM]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -Title
    # Onsite Comment -pass the textform as a title from  hyperlink of notice url

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4) ').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -pass the hyperlink as a  notice url from title

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    # Onsite Field -Reference Number
    # Onsite Comment -None
    
    # Onsite Field -Solicitation Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = WebDriverWait(page_details, 150).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"Reference Number")]//following::td[1]'))).text
    except:
        try:
            notice_data.notice_no = WebDriverWait(page_details, 150).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"Solicitation Number")]//following::td[1]'))).text
        except:
            try:
                notice_data.notice_no = re.findall('\d{8}',notice_data.notice_url)[0]
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass
            
    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, '#lblHeader').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    
    # Onsite Field -Procurement Mode
    # Onsite Comment -Note:splite a deta forth of dash (Ex.,Negotiated Procurement - Small Value Procurement (Sec. 53.9) "Splite=Negotiated Procurement")

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Mode")]//following::td[1]').text
        type_of_procedure_actual = notice_data.type_of_procedure_actual.replace(' (Sec. 53.9)','').strip()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/ph_philgeps_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]/span').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description[:4300])
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Table6 > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Approved Budget for the Contract
    # Onsite Comment -None

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Approved Budget for the Contract")]//following::td[1]').text
        netbudgetlc = re.sub("[^\d\.\,]", "",netbudgetlc)
        netbudgetlc = netbudgetlc.replace(',','').strip()
        notice_data.netbudgetlc = float(netbudgetlc)
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Classification
    # Onsite Comment -Note:Replece("Googs=Supply","Civil Works=Works")

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Classification")]//following::td[1]').text
        if "Civil Works" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        elif "Goods" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Delivery Period
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Delivery Period")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Pre-bid Conference >> Date
    # Onsite Comment -Note:Available than tack

    try:
        pre_bid_meeting_date = page_details.find_element(By.CSS_SELECTOR, '#dgPreBidTD  tbody > tr:nth-child(2) > td:nth-child(1)').text
        pre_bid_meeting_date = re.findall('\d+/\d+/\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    try:
        category = page_details.find_element(By.XPATH, '//*[contains(text(),"Category")]//following::span[1]').text.lower()
        notice_data.category = fn.CPV_mapping("assets/ph_philgeps_spn_categorymap.csv",category)[0]
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Date Created")]//following::td[1]''').text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        
        # Onsite Field -Procuring Entity
        # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Procuring Entity")]//following::td[1]').text
        
        # Onsite Field -Contact Person
        # Onsite Comment -Note:splite and remove: tel No, email id and contact person  from org address and (removed data take  in ( "org_phone , "org_email", "contect person " field )

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::td[1]').text.split("63")[0]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact Person
        # Onsite Comment -Note:splite phone number from Contact Person field

        try:
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::td[1]').text
            customer_details_data.org_phone = re.findall('\d{2}-\d+-\d+',org_phone)[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact Person
        # Onsite Comment -Note:splite email from Contact Person field

        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::td[1]').text
            customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Area of Delivery
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Area of Delivery")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::td[1]').text.split("\n")[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_country = 'PH'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Description > Line Items
# Onsite Comment -None

    try:     
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#dgDocs > tbody > tr')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Description > Line Items > Item No
        # Onsite Comment -None

        
        # Onsite Field -Description > Line Items > Product/Service Name
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        
        # Onsite Field -Description > Line Items > Description
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description > Line Items > Budget (PHP)
        # Onsite Comment -None

            try:
                lot_netbudget_lc = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(6)').text
                lot_netbudget_lc = re.sub("[^\d\.\,]", "",lot_netbudget_lc)
                lot_netbudget_lc = lot_netbudget_lc.replace(',','').strip()
                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description > Line Items > Quantity
        # Onsite Comment -None

            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Description > Line Items > UOM
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
    
        # Onsite Field -Classification
        # Onsite Comment -Note:Replece("Googs=Supply","Civil Works=Works")

            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.file_name = "Printable Version"
        # Onsite Field -Printable Version
        # Onsite Comment -None
        
        # Onsite Field -Printable Version
        # Onsite Comment -None
        
        attach = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a.A').get_attribute('href')
        data = attach.split("'")[1].split("'")[0]
        
        attachments_data.external_url = 'https://notices.philgeps.gov.ph/GEPSNONPILOT/Tender/PrintableBidNoticeAbstractUI.aspx?refid='+ str(data)
        
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
    urls = ["https://notices.philgeps.gov.ph/GEPSNONPILOT/Tender/SplashOpportunitiesSearchUI.aspx?menuIndex=3&ClickFrom=OpenOpp&Result=3"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,350):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dgSearchResult"]/tbody/tr'))).text
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#pgCtrlDetailedSearch_nextLB")))
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
