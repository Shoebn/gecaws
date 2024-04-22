from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_merx_ca"
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
SCRIPT_NAME = "ca_merx_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# to explore CA details - 1) click on URL : "https://www.merx.com/public/solicitations/awarded?keywords=&solSearchStatus=awardedSolicitationsTab"

#                         2)  go to "Status" Drop down ,and select 2 options for contract_award --      
#                                                                                               i) Bid Results     (ref url : "https://www.merx.com/public/solicitations/bid-results?keywords=&solSearchStatus=bidResultsSolicitationsTab")
#                                                                                               ii) award solicitation (ref url : "https://www.merx.com/public/solicitations/awarded?keywords=&solSearchStatus=awardedSolicitationsTab")


#                         3) click on "Relevancy" select  "publication Date (Newest first)" option 
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ca_merx_ca'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CAD'
    
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -take notice_type 7 for "Bid Results" and "Awarded Solicitations" ( status > Bid Results ) and (status > Awarded Solicitations )
    notice_data.notice_type = 7
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.rowTitle').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, '#solicitationList-resultList > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -None
    # Onsite Comment -inspect url for detail page , detail_page of "Bid Results" = "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0"  ,   detail_page of "Awarded Solicitations" = "https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        page_details.find_element(By.CSS_SELECTOR,'#cookieBannerAcceptBtn').click()
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div:nth-child(1) > h3.content-block-title')))
    except:
        pass
    
    # Onsite Field -None
    # Onsite Comment -for the "Awarded Solicitation" take notice_text from "Award" tab (selector : #awardAbstractTab > a) ... for the "bid results" take notice_text from "Bid Results" tab (selector : #bidResultAbstractTab > a), url ref : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0" , "https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#innerTabContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        page_details.find_element(By.XPATH,'//*[@id="descriptionTextReadMore"]').click()
        time.sleep(5)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'content-block-sub-title mets-field-label')))
    except:
        pass
    
    # Onsite Field -Solicitation Number
    # Onsite Field -Project Number
    # Onsite Comment -for detail page: click on (selector : "tr> td > a"), split the "Solicitation Number" from the "Notice" tab
    # Onsite Field -None
    # Onsite Comment -format 3 ,if notice_no is not available in "Reference Number"  field then pass notice_no from notice_url
    # Onsite Field -Reference Number
    # Onsite Comment -format 3
    
    # Onsite Field -Published Bid Results
    # Onsite Comment -for the "bid results" take publish_date from "Published Bid Results" field, ref url : "https://www.merx.com/public/solicitations/bid-results?keywords=&solSearchStatus=bidResultsSolicitationsTab&sortBy=publicationDate&sortDirection=DESC&pageNumberSelect=1"
    
    try:  
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Publication")]//following::p[1]').text
        publish_date = re.findall('\d{4}/\d+/\d+ \d+:\d+:\d+ [apAP][mM]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y/%m/%d %H:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S %p')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference Number")]//following::p[1]').text
    except:
        try:
            notice_no = notice_data.notice_url
            notice_data.notice_no = re.findall('\d+',notice_no)[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass  
                
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::div[1]").text.strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::table[1]").text.strip()
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
     
    # Onsite Field -Notice Type
    # Onsite Comment -Replace following keywords with given respective keywords ('services = service' , 'goods = supply' , 'Goods & Services   = service') ,       split the data from detail_page, ref_url ="https://www.merx.com/public/supplier/award-without-solicitation/42838139361/abstract"

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice Type")]//following::p[1]').text
        if "Goods & Services" in notice_contract_type or "Services" in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif "Goods" in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_type_actual = notice_data.notice_contract_type
    except:
        pass

    # Onsite Field -Reference Number
    # Onsite Comment -for detail page: (selector : "tr> td > a") , split the "Reference_number" from the "Notice" tab,             ref url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0" , "https://www.merx.com/arcavialivingltd/solicitations/Long-Term-Care-Construction-160-Beds-Orillia/0000252660?origin=0"

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Number")]//following::p[1]').text
    except:
        try:
            notice_data.related_tender_id = page_details.find_element(By.XPATH, ' //*[contains(text(),"Project Number")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Source ID
    # Onsite Comment -for detail page: click on (selector : "tr> td > a"), split the "-Source ID " from the "Notice" tab

    try:
        notice_data.additional_source_id = page_details.find_element(By.CSS_SELECTOR, '#innerTabContent').text.split("Source ID")[1].split("Agreement Type")[0].split("Details")[0].split("Associated Components")[0].strip()
    except Exception as e:
        logging.info("Exception in additional_source_id: {}".format(type(e).__name__))
        pass

    
    notice_data.class_at_source = "CPV"
    
    # Onsite Field -UNSPSC Categories
    # Onsite Comment -for detail page: click on (selector : "tr> td > a"), split the category from "Categories" tab (selector : #categoriesAbstractTab > a)
    # Onsite Field -Details >> Category
    # Onsite Comment -format 3 , take the following data from "Category	" field

    
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Issuing Organization
        # Onsite Comment -in detail_page , split the data from "Notice" tab, ref url : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0"  , "https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"
        
        # Onsite Field -None
#         # Onsite Comment -for award_solicitation take org_name from tender_html_page

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Issuing Organization")]//following::p[1]').text
        except:
            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.buyer-name').text
            except:
                customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer Information')]//following::td[2]").text
    
        customer_details_data.org_country = 'CA'
        # Onsite Field -Location
        # Onsite Comment -split only city For ex. "Canada, Manitoba, Winnipeg", here split only  "Manitoba" and "Winnipeg" , url ref: "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  ,  "https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"
        
        # Onsite Field -City         :
#         # Onsite Comment -split the data between "City" and "Province" field ,   ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

        try:
            customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, '#innerTabContent').text.split("Location")[1].split("Dates")[0].split("Delivery Point")[0].split("Job ")[0].split("Job Location")[0].split("Purchase Type")[0].strip()
        except:
            try:
                customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, "#Table3 > tbody").text.split("City")[1].split("State / Province")[0].strip()
            except:
                try:
                    customer_details_data.org_city = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer Information')]//following::td[2]").text.split("City         :")[1].split("Province     :")[0].strip()
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass
        
        customer_details_data.org_language = 'EN'

        # Onsite Field -Contact Information
        # Onsite Comment -split the data from "Notice" tab , ref url : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0","https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"
        
        # Onsite Field -Contact Information
#         # Onsite Comment - 

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[1]').text
        except:
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[1]').text
            except:
                try:
                    customer_details_data.contact_person  = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer Information')]//following::td[2]").text.split("Telephone    : ")[1].split("E-mail       :")[0].strip()
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass
            
        # Onsite Field -Contact Information
        # Onsite Comment -split the data from detail_page
        
        # Onsite Field -Telephone
        # Onsite Comment -split the data between "Telephone  " and "E-mail"  ,      ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

        try:
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[2]').text
            customer_details_data.org_phone = re.findall('\d{3}-\d{3}-\d{4}',org_phone)[0]
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[3]').text
                customer_details_data.org_phone = re.findall('\d{3}-\d{3}-\d{4}',org_phone)[0]
            except:
                try:
                    customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, "#Table3 > tbody").text.split("Phone")[1].split("Fax")[0].strip()
                except:
                    try:
                        org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer Information')]//following::td[2]").text.split("Telephone    : ")[1].split("E-mail       :")[0].strip()
                        customer_details_data.org_phone = re.findall('\d{3}-\d{3}-\d{4}',org_phone)[0]
                    except Exception as e:
                        logging.info("Exception in org_email: {}".format(type(e).__name__))
                        pass
        
        # Onsite Field -Contact Information
        # Onsite Comment -split the data from detail_page
        
        # Onsite Field -E-mail       :
          # Onsite Comment -split the data after "E-mail"

        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[3]').text
            customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
        except:
            try:
                org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[2]').text
                customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
            except:
                try:
                    customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, "#Table3 > tbody").text.split("Email")[1].split("Website URL")[0].strip()
                except:
                    try:
                        org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer Information')]//following::td[2]").text.split("E-mail       :")[1].strip()
                        customer_details_data.org_email = re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
                    except Exception as e:
                        logging.info("Exception in org_email: {}".format(type(e).__name__))
                        pass
                
                
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer Information')]//following::td[2]").text.split("Address: ")[1].split("City")[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
                # Onsite Field -Province     :
        # Onsite Comment -split the data between "Province" and "Postal Code" field

        try:
            customer_details_data.org_state = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer Information')]//following::td[2]").text.split("Province     :")[1].split("Postal Code  :")[0].strip()
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Postal Code  :
        # Onsite Comment -split the data between "Postal Code  :" and "Telephone" field, ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer Information')]//following::td[2]").text.split("Postal Code  :")[1].split("Telephone    :")[0].strip()
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        category_url = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#categoriesAbstractTab > a")))
        page_details.execute_script("arguments[0].click();",category_url)
        time.sleep(10)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#selectedHeaderTitleMERX')))
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#innerTabContent').get_attribute("outerHTML")                     
    except:
        pass


    try:
        cpv_at_source = ''
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"UNSPSC Catego")]//following::tr/td[1]'):
            category = single_record.text
            notice_data.category = re.findall('\d{8}',category)[0]
            cpv_codes_list = fn.CPV_mapping("assets/ca_merx_ca_unspsc_category.csv",notice_data.category)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpv_code1 = each_cpv
                cpv_code = re.findall('\d{8}',cpv_code1)[0]                
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
                cpv_at_source += cpv_code
                cpv_at_source += ','
            notice_data.cpv_at_source = cpv_at_source.rstrip(',') 
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    
    if url == urls[0]:
        try:
            bid_results = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#bidResultAbstractTab > a")))
            page_details.execute_script("arguments[0].click();",bid_results)
            time.sleep(10)
        except:
            pass
        
        try:
            WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.fieldset.content-block > h3')))
        except:
            pass
        
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#innerTabContent').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Amount")]//following::span[1]').text
            grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
            notice_data.grossbudgetlc = float(grossbudgetlc.replace('.','').replace(',','').strip())
            notice_data.est_amount = notice_data.grossbudgetlc
        except:
            try:
                grossbudgetlc = page_details.find_element(By.XPATH, "//*[contains(text(),'Amount')]//following::td[1]").text
                grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
                notice_data.grossbudgetlc = float(grossbudgetlc.replace('.','').replace(',','').strip())
                notice_data.est_amount = notice_data.grossbudgetlc
            except Exception as e:
                logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
                pass


    # # Onsite Field -None
    # # Onsite Comment -for the "bid results" take lot_details from "Bid Results" tab (selector : #bidResultAbstractTab > a)... for the "Awarded Solicitation" take lot_details from "Award" tab (selector : #awardAbstractTab > a) ...

        try:       
            lot_number=1
            for single_record in page_details.find_elements(By.XPATH, '/html/body/main/div[1]/div[2]/div[3]/div[2]/div[3]/table/tbody/tr[1]/td/div[2]/div/table/tbody/tr[1]/td/div[2]/div/table/tbody/tr')[:-1]:
                lot = single_record.text
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number

            # Onsite Field -Items
            # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"


                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td.bidItemRow > span').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        

            # Onsite Field -"Price / Each" , "Price / Meter"
            # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

                try:
                    lot_grossbudget_lc = lot.split("Price / Metric Ton/Tonne")[1].split("Quantity")[0]
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace('.','').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

            # Onsite Field -UOM
            # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.XPATH, '//*[contains(text(),"UOM")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Qty
            # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

                try:
                    lot_quantity = lot.split("Qty")[1].split("Quote Type")[0]
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_contract_type_actual = notice_data.notice_contract_type
                except:
                    pass
                
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
    
# # Onsite Field -Bid Results Document
# # Onsite Comment -for the "bid results" take attachments from "Bid Results" tab (selector : #bidResultAbstractTab > a)...  ref url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

        try:              
            attachments_data = attachments()
            # Onsite Field -File
            # Onsite Comment -for the "bid results" take attachments from "Bid Results" tab (selector : #bidResultAbstractTab > a)...  ref url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#tblBidResultDocument > tbody > tr > td:nth-child(1) a').text.split(".")[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            # Onsite Field -File
            # Onsite Comment -split only file_name for ex. "Results - NLESD-23-204.pdf" ,heresplit only ---"Results - NLESD-23-204",        ref url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

            attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#tblBidResultDocument > tbody > tr > td:nth-child(1) a').text.split(".")[0].strip()

            # Onsite Field -Size
            # Onsite Comment -ref_url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, '#tblBidResultDocument > tbody > tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            # Onsite Field -File
            # Onsite Comment -split the data from "Bid Results" tab (selector: "#bidResultAbstractTab > a")   ref_url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#tblBidResultDocument > tbody > tr > td:nth-child(1) a').get_attribute('href')


            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    
    elif url == urls[1]:
        
        try:
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english = notice_data.notice_title 
            
            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_contract_type_actual = notice_data.notice_contract_type
            except:
                pass

            award_details_data = award_details()

            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Supplier Awarded")]//following::p').text

            award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::p[1]').text

            # Onsite Field -Total Cost
            # Onsite Comment -
            grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded Value")]//following::span[1]').text
            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
            award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace('.','').replace(',','').strip())


            # Onsite Field -Award Date
            # Onsite Comment -

            award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Award Date")]//following::p[1]').text
            award_date = re.findall('\d{4}/\d+/\d+',award_date)[0]
            award_details_data.award_date  = datetime.strptime(award_date,'%Y/%m/%d').strftime('%Y/%m/%d')

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except:
            pass
        
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#   reference_url  of format 2 : "https://www.merx.com/public/supplier/award-without-solicitation/42851773141/abstract"

#    to view  above format  go to "Status" Drop down , and select "award solicitation" --   
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#     # Onsite Field -None
#     # Onsite Comment -for the "bid results" take lot_details from "Bid Results" tab (selector : #bidResultAbstractTab > a)... for the "Awarded Solicitation" take lot_details from "Award" tab (selector : #awardAbstractTab > a) ...

        try:     
            award_result = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#awardAbstractTab > a")))
            page_details.execute_script("arguments[0].click();",award_result)
            time.sleep(10)
            
            try:
                WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div:nth-child(2) > h1')))
            except:
                pass
            
            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#innerTabContent').get_attribute("outerHTML")                     
            except:
                pass
            
            lot_details_data = lot_details()
            lot_details_data.lot_number=1

            # Onsite Field -Items
            # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english = notice_data.notice_title 
            

            try:
                contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Dates")]//following::p[1]').text.split("-")[0]
                contract_start_date = re.findall('\d{4}/\d+/\d+',contract_start_date)[0]
                lot_details_data.contract_start_date  = datetime.strptime(contract_start_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass


            # Onsite Field -Notice Type
            # Onsite Comment -Replace following keywords with given respective keywords ('services = service' , 'goods = supply' , 'Goods & Services   = service') ,       split the data from detail_page, ref_url ="https://www.merx.com/public/supplier/award-without-solicitation/42838139361/abstract"

            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_contract_type_actual = notice_data.notice_contract_type
            except:
                pass


            # Onsite Field -Contract Dates
            # Onsite Comment -split only end_date, for ex: "2023/03/31 - 2025/03/30" , here split only "2025/03/30" (i.e = right side date )     

            try:
                contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Dates")]//following::p[1]').text.split("-")[1]
                contract_end_date = re.findall('\d{4}/\d+/\d+',contract_end_date)[0]
                lot_details_data.contract_end_date  = datetime.strptime(contract_end_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass

            # Onsite Field -None
            # Onsite Comment 
            # div.fieldset.awardeeItem.content-block

            for single_record in page_details.find_elements(By.XPATH, '//*[@class="content-block bidResultItems"]/div'):
                lot1 = single_record.text
                award_details_data = award_details()

                    # Onsite Field -"Supplier Awarded"
                    # Onsite Comment -for the "Awarded Solicitation" bidder name is avaible in "Award" ...

                award_details_data.bidder_name = lot1.split("Supplier Awarded")[1].split("Address")[0].strip()


                    # Onsite Field -Address
                    # Onsite Comment -

                award_details_data.address =  lot1.split("Address")[1].split("Awarded Value")[0].strip()
#                         # Onsite Field -Total Cost
#                         # Onsite Comment -
                grossawardvaluelc = lot1.split("Awarded Value")[1].split("Award Date")[0].strip()
                grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace('.','').replace(',','').strip())

#                         # Onsite Field -Award Date
#                         # Onsite Comment -

                award_date = lot1.split("Award Date")[1].split("Contract Dates")[0].split("DESCRIPTION")[0].strip()
                award_date = re.findall('\d{4}/\d+/\d+',award_date)[0]
                award_details_data.award_date  = datetime.strptime(award_date,'%Y/%m/%d').strftime('%Y/%m/%d')

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            try:
                lot_details_data = lot_details()
                lot_details_data.lot_number = 1
                lot_details_data.lot_title = notice_data.local_title
                notice_data.is_lot_default = True
                lot_details_data.lot_title_english = notice_data.notice_title 
                
                try:
                    contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Dates")]//following::p[1]').text.split("-")[0]
                    contract_start_date = re.findall('\d{4}/\d+/\d+',contract_start_date)[0]
                    lot_details_data.contract_start_date  = datetime.strptime(contract_start_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass
                
                try:
                    contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Dates")]//following::p[1]').text.split("-")[1]
                    contract_end_date = re.findall('\d{4}/\d+/\d+',contract_end_date)[0]
                    lot_details_data.contract_end_date  = datetime.strptime(contract_end_date,'%Y/%m/%d').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_contract_type_actual = notice_data.notice_contract_type
                except:
                    pass

                award_details_data = award_details()

                award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'fieldset:nth-child(20)').text.split("Supplier Information")[1].split(".")[0].strip()

                award_details_data.address = page_details.find_element(By.CSS_SELECTOR, 'fieldset:nth-child(20)').text.split("Supplier Information")[1].strip()

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
            except:
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.merx.com/public/solicitations/bid-results?keywords=&solSearchStatus=bidResultsSolicitationsTab" , "https://www.merx.com/public/solicitations/awarded?keywords=&solSearchStatus=awardedSolicitationsTab"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            page_main.find_element(By.CSS_SELECTOR,'#cookieBannerAcceptBtn').click()
            time.sleep(5)
        except:
            pass
        try:
            click1 = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#fs_3 > div.fs-widget')))
            page_main.execute_script("arguments[0].click();",click1)
            time.sleep(3)
        except:
            pass
        
        try:
            click2 = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="fs_3"]/div[2]/div/div[7]')))
            page_main.execute_script("arguments[0].click();",click2)
            time.sleep(3)
        except:
            pass

        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#g_6 > label')))
        except:
            pass

        try:
            for page_no in range(1,5):#5
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="solicitationsList"]/tbody/tr/td'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="solicitationsList"]/tbody/tr/td')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="solicitationsList"]/tbody/tr/td')))[records]
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," a > span:nth-child(1)")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="solicitationsList"]/tbody/tr/td'),page_check))
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
