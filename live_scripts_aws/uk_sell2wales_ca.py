from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uk_sell2wales_ca"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_sell2wales_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'uk_sell2wales_ca'
    
    notice_data.main_language = 'EN'
    
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'GBP'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -Reference
    # Onsite Comment -split data from "Reference No" to "Published By" for tender no.  
  
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_grdResults > tbody > tr:nth-child(n) > td:nth-child(2)').text.split("Reference No:")[1].split("\n")[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -just take title remove "a" tag
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) >a').text
        notice_data.notice_title = notice_data.local_title
        if len(notice_data.local_title) < 5:
            clk = page_details.find_element(By.LINK_TEXT, 'Coding').click()
            notice_data.local_title = page_details.find_element(By.CSS_SELECTOR,'#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_notice_coding1_grdCategories > tbody > tr:nth-child(2) > td:nth-child(3)').text
            notice_data.notice_title =notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) >a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_RadMultiPage1').get_attribute("outerHTML")                     
    
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -----In detail page click on "Introduction" for short description
    # Onsite Comment -map ref "/images/subcontractflag.gif, /images/subcontractflag.gif"  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441660"

    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
                   
    # Onsite Field -Published By:
    # Onsite Comment -split data from "Published By" to "Deadline Date" for publish_date

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Publication Date:")]//following::td[1]').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline Date:
    # Onsite Comment -split data from "Deadline Date" to "Notice Type:" for tender no.

    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_Page1 > div > div:nth-child(1) > table > tbody > tr:nth-child(6) > td:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
   
     # Onsite Field -In detail page click on "Introduction" and select data---Notice Type:
    # Onsite Comment -map ref "/images/FtsNoticeflag.gif ",  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686"
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice Type:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Introduction" and select data
    # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_Page1 > div > div:nth-child(2) a')[1:2]:
            attachments_data = attachments()
            
        # Onsite Field -In detail page click on "Introduction" and select data for "file_name"
        # Onsite Comment -None

            attachments_data.file_name = single_record.text
        # Onsite Field -In detail page click on "Introduction" and select data for "external url"
        # Onsite Comment -None
            external_url = single_record.click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#Tab2 > span > span > span")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(2)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div:nth-child(1) > table > tbody > tr:nth-child(1) > td:nth-child(1) > strong')))
    except:
        pass
    
    # Onsite Field -In detail page click on "Full Notice Text" for "grossbudgetlc" ---II.1.5) Estimated total value
    # Onsite Comment -map ref "/images/FtsNoticeflag.gif ",  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686"

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.5) Estimated total value")]//following::p[1]').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Full Notice Text" for "grossbudgetlc" ---II.1.5) Estimated total value
    # Onsite Comment -map ref "/images/FtsNoticeflag.gif ",  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686"

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -notice type
    # Onsite Comment -split data from "Notice Type:" to "OCID" for notice_type

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.3) Type of contract")]//following::p[1]').text
        if "Services" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Service"
        elif  "Works" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Works"
        elif  "Supplies" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -dispatch date
    # Onsite Comment -map ref "/images/FtsNoticeflag.gif ",  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686"

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of dispatch")]//following::p[1]').text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -II.1.4) Short description ----In detail page click on "Full Notice Text" for short description
    # Onsite Comment -map ref "/images/FtsNoticeflag.gif ", ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686"

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Short description")]//following::p[1]').text
        if len(notice_data.notice_summary_english) < 5:
            clk = page_details.find_element(By.LINK_TEXT, 'Coding').click()
            notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR,'#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_notice_coding1_grdCategories > tbody > tr:nth-child(2) > td:nth-child(3)').text
    except Exception as e:
        notice_data.notice_summary_english = notice_data.notice_title
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Short description")]//following::p[1]').text
    except Exception as e:
        notice_data.local_description = notice_data.notice_summary_english
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Full Notice Text"
    # Onsite Comment -map ref "/images/FtsNoticeflag.gif, /images/euroflag.gif", ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of Procedure")]//following::span[1]').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/uk_sell2wales_ca_procedure.csv",type_of_procedure_actual)
    except:
        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of procedure")]//following::p[1]').text
            type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/uk_sell2wales_ca_procedure.csv",type_of_procedure_actual)            
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'GB'
        
        # Onsite Field -map ref "/images/FtsNoticeflag.gif, /images/euroflag.gif", ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686
        # Onsite Comment -In detail page click on "Full Notice Text" and select data---I.1) Name and addresses
        
         # Onsite Field -map ref "/images/subcontractflag.gif, /images/sitenoticeflag.gif"  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441660"
        # Onsite Comment -In detail page click on "Full Notice Text" and select data---I.1) Name and addresses

        try:
            customer_details_data.org_name = tender_html_element.text.split('Published By: ')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        # Onsite Field -map ref "/images/FtsNoticeflag.gif, /images/euroflag.gif", ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686
        # Onsite Comment -just select address split data from "Name and addresses" till "Contact person"
        
         # Onsite Field -map ref "/images/subcontractflag.gif, /images/sitenoticeflag.gif"  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441660"
        # Onsite Comment -grab data of "Postal address, Town" fromPurchasing Organisation Name and Address"

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name and addresses")]//following::div [1]').text.split("Contact person:")[0].split("Telephone: ")[0].strip()
        except:
            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Address:")]//following::span[1]').text
            except Exception as e:  
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -map ref "/images/FtsNoticeflag.gif, /images/euroflag.gif", ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686
        # Onsite Comment -split data between "Telephone" and "Email" in "org_phone"
        
           # Onsite Field -map ref "/images/subcontractflag.gif, /images/sitenoticeflag.gif"  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441660"
        # Onsite Comment -grab data from "telephone"

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name and addresses")]//following::div [1]').text.split("Telephone:")[1].split("\n")[0].strip()
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(5) tr:nth-child(4) > td:nth-child(2)').text.split("Telephone:")[1].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
            
     # Onsite Field -map ref "/images/subcontractflag.gif, /images/sitenoticeflag.gif"  ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441660"
        # Onsite Comment -grab data from "E-Mail:"

        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(5) > p:nth-child(7)').text.split("E-mail:")[1].strip()
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'td tr:nth-child(5) > td:nth-child(1)').text.split("E-Mail:")[1].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split data between "NUTS" and "Internet address(es)" in customer_NUTS
        # Onsite Comment -map ref "/images/FtsNoticeflag.gif, /images/euroflag.gif", ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(5) > p:nth-child(8)').text.split("NUTS:")[1]
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -map ref "/images/FtsNoticeflag.gif, /images/euroflag.gif", ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686
        # Onsite Comment -split data between "Contact person" and "Telephone" in contact_person

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name and addresses")]//following::div [1]').text.split("Contact person: ")[1].split("E-mail:")[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1

        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        lot_details_data.lot_grossbudget = notice_data.est_amount
        
        try:
            lot_details_data.lot_description = notice_data.local_description
        except Exception as e:
            lot_details_data.lot_description = notice_data.notice_summary_english
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass

        try:
            lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.7) Duration of the contract, ")]//following::p[1]').text.split("Duration in months:")[1]
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

        notice_text_data1= page_details.find_element(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_RadMultiPage1').text
        if "V.2.3) Name and address of the contractor" in notice_text_data1 or "Official Name:" in notice_text_data1:

            award_details_data = award_details()
            if 'V.2.3) Name and address of the contractor' in notice_text_data1:
                award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3) Name and address of the contractor")]//following::p[1]').text
            else:
                award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'table > tbody > tr:nth-child(15)   tr:nth-child(1) > td > span').text

            try:
                grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"nformation on value of the concession and main ")]//following::p[1]').text
                grossawardvaluelc = re.sub("[^\d\.\,]", "", grossawardvaluelc)
                award_details_data.grossawardvaluelc = float(grossawardvaluelc)
            except:
                try:
                    grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.4) Information on value of the contract/lot (excluding VAT)")]//following::p[1]').text
                    grossawardvaluelc = re.sub("[^\d\.\,]", "", grossawardvaluelc)
                    award_details_data.grossawardvaluelc = float(grossawardvaluelc)
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass

            try:
                award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"address of the contractor")]//following::p[2]').text
            except:
                try:
                    award_details_data.address = page_details.find_element(By.CSS_SELECTOR, ' table > tbody > tr:nth-child(15)  tr:nth-child(2) > td > span').text
                except Exception as e:
                    logging.info("Exception in address: {}".format(type(e).__name__))
                    pass
            try:
                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of Contract Award")]//following::span[1]').text
                award_date = re.findall('\d+-\d+-\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d-%m-%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass   

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

        # Onsite Field -map ref "/images/FtsNoticeflag.gif, /images/euroflag.gif", ref url "https://www.sell2wales.gov.wales/search/show/search_view.aspx?ID=JUN441686
        # Onsite Comment -None

    try:
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text()," Information about European Union funds")]//following::p[1]').text.split("The procurement is related to a project and/or programme financed by European Union funds:")[1]
        if 'Yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 7794645
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass
        

 # Onsite Field -Award criteria
# Onsite Comment -None

    try:
        tender_cri=page_details.find_element(By.CSS_SELECTOR,'#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_Page2').text
        if 'Award criteria' in tender_cri:
            tender_cri1 = tender_cri.split('Award criteria')[1].split('II.')[0].strip()
            for l in tender_cri1.split('\n'):
                tender_criteria_data = tender_criteria()
                tender_criteria_data.tender_criteria_title = l.split('/ Weighting:')[0]
                tender_criteria_weight = l.split('Weighting:')[1].split('\n')[0]
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
 
    try:
        cpvs_data = cpvs()
        cpvs_data.cpv_code  = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV ")]//following::p[1]').text
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv: {}".format(type(e).__name__)) 
        pass

    
    try:
        for single_record in page_details.find_elements(By.XPATH,'//*[contains(text(),"Additional CPV code(s)")]//following::p'):
            single_cpv = single_record.text
            if 'NUTS code:' not in single_cpv:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = single_cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

            if 'NUTS code:' in single_cpv:
                break
            else: 
                pass       
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR,' table:nth-child(3) > tbody > tr:nth-child(n) > td:nth-child(2) > span'):
            cpvs_data = cpvs()
            cpvs_data.cpv_code = single_record.text
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.sell2wales.gov.wales/Search/search_mainpage.aspx'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        pp_btn = Select(page_main.find_element(By.ID,'ctl00_ContentPlaceHolder1_cboDocType'))
        pp_btn.select_by_index(3)
        
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#ctl00_ContentPlaceHolder1_cmdSearch")))
            page_main.execute_script("arguments[0].click();",click)
            time.sleep(2)
        except:
            pass
        
        try:
            WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' tr.GridHeader > th:nth-child(2)')))
        except:
            pass
        
        for page_no in range(1,7):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_ContentPlaceHolder1_grdResults"]/tbody/tr[2]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_grdResults"]/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_grdResults"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.ID,"ctl00_ContentPlaceHolder1_NavBar2_cmdNext")))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl00_ContentPlaceHolder1_grdResults"]/tbody/tr[2]'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
