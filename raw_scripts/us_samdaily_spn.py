# ------------------------------------------------------------------------------------------------------------------------------------------------------

# CSV file URL : "https://sam.gov/data-services/Contract%20Opportunities/datagov?privacy=Public"

# ------------------------------------------------------------------------------------------------------------------------

# change script name from "us_samdaily_spn"  to "us_samdaily"
# -----------------------------------------------------------------





#   script_name :    us_samdaily_spn
# --------------------------
#  Notice_type = Type (field from CSV)
# ----------------------------------------------
# keywords  for notice type : 4
# - Sources Sought
# - Combined Synopsis/Solicitation
# - Special Notice
# - Solicitation
# - Presolicitation
# - Sale of Surplus Property


# DG Fields                               SAM.gov (field from CSV)
# -----------------------------------------------------
# notice_no :                               Sol#
# notice_no (from url)                      NoticeId 
# local_title 				                Title
# publish_date                              PostedDate
# notice_deadline				            ResponseDeadLine
# document_type_description 		        Type
# local_description                         Description
# notice_summary_english                    Description
# notice_url                                Link
# additional_tender_url			            AdditionalInfoLink                         
                         


# ----------------
# customer_details
# -----------------
                  
# 		 org_name 	                        Department/Ind.Agency
# 		 org_address	                    Office
# 		 org_city	                        City
# 		 org_state	                        State
# 		 postal_code                        ZipCode
#        org_country                        CountryCode
# 		 contact_person                     PrimaryContactFullname
# 		 org_email	                        PrimaryContactEmail
# 		 org_phone                          PrimaryContactPhone
#        	org_fax                         PrimaryContactFax



# -----------------
# lot_details
# -----------------

#        lot_title = local_title        Title (csv field)        




# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





#   script_name :    us_samdaily_ca
# --------------------------
#  Notice_type = Type (field from CSV)
# ----------------------------------------------
# keyword For notice type 7: 
# - Award Notice



# DG Fields                               SAM.gov (field from CSV)
# -----------------------------------------------------
# notice_no :                               AwardNumber :
# notice_no (from url)                      NoticeId 
# local_title 				                Title
# publish_date                              PostedDate
#Releated tender ID			                Sol#	
# document_type_description 		        Type
# local_description                         Description
# notice_summary_english                    Description
# notice_url                                Link
# additional_tender_url			            AdditionalInfoLink



# ----------------
# customer_details
# -----------------
                  
# 		 org_name 	                    Department/Ind.Agency
# 		 org_address	                Office
# 		 org_city	                    City
# 		 org_state	                    State
# 		 postal_code                    ZipCode
#        	org_country                 CountryCode
# 		 contact_person                 PrimaryContactFullname
# 		 org_email	                    PrimaryContactEmail
# 		 org_phone                      PrimaryContactPhone
#        	org_fax                     PrimaryContactFax


# -----------------
# lot_details
# -----------------

#        lot_title = local_title        Title (csv field)   


# 		---------------
# 		 award_details
# 		---------------

# 				award_date		   AwardDate
# 				bidder_name 		    Awardee	
# 				grossawardvaluelc           Award$	 


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




#   script_name :    us_samdaily_amd
# --------------------------
#  Notice_type = Type (field from CSV)
# ----------------------------------------------
# keyword For notice type 16: 
# - Justification
# - Fair Opportunity / Limited Sources Justification
# - Justification and Approval (J&A)
# - Modification/Amendment/Cancel



# DG Fields                               SAM.gov (field from CSV)
# -----------------------------------------------------
# notice_no :                               Sol#
# notice_no (from url)                      NoticeId 
# local_title 				                Title
# publish_date                              PostedDate
# notice_deadline				            ResponseDeadLine
# document_type_description 		        Type
# local_description                         Description
# notice_summary_english                    Description
# notice_url                                Link
# additional_tender_url			            AdditionalInfoLink
                         


# ----------------
# customer_details
# -----------------
                  
# 		 org_name 	                    Department/Ind.Agency
# 		 org_address	                Office
# 		 org_city	                    City
# 		 org_state	                    State
# 		 postal_code                    ZipCode
#        org_country                    CountryCode
# 		 contact_person                 PrimaryContactFullname
# 		 org_email	                    PrimaryContactEmail
# 		 org_phone                      PrimaryContactPhone
#        	org_fax                     PrimaryContactFax


# -----------------
# lot_details
# -----------------

#        lot_title = local_title        Title (csv field)        




# -------------------------------------------------------------------------------------------------------------------
#                           -------------------------------
#                            Attachments details as follows
#                           ---------------------------------
#        Take the attachments data from ("Link" CSV file field) 
#        1) ref_url : "https://sam.gov/opp/f20236cfb1b14ced9e7c95c68d38ce11/view" , "https://sam.gov/opp/e7dd02f882574f56876f9a17a0f407d9/view"



# Onsite Field -Attachments/Links
# Onsite Comment -

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#attachments-links > div.ng-star-inserted'):
            attachments_data = attachments()

        # Onsite Field -Document
        # Onsite Comment -

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div.file-icon').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File
        # Onsite Comment -split only file_name, for ex."36C25624R0018 Solicitation Questions Answers and Changes thru Amendment 0002.xlsx" , here take only "36C25624R0018 Solicitation Questions Answers and Changes thru Amendment 0002"

            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td div.file-icon+a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -File Size
        # Onsite Comment -
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field - File
        # Onsite Comment - Document

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td div.file-icon+a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
