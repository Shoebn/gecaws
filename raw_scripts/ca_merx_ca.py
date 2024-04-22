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
import functions as fn
from functions import ET
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
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'ca_merx_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'CAD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -take notice_type 7 for "Bid Results" and "Awarded Solicitations" ( status > Bid Results ) and (status > Awarded Solicitations )
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.rowTitle').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Published Bid Results
    # Onsite Comment -for the "bid results" take publish_date from "Published Bid Results" field, ref url : "https://www.merx.com/public/solicitations/bid-results?keywords=&solSearchStatus=bidResultsSolicitationsTab&sortBy=publicationDate&sortDirection=DESC&pageNumberSelect=1"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span.bidResultsPublicationDate").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    


      # Onsite Field -Published
    # Onsite Comment -for the "Awarded Solicitation" take publish_date from "Published" field, ref url : "https://www.merx.com/public/solicitations/awarded?keywords=&solSearchStatus=awardedSolicitationsTab&sortBy=publicationDate&sortDirection=DESC&pageNumberSelect=1"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span.publicationDate").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, '#solicitationList-resultList > h1').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Solicitation Number
    # Onsite Comment -for detail page: click on (selector : "tr> td > a"), split the "Solicitation Number" from the "Notice" tab

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Number")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project Number
    # Onsite Comment -some notices has contains the diffrent field name for notice_no such as "project_number" , ref_url : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/Mowing-Red-River-Floodway-and-Provincial-Waterways-Vicinity-of-Winnipeg-MB/0000255532?origin=0"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Project Number")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::p').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -excluding the "Local_title /  Local_description "all fields should be in English,      split the data from detail_page

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::p').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    # Onsite Field -Notice Type
    # Onsite Comment -Replace following keywords with given respective keywords ('services = service' , 'goods = supply' , 'Goods & Services   = service') ,       split the data from detail_page, ref_url ="https://www.merx.com/public/supplier/award-without-solicitation/42838139361/abstract"

    try:
        notice_data.notice_contract_type = single_record.find_element(By.XPATH, '//*[contains(text(),"Notice Type")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass


    
    # Onsite Field -Reference Number
    # Onsite Comment -for detail page: (selector : "tr> td > a") , split the "Reference_number" from the "Notice" tab,             ref url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0" , "https://www.merx.com/arcavialivingltd/solicitations/Long-Term-Care-Construction-160-Beds-Orillia/0000252660?origin=0"

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference Number")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Source ID
    # Onsite Comment -for detail page: click on (selector : "tr> td > a"), split the "-Source ID " from the "Notice" tab

    try:
        notice_data.additional_source_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Source ID")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in additional_source_id: {}".format(type(e).__name__))
        pass


        # Onsite Field -Bid Amount
    # Onsite Comment -for the "bid results" take grossbudgetlc from "Bid Results" tab (selector : #bidResultAbstractTab > a)... for the "Awarded Solicitation" take grossbudgetlc from "Bid Results" tab (selector : #bidResultAbstractTab > a) ref url : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0" , "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

    try:
        notice_data.grossbudgetlc = single_record.find_element(By.XPATH, '//*[contains(text(),"Bid Amount")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bid Amount
    # Onsite Comment -for the "bid results" take est_amount from "Bid Results" tab (selector : #bidResultAbstractTab > a)... for the "Awarded Solicitation" take est_amount from "Bid Results" tab (selector : #bidResultAbstractTab > a) ref url : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0" , "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

    try:
        notice_data.est_amount = single_record.find_element(By.XPATH, '//*[contains(text(),"Bid Amount")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
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
    
    # Onsite Field -None
    # Onsite Comment -for the "Awarded Solicitation" take notice_text from "Award" tab (selector : #awardAbstractTab > a) ... for the "bid results" take notice_text from "Bid Results" tab (selector : #bidResultAbstractTab > a), url ref : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0" , "https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#innerTabContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = '"CPV"'
    
    # Onsite Field -UNSPSC Categories
    # Onsite Comment -for detail page: click on (selector : "tr> td > a"), split the category from "Categories" tab (selector : #categoriesAbstractTab > a)

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC Catego")]//following::tr/td[2]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass    
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#innerTabContent > form'):
            customer_details_data = customer_details()
        # Onsite Field -Issuing Organization
        # Onsite Comment -in detail_page , split the data from "Notice" tab, ref url : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0"  , "https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"

            try:
                customer_details_data.org_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Issuing Organization")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'CA'
        # Onsite Field -Location
        # Onsite Comment -split only city For ex. "Canada, Manitoba, Winnipeg", here split only  "Manitoba" and "Winnipeg" , url ref: "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  ,  "https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"

            try:
                customer_details_data.org_city = single_record.find_element(By.XPATH, '//*[contains(text(),"Details")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_language = 'EN'

        # Onsite Field -Contact Information
        # Onsite Comment -split the data from "Notice" tab , ref url : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0","https://www.merx.com/universityofcalgary/solicitations/Turnkey-Ultrasound-Based-Neuromodulation/0000250384?origin=0"

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Information
        # Onsite Comment -split the data from detail_page

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Information
        # Onsite Comment -split the data from detail_page

            try:
                customer_details_data.org_email = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[3]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    # Onsite Field -None
    # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#selectedCategoryContainerUNSPSC'):
            cpvs_data = cpvs()

            
        # Onsite Field -UNSPSC Categories / UNSPSC Category
        # Onsite Comment -for detail page: click on (selector : "tr> td > a"), split the cpvs from "Categories" tab (selector : #categoriesAbstractTab > a)

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC Catego")]//following::tr/td[1]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    

    
# Onsite Field -None
# Onsite Comment -for the "bid results" take lot_details from "Bid Results" tab (selector : #bidResultAbstractTab > a)... for the "Awarded Solicitation" take lot_details from "Award" tab (selector : #awardAbstractTab > a) ...

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#innerTabContent'):
            lot_details_data = lot_details()
        # Onsite Field -Items
        # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'td.bidItemRow > span').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Items
        # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'td.bidItemRow > span').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -"Price / Each" , "Price / Meter"
        # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

            try:
                lot_details_data.lot_grossbudget_lc = single_record.find_element(By.XPATH, '//*[contains(text(),"Price")]//following::span[1]').text
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
                lot_details_data.lot_quantity = single_record.find_element(By.XPATH, '//*[contains(text(),"Qty")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

        # Onsite Field -Contract Dates
        # Onsite Comment -split only start_date, for ex: "2023/03/31 - 2025/03/30" , here split only "2023/03/31" (i.e = left side date )     for the "Awarded Solicitation" take "contract_start_date" and "contract_end_date" from "Award" tab,  ref url : "https://www.merx.com/public/supplier/award-without-solicitation/42834057708/abstract" , "https://www.merx.com/universityofcalgary/solicitations/Thrombin-Generation-Analyzer-with-Consumables/0000252653?origin=0"

            try:
                lot_details_data.contract_start_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Contract Dates")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass

        
        # Onsite Field -Notice Type
        # Onsite Comment -Replace following keywords with given respective keywords ('services = service' , 'goods = supply' , 'Goods & Services   = service') ,       split the data from detail_page, ref_url ="https://www.merx.com/public/supplier/award-without-solicitation/42838139361/abstract"

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice Type")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
            
        
        # Onsite Field -Contract Dates
        # Onsite Comment -split only end_date, for ex: "2023/03/31 - 2025/03/30" , here split only "2025/03/30" (i.e = right side date )     for the "Awarded Solicitation" take "contract_start_date" and "contract_end_date" from "Award" tab,  ref url : "https://www.merx.com/public/supplier/award-without-solicitation/42834057708/abstract" , "https://www.merx.com/universityofcalgary/solicitations/Thrombin-Generation-Analyzer-with-Consumables/0000252653?origin=0"

            try:
                lot_details_data.contract_end_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Contract Dates")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass


            

    
        # Onsite Field -Award Date
        # Onsite Comment -take award_date from "Award" tab (selector : #awardAbstractTab > a)... , url ref : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0" , "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Maintenance-Services-Contract-HVAC-EMCS-Systems-Multiple-Locations/0000256080?origin=0"

            try:
                lot_details_data.lot_award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Award Date")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -None
        # Onsite Comment -for the "bid results" take award_details from "Bid Results" tab (selector : #bidResultAbstractTab > a)... for the "Awarded Solicitation" take award_details from "Award" tab (selector : #awardAbstractTab > a) ref url : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0" , "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#innerTabContent'):
                    award_details_data = award_details()
		
                    # Onsite Field -"Supplier Awarded"
                    # Onsite Comment -for the "bid results" "Award" tab is not available so take "N/A" in "Bidder Name" Field... for the "Awarded Solicitation" bidder name is avaible in "Award" tab...

                    award_details_data.bidder_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Supplier Awarded")]//following::p').text
			
                    # Onsite Field -Total Cost
                    # Onsite Comment -for the "bid results" take grossawardvaluelc from "Bid Results" tab (selector : #bidResultAbstractTab > a)... , url ref : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-STAND-ALONE-WATER-PRESSURE-TRANSDUCER-WATER-LEVELS-PROBES/0000253481?origin=0"

                    award_details_data.grossawardvaluelc = single_record.find_element(By.XPATH, '//*[contains(text(),"Total Cost")]//following::span[1]').text
			
                    # Onsite Field -Awarded Value
                    # Onsite Comment -for the "Awarded Solicitations" take grossawardvaluelc from "Award" tab (selector : #awardAbstractTab > a)... , url ref : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"   ........ you can also use "//*[contains(text(),"Awarded Value")]//following::p" selector for grossawardvaluelc

                    award_details_data.grossawardvaluelc = single_record.find_element(By.XPATH, '//*[contains(text(),"Awarded Value")]//following::span').text
			
                    # Onsite Field -Address
                    # Onsite Comment -for the "Awarded Solicitations" take address from "Award" tab (selector : #awardAbstractTab > a)... , url ref : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

                    award_details_data.address = single_record.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::p').text
			
                    # Onsite Field -Award Date
                    # Onsite Comment -for the "Awarded Solicitations" take award_date from "Award" tab (selector : #awardAbstractTab > a)... , url ref : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

                    award_details_data.award_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Award Date")]//following::p').text

                    # Onsite Field -Duration
                    # Onsite Comment -for the "Awarded Solicitation" take contract_duration from "Award" field , split the data between "Duration" and "Contact Information" field, ref url : "https://www.merx.com/public/supplier/award-without-solicitation/42834057708/abstract"

                    award_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duration")]//following::div[1]').text
			
			
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
    

    
# Onsite Field -Bid Results Document
# Onsite Comment -for the "bid results" take attachments from "Bid Results" tab (selector : #bidResultAbstractTab > a)...  ref url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#innerTabContent > div.fieldset'):
            attachments_data = attachments()
        # Onsite Field -File
        # Onsite Comment -for the "bid results" take attachments from "Bid Results" tab (selector : #bidResultAbstractTab > a)...  ref url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

            try:
                attachments_data.file_type = single_record.find_element(By.XPATH, '//*[contains(text(),"File")]//following::span').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File
        # Onsite Comment -split only file_name for ex. "Results - NLESD-23-204.pdf" ,heresplit only ---"Results - NLESD-23-204",        ref url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

            try:
                attachments_data.file_name = single_record.find_element(By.XPATH, '//*[contains(text(),"File")]//following::a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Size
        # Onsite Comment -ref_url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

            try:
                attachments_data.file_size = single_record.find_element(By.XPATH, '//*[contains(text(),"Size")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File
        # Onsite Comment -split the data from "Bid Results" tab (selector: "#bidResultAbstractTab > a")   ref_url : "https://www.merx.com/govnl/newfoundlandlabradorenglishschooldistrict/solicitations/Asphalt-Repairs-Various-St-John-s-Metro-Area-Schools/0000253271?origin=0"

            attachments_data.external_url = single_record.find_element(By.XPATH, '//*[contains(text(),"File")]//following::a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass






# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#   reference_url  of format 2 : "https://www.merx.com/public/supplier/award-without-solicitation/42851773141/abstract"

#    to view  above format  go to "Status" Drop down , and select "award solicitation" --   
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# Onsite Field -Notice Type
# Onsite Comment -Replace following keywords with given respective keywords ('services = service' , 'goods = supply' , 'Goods & Services   = service') ,       split the data from detail_page, ref_url ="https://www.merx.com/public/supplier/award-without-solicitation/42838139361/abstract"

    try:
        notice_data.notice_contract_type = single_record.find_element(By.XPATH, '//*[contains(text(),"Notice Type")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass


# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#innerTabContent > form'):
            customer_details_data = customer_details()

        # Onsite Field -None
        # Onsite Comment -for award_solicitation take org_name from tender_html_page

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.buyer-name').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass


            customer_details_data.org_language = 'EN'

            customer_details_data.org_country = 'CA'

        # Onsite Field -Contact Information
        # Onsite Comment - 
            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass


        # Onsite Field -Contact Information
        # Onsite Comment -split the data from detail_page

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[3]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contact Information
        # Onsite Comment -split the data from detail_page

            try:
                customer_details_data.org_email = single_record.find_element(By.XPATH, '//*[contains(text(),"Contact Information")]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass  


                customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
         
    




    # Onsite Field -None
    # Onsite Comment -for the "bid results" take lot_details from "Bid Results" tab (selector : #bidResultAbstractTab > a)... for the "Awarded Solicitation" take lot_details from "Award" tab (selector : #awardAbstractTab > a) ...

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#innerTabContent'):
            lot_details_data = lot_details()

        # Onsite Field -Items
        # Onsite Comment -reference url for  "Bid Results" tab (selector : #bidResultAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/SUPPLY-AND-DELIVERY-OF-CORRUGATED-STEEL-CULVERTS/0000253012?origin=0"  reference url for  "Award" tab (selector : #awardAbstractTab > a) : "https://www.merx.com/mbgov/manitobainfrastructure/solicitations/THE-SUPPLY-AND-DELIVERY-OF-SDI-12-RAIN-GAUGE-WITH-200-CM2-COLLECTION-AREA/0000252141?origin=0"

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.rowTitle').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass


        
        # Onsite Field -Contract Dates
        # Onsite Comment -split only start_date, for ex: "2023/03/31 - 2025/03/30" , here split only "2023/03/31" (i.e = left side date )  
            try:
                lot_details_data.contract_start_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Contract Dates")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass

        
        # Onsite Field -Notice Type
        # Onsite Comment -Replace following keywords with given respective keywords ('services = service' , 'goods = supply' , 'Goods & Services   = service') ,       split the data from detail_page, ref_url ="https://www.merx.com/public/supplier/award-without-solicitation/42838139361/abstract"

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice Type")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
            
        
        # Onsite Field -Contract Dates
        # Onsite Comment -split only end_date, for ex: "2023/03/31 - 2025/03/30" , here split only "2025/03/30" (i.e = right side date )     

            try:
                lot_details_data.contract_end_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Contract Dates")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
    

                    
        # Onsite Field -None
        # Onsite Comment 

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#innerTabContent'):
                    award_details_data = award_details()

                    # Onsite Field -"Supplier Awarded"
                    # Onsite Comment -for the "Awarded Solicitation" bidder name is avaible in "Award" ...

                    award_details_data.bidder_name = single_record.find_element(By.XPATH, '//*[contains(text(),"Supplier Awarded")]//following::p').text


                    # Onsite Field -Address
                    # Onsite Comment -

                    award_details_data.address = single_record.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::p[1]').text

                    # Onsite Field -Total Cost
                    # Onsite Comment -
                    award_details_data.grossawardvaluelc = single_record.find_element(By.XPATH, '//*[contains(text(),"Awarded Value")]//following::span[1]').text


                    # Onsite Field -Award Date
                    # Onsite Comment -

                    award_details_data.award_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Award Date")]//following::p[1]').text

            		
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
    

               


    
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#       ref_url for 3rd format :  "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"


#       to view  above format  go to "Status" Drop down , and select "award solicitation" -- 
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


    # Onsite Field -Reference Number
    # Onsite Comment -format 3

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),'Reference Number')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -format 3 ,if notice_no is not available in "Reference Number"  field then pass notice_no from notice_url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Published
    # Onsite Comment -format 3 ,

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Published')]//following::td[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Amount
    # Onsite Comment -format 3 , take the following data from "Amount" field

    try:
        notice_data.est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),'Amount')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Amount
    # Onsite Comment -format 3 , take the following data from "Amount" field

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),'Amount')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details >> Category
    # Onsite Comment -format 3 , take the following data from "Category	" field

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),'Category')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Description')]//following::table[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -format 3

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Description')]//following::table[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Buyer Information
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td:nth-child(2) > fieldset:nth-child(23)'):
            customer_details_data = customer_details()
        # Onsite Field -Buyer Information
        # Onsite Comment -split the data between "Buyer Information" and "Address:" field

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Buyer Information')]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Address:
        # Onsite Comment -split the data between "Address:" and "city" field,  ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),'Buyer Information')]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -City         :
        # Onsite Comment -split the data between "City" and "Province" field ,   ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),'Buyer Information')]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Province     :
        # Onsite Comment -split the data between "Province" and "Postal Code" field

            try:
                customer_details_data.org_state = page_details.find_element(By.XPATH, '//*[contains(text(),'Buyer Information')]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in org_state: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postal Code  :
        # Onsite Comment -split the data between "Postal Code  :" and "Telephone" field, ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),'Buyer Information')]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Telephone
        # Onsite Comment -split the data between "Telephone  " and "E-mail"  ,      ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),'Buyer Information')]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -E-mail       :
        # Onsite Comment -split the data after "E-mail"

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),'Buyer Information')]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#Table7 > tbody > tr'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -here we pass the local_title as a lot_title

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.rowTitle').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Supplier Information
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'fieldset:nth-child(20)'):
                    award_details_data = award_details()
		
                    # Onsite Field -Supplier Information
                    # Onsite Comment -for bidder_name split the data between "Supplier Information" and "Greyback Construction Ltd." field,   take first line as a bidder name , ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'fieldset:nth-child(20)').text
			
                    # Onsite Field -Supplier Information
                    # Onsite Comment -for address split the data between "Greyback Construction Ltd" and "Buyer Information" , skip the first line for addres , ref_url : "https://legacy.merx.com/English/SUPPLIER_Menu.asp?WCE=Show&TAB=3&PORTAL=MERX&State=8&id=1149181&hcode=7v9nTQNzZkzY0vCqfLmWkw%3D%3D"

                    award_details_data.address = page_details.find_element(By.CSS_SELECTOR, 'fieldset:nth-child(20)').text
			
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
    urls = ["https://www.merx.com/public/solicitations/bid-results?keywords=&solSearchStatus=bidResultsSolicitationsTab" ,  	"https://www.merx.com/public/solicitations/awarded?keywords=&solSearchStatus=awardedSolicitationsTab"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="solicitationsList"]/tbody/tr/td'),page_check))
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