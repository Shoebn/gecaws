from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_csrn_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_csrn_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'mfa_csrn_spn'
   
    notice_data.main_language = 'EN'
    
    notice_data.currency = 'USD'
    
    notice_data.notice_url = url
    
    # Onsite Field -Project
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_nno from title.	2.here "TA-9923 REG: International PFM Specialist (53363-001)" take "53363-001" in notice_no.

    try:
        notice_no_1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(1)').text
        notice_no  = re.findall('(\d{5}-\d{3})',notice_no_1)[0]
        notice_data.notice_no =notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -View CSRN
    # Onsite Comment -1.split notice_no from url.	2.here "https://selfservice.adb.org/OA_HTML/OA.jsp?page=/adb/oracle/apps/xxcrs/csrn/webui/CsrnHomePG&OAPB=ADBPOS_CMS_ISP_BRAND&_ti=2131469228&oapc=11&oas=AqCerjd8gpoJiE19OI0ujw.." take "2131469228" in notice_no.

    # Onsite Field -Engagement Period
    # Onsite Comment -1.after grabbing the number add "(months)" in front of the number.

    try:
        contract_duration = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(4)').text
        notice_data.contract_duration =contract_duration+' '+'(months)'
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Published
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.x1s:nth-child(5)").text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Deadline  
    # Onsite Comment -None 14-Feb-2024 11:59 PM

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.x1s:nth-child(6)").text
        notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMampm]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -View CSRN
    # Onsite Comment -None

    try:
        page_details_click = WebDriverWait(tender_html_element, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td.x1w:nth-child(7) > a')))
        page_main.execute_script("arguments[0].click();",page_details_click)
        page_url=page_main.current_url
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in page_details_click: {}".format(type(e).__name__))
        pass
    
    try:
        if notice_data.notice_no == None:
            notice_data.notice_no =page_url.split('ti=')[1].split('&')[0].strip()
        else:
            notice_data.notice_no =notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.from page_details take notice_text from this two tabs "Terms of Reference" and "Cost Estimate".
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#plMain > div').get_attribute("outerHTML")                     
    except:
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.if this text contains "Deadline of Submitting EOI" then pass notice_type=5, otherwise pass notice_type=4.

    try:
        notice_type = page_main.find_element(By.CSS_SELECTOR, '#ftPageStatus').text
        if 'Deadline of Submitting EOI' in notice_type:
             notice_data.notice_type = 5
        else:
             notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Source
    # Onsite Comment -1.replace the grabbed keywords with given numbers("National=0","International=1") otherwise pass 2.

    try:
        procurement_method = page_main.find_element(By.XPATH, '//*[contains(text(),"Source")]//following::td[2]').text
        if 'National' in procurement_method:
            notice_data.procurement_method =0
        elif 'International' in  procurement_method:
            notice_data.procurement_method =1
        else:
            notice_data.procurement_method =2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Selection Method
#     # Onsite Comment -None

    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Selection Method")]//following::td[2]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Package Name
    # Onsite Comment -None

    try:
        notice_data.project_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Package Name")]//following::td[2]').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Consulting Services Budget
    # Onsite Comment -1.don't grab currency name.

    try:
        est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Consulting Services Budget")]//following::td[2]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace(',','').strip()
        notice_data.est_amount =float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Country of assignment
#     # Onsite Comment -1.csv file is pulled name as "mfa_csrn_spn_countrycode.csv"	2."Hong Kong, China=CN" and "Regional=PH"       3.if country_name is not present then pass "PH".

    try:
        performance_country1 = page_main.find_element(By.XPATH, '//*[contains(text(),"Country of assignment")]//following::td[2]').text
        performance_country_data = performance_country()
        performance_country_data.performance_country =fn.procedure_mapping("assets/mfa_csrn_spn_countrycode.csv",performance_country1)
        if performance_country_data.performance_country == None:
            performance_country_data.performance_country = 'PH'
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:        
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    try:
        attach=page_main.find_element(By.XPATH, '//*[contains(text(),"CSRN Additional Information / Attachments")]//following::td[2]')
        for single_record in attach.find_elements(By.CSS_SELECTOR, '#AttachmentTable_ATTACH_\/adb\/oracle\/apps\/xxcrs\/csrn\/webui\/CsrnProfilePG\.stlProfile\.EoiAttachmentTable > table.x1o > tbody > tr')[1:]:
            attachments_data = attachments()
        # Onsite Field -CSRN Additional Information / Attachments >> Title
        # Onsite Comment -1.take in text format.

            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a.xh').text
            if '.pdf' in file_name:
                attachments_data.file_name = file_name.split('.')[0].strip()
            else:
                attachments_data.file_name = file_name

            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').click()
            time.sleep(3)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        # Onsite Field -CSRN Additional Information / Attachments >> Description
        # Onsite Comment -None

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try: 
        org_name = page_main.find_element(By.XPATH, '(//*[contains(text(),"Agencies")])[2]//following::tbody[1]')
        org_name1 =''
        for data in org_name.find_elements(By.CSS_SELECTOR, '#atAgency > table.x1o > tbody > tr')[1:]:
            checked = data.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').get_attribute("innerHTML")
            if "Read only Checkbox Checked" in checked:

                customer_details_data = customer_details()
                customer_details_data.org_language = 'EN'
                
                name = data.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                if name not in org_name1:
                    org_name1 += name
                    org_name1 += ','
                    
                    customer_details_data.org_name = name
                    if 'Asian Development Bank' in customer_details_data.org_name:
                        customer_details_data.org_parent_id = '7780104'
                    
                    org_country = data.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    customer_details_data.org_country = fn.procedure_mapping("assets/mfa_csrn_spn_countrycode.csv",org_country)
                    if customer_details_data.org_country == None:
                        customer_details_data.org_country = 'PH'
                        
                    try:
                        contact_person = data.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                        if contact_person == '':
                            try:
                                customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Person for Inquiries")]//following::td[2]').text
                            except:
                                try:
                                    customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::td[5]').text
                                except Exception as e:
                                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                                    pass
                        else:
                            customer_details_data.contact_person = contact_person
                    except Exception as e:
                        logging.info("Exception in contact_person: {}".format(type(e).__name__))
                        pass

                    try:
                        customer_click = WebDriverWait(data, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td.x1w:nth-child(6) > a')))
                        page_main.execute_script("arguments[0].click();",customer_click)
                        page_main.switch_to.window(page_main.window_handles[1])
                        time.sleep(7)
                        try:
                            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#PageLayout > div > div.x7x').get_attribute("outerHTML")                     
                        except:
                            pass

                        try: 
                            name = page_main.find_element(By.XPATH, '//*[@id="mstCity__xc_"]').text.strip()
                            if name == 'City':
                                customer_details_data.org_address = page_main.find_element(By.CSS_SELECTOR, '#mclInfo1 > tbody > tr > td:nth-child(2) > table > tbody').text.split('Mailing Address')[1].split('Country')[0].strip().rstrip('City')
                            else:
                                customer_details_data.org_address = page_main.find_element(By.CSS_SELECTOR, '#mclInfo1 > tbody > tr > td:nth-child(2) > table > tbody').text.split('Mailing Address')[1].split(name)[0].strip()
                        except Exception as e:
                            logging.info("Exception in org_address1: {}".format(type(e).__name__))
                            pass

                        try: 
                            org_city_details = page_main.find_element(By.XPATH, '//*[contains(text(),"City")]//following::td[2]').text
                            if org_city_details != '':
                                customer_details_data.org_city = org_city_details
                            else :
                                org_city_details = page_main.find_element(By.XPATH, '(//*[contains(text(),"City")])[2]//following::td[2]').text
                                customer_details_data.org_city = org_city_details
                        except Exception as e:
                            logging.info("Exception in org_city: {}".format(type(e).__name__))
                            pass

                        try: 
                            org_phone_details = page_main.find_element(By.XPATH, '//*[contains(text(),"Telephone Number")]//following::td[2]').text
                            if org_phone_details != '':
                                customer_details_data.org_phone = org_phone_details
                            else:
                                org_phone_details = page_main.find_element(By.CSS_SELECTOR, '#atCsrnAgencyContact > table.x1o > tbody > tr:nth-child(2) > td:nth-child(4)').text
                                customer_details_data.org_phone = org_phone_details
                        except Exception as e:
                            logging.info("Exception in org_phone1: {}".format(type(e).__name__))
                            pass

                        try: 
                            org_fax_details = page_main.find_element(By.XPATH, '//*[contains(text(),"Fax Number")]//following::td[2]').text
                            if org_fax_details != '':
                                customer_details_data.org_fax = org_fax_details
                            else:
                                org_fax_details = page_main.find_element(By.CSS_SELECTOR, '#atCsrnAgencyContact > table.x1o > tbody > tr:nth-child(2) > td:nth-child(5)').text
                                customer_details_data.org_fax = org_fax_details
                        except Exception as e:
                            logging.info("Exception in org_fax1: {}".format(type(e).__name__))
                            pass

                        try: 
                            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Website")]//following::td[2]').text
                        except Exception as e:
                            logging.info("Exception in org_website1: {}".format(type(e).__name__))
                            pass

                        try: 
                            org_email_details = page_main.find_element(By.XPATH, '//*[contains(text(),"Agency Email")]//following::td[2]').text
                            if org_email_details != '':
                                customer_details_data.org_email = org_email_details
                            else:
                                org_email_details = page_main.find_element(By.CSS_SELECTOR, '#atCsrnAgencyContact > table.x1o > tbody > tr:nth-child(2) > td:nth-child(6)').text
                                customer_details_data.org_email = org_email_details
                        except Exception as e:
                            logging.info("Exception in org_email1: {}".format(type(e).__name__))
                            pass

                        customer_close = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CloseBtn_uixr')))
                        page_main.execute_script("arguments[0].click();",customer_close)
                        time.sleep(5)
                        page_main.switch_to.window(page_main.window_handles[0])
                    except Exception as e:
                        logging.info("Exception in customer_click: {}".format(type(e).__name__))
                        pass
                 
                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            else:
                pass
            
    except:
        try:
            customer_details_data = customer_details()
            customer_details_data.org_language = 'EN'
            customer_details_data.org_parent_id = '7780104'
            customer_details_data.org_name = 'Asian Development Bank'

                # Onsite Field -Country of assignment
                # Onsite Comment -1.csv file is pulled name as "mfa_csrn_spn_countrycode.csv"	2."Hong Kong, China=CN" and "Regional=PH"       3.if country_name is not present then pass "PH".

            try:
                org_country = page_main.find_element(By.XPATH, '//*[contains(text(),"Country of assignment")]//following::td[2]').text
                customer_details_data.org_country =fn.procedure_mapping("assets/mfa_csrn_spn_countrycode.csv",org_country)
                if customer_details_data.org_country == None:
                    customer_details_data.org_country = 'PH'                
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass

            # Onsite Field -Contact Information >> Contact Person for Inquiries
            # Onsite Comment -None

            # Onsite Field -Contact Information >> Project Officer
            # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Person for Inquiries")]//following::td[2]').text
            except:
                try:
                    customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::td[5]').text
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Contact Information >> Email
            # Onsite Comment -None

            try:
                org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::a[2]').text
                customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
            except:
                try:
                    org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::a[1]').text
                    customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass
            
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    
    try:
        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Terms of Reference')))
        page_main.execute_script("arguments[0].click();",next_page)
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in click1: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#plMain > div').get_attribute("outerHTML")                     
    except:
        pass
# # Onsite Field -TOR Attachments
# # Onsite Comment -1.click on "Terms of Reference" tab in page_details to get attachments.

    try: 
        attach=page_main.find_element(By.XPATH, '//*[contains(text(),"TOR Attachments")]//following::td[2]')
        for single_record in attach.find_elements(By.CSS_SELECTOR, '#AttachmentTable_ATTACH_\/adb\/oracle\/apps\/xxcrs\/csrn\/webui\/CsrnProfilePG\.stlProfile\.TorAttachmentRN > table.x1o > tbody > tr')[1:]:
            attachments_data = attachments()

            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a.xh').text
            if '.pdf' in file_name:
                attachments_data.file_name = file_name.split('.')[0].strip()
            else:
                attachments_data.file_name = file_name
                
            external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > a').click()
            time.sleep(3)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        # Onsite Field -TOR Attachments >> Description
        # Onsite Comment -None

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
        pass
    
     # Onsite Field -Scope of Work
    # Onsite Comment -1.click on "Terms of Reference" tab in page_details to get notice_summary_english.
    
    # Onsite Field -Objective and Purpose of the Assignment
    # Onsite Comment -1.click on "Terms of Reference" tab in page_details to get notice_summary_english.
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Scope of Work")]//following::td[2]').text
        notice_data.notice_summary_english = notice_data.local_description
    except:
        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Objective and Purpose of the Assignment")]//following::td[2]').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Minimum Qualification Requirements
    # Onsite Comment -1.click on "Terms of Reference" tab in page_details to get attachments.

    try:
        notice_data.eligibility = page_main.find_element(By.XPATH, '//*[contains(text(),"Minimum Qualification Requirements")]//following::td[2]').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass

    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = 106
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass 
    
    try:
        next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.LINK_TEXT,'Cost Estimate')))
        page_main.execute_script("arguments[0].click();",next_page)
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in click2: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#plMain > div').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.LINK_TEXT,'Data Sheet')))
        page_main.execute_script("arguments[0].click();",next_page)
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in click3: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#plMain > div').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.LINK_TEXT,'Evaluation Criteria')))
        page_main.execute_script("arguments[0].click();",next_page)
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in click4: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#plMain > div').get_attribute("outerHTML")                     
    except:
        pass
    
    try: 
        attach=page_main.find_element(By.XPATH, '//*[contains(text(),"Narrative Evaluation Criteria")]//following::td[2]')
        for single_record in attach.find_elements(By.CSS_SELECTOR, '#AttachmentTable_ATTACH_\/adb\/oracle\/apps\/xxcrs\/csrn\/webui\/CsrnProfilePG\.stlProfile\.attachmentBeanNarrative > table.x1o > tbody > tr')[1:]:
            attachments_data = attachments()
        # Onsite Field -TOR Attachments >> Title
        # Onsite Comment -1.take in text format.

            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a.xh').text
            if '.pdf' in file_name:
                attachments_data.file_name = file_name.split('.')[0].strip()
            else:
                attachments_data.file_name = file_name
                
            external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > a').click()
            time.sleep(3)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        # Onsite Field -TOR Attachments >> Description
        # Onsite Comment -None

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
        pass
    
    try:
        next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.LINK_TEXT,'Attachments')))
        page_main.execute_script("arguments[0].click();",next_page)
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in click5: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#plMain > div').get_attribute("outerHTML")                     
    except:
        pass
    
    try: 
        attach1=page_main.find_element(By.XPATH, '//*[contains(text(),"RFP Attachments")]//following::td[2]')
        for page_no in range(1,4):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#AttachmentTable_ATTACH_\/adb\/oracle\/apps\/xxcrs\/csrn\/webui\/CsrnProfilePG\.stlProfile\.attachmentBeanRfp > table.x1o > tbody > tr:nth-child(2)'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#AttachmentTable_ATTACH_\/adb\/oracle\/apps\/xxcrs\/csrn\/webui\/CsrnProfilePG\.stlProfile\.attachmentBeanRfp > table.x1o > tbody > tr')))
            length = len(rows)
            for data in range(1,length):
                single_record = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#AttachmentTable_ATTACH_\/adb\/oracle\/apps\/xxcrs\/csrn\/webui\/CsrnProfilePG\.stlProfile\.attachmentBeanRfp > table.x1o > tbody > tr')))[data]

        # Onsite Field -TOR Attachments >> Title
        # Onsite Comment -1.take in text format.
                file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a.xh').get_attribute("outerHTML")
                if 'onclick' in file_name:
                    attachments_data = attachments()
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a.xh').text.split('.')[0].strip()
                    
                    external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > a').click()
                    time.sleep(3)
                    file_dwn = Doc_Download.file_download()
                    attachments_data.external_url = str(file_dwn[0])
                    
                    try:
                        attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass
                # Onsite Field -TOR Attachments >> Description
                # Onsite Comment -None

                    try:
                        attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    except Exception as e:
                        logging.info("Exception in file_description: {}".format(type(e).__name__))
                        pass
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
                else:
                    attachments_data = attachments()
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a.xh').text
                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > a').get_attribute("href")
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," table:nth-child(3) > tbody > tr > td > table > tbody > tr > td:nth-child(2) > table > tbody > tr > td:nth-child(7) > a")))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page attachments")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#AttachmentTable_ATTACH_\/adb\/oracle\/apps\/xxcrs\/csrn\/webui\/CsrnProfilePG\.stlProfile\.attachmentBeanRfp > table.x1o > tbody > tr:nth-child(2)'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page attachments")
                break
    except Exception as e:
        logging.info("Exception in attachments3: {}".format(type(e).__name__)) 
        pass
    
    try: 
        attach2=page_main.find_element(By.XPATH, '//*[contains(text(),"Proposal Attachments")]//following::td[2]')
        for single_record in attach2.find_elements(By.CSS_SELECTOR, '#AttachmentTable_ATTACH_\/adb\/oracle\/apps\/xxcrs\/csrn\/webui\/CsrnProfilePG\.stlProfile\.attachmentBeanProposal > table.x1o > tbody > tr')[1:]:
            
        # Onsite Field -TOR Attachments >> Title
        # Onsite Comment -1.take in text format.
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a.xh').get_attribute("outerHTML")
            if 'onclick' in file_name:
                attachments_data = attachments()
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a.xh').text.split('.')[0].strip()

                external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > a').click()
                time.sleep(3)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])

                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass
            # Onsite Field -TOR Attachments >> Description
            # Onsite Comment -None

                try:
                    attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                except Exception as e:
                    logging.info("Exception in file_description: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments4: {}".format(type(e).__name__)) 
        pass
    
    try:
        back = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#bBack_uixr')))
        page_main.execute_script("arguments[0].click();",back)
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in back: {}".format(type(e).__name__)) 
        
    WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#atResults > table.x1o > tbody > tr:nth-child(4)')))
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))  
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details 
page_main.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://selfservice.adb.org/OA_HTML/OA.jsp?OAFunc=XXCRS_CSRN_HOME_PAGE"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#atResults > table.x1o > tbody > tr:nth-child(4)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#atResults > table.x1o > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#atResults > table.x1o > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,"Next 25")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#atResults > table.x1o > tbody > tr:nth-child(4)'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
