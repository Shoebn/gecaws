import re
import sys
import pandas as pd
import psycopg2 as ps
from datetime import datetime, date
# Import numpy for handling NA values
import numpy as np
import xml.etree.ElementTree as ET
import os
import gec_common.web_application_properties as application_properties
from datetime import datetime

# Define the folder path
output_folder = application_properties.GENERATED_JSON_ROOT_DIR + "/" + "DG_OLD_OUTPUT"


# Function to create XML elements for each row
def create_xml_element(row):
    notice_element = ET.Element("NOTICE")
    for column, value in row.items():
        if isinstance(value, list):
            for v in value:
                if pd.notnull(v) and v != '' and column != 'script_name' and not (column == 'UPDATE' and not value):
                    child_element = ET.Element(column)
                    child_element.text = str(v)
                    notice_element.append(child_element)
        else:
            if pd.notnull(value) and value != '' and column != 'script_name' and not (column == 'UPDATE' and not value):
                child_element = ET.Element(column)
                child_element.text = str(value)
                notice_element.append(child_element)
    return notice_element



# Function to write XML files for each unique script_name with a maximum of 500 records per file
def write_xml_files(data, folder_path, main_tag, max_records_per_file=500):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Group the DataFrame by script_name
    grouped_data = data.groupby('script_name')
    
    for script_name, group in grouped_data:
        # Split the group into chunks of max_records_per_file
        chunks = [group[i:i + max_records_per_file] for i in range(0, len(group), max_records_per_file)]
        
        for idx, chunk in enumerate(chunks):
            xml_root = ET.Element(main_tag)
            for index, row in chunk.iterrows():
                notice_element = create_xml_element(row)
                xml_root.append(notice_element)
            
            # Create XML tree
            xml_tree = ET.ElementTree(xml_root)
            
            # Generate datetime string
            datetime_str = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            
            # Create XML file name
            file_name = f"{script_name}_{datetime_str}_{idx}.xml"
            
            file_path = os.path.join(folder_path, file_name)
            
            # Write XML file for the script_name chunk
            xml_tree.write(file_path)

# Define a function to determine if a value is None, 0.0, '', or NA
def is_valid_value(value):
    return value is not None and value != 0.0 and value != '' and not pd.isna(value)


def get_conn():
    try:
        db = ps.connect(
            host="prod-gec-db.chsqqj3urp6j.ap-south-1.rds.amazonaws.com",
            dbname="global_content_db",
            user="gecpgadmin",
            password="g3cStrongPass22",
            port="5432"
        )
        return db
    except Exception as e:
        return e

# Establish database connection
connection = get_conn()

# Get yesterday's date
yesterday_date_query = "SELECT MAX(created_time) FROM dgmarket_old_export_log"
cursor = connection.cursor()
cursor.execute(yesterday_date_query)
yesterday_date = cursor.fetchone()[0]

# Get today's date
today_date = datetime.now()
# today_date = '2024-04-15 18:00:00.000000'

# Load data from all tables into dataframes with filtering
tables = [
    ("tender", f"update_date BETWEEN '{yesterday_date}' AND '{today_date}' and notice_text is not null and ((date(notice_deadline) is not null or date(notice_deadline) >= date(now()) )  or notice_type  in (7)) and is_publish_on_gec is true and (completed_steps != 'deleted' or completed_steps is null)"),
    ("attachments", ""),  # No specific condition for this table
    ("award_details", ""),  # No specific condition for this table
    ("customer_details", ""),  # No specific condition for this table
    ("countries", ""),  # No specific condition for this table
    ("lot_details", ""),  # No specific condition for this table
    ("notice_cpv_mapping", ""),  # No specific condition for this table
    ("notice_fundings", ""),  # No specific condition for this table
    ("performance_country", ""),  # No specific condition for this table
    ("performance_state", ""),  # No specific condition for this table
    ("tender_criteria", "")  # No specific condition for this table
]

dfs = {}
posting_ids = None
for table, condition in tables:
    if table == "tender":
        query = f"SELECT * FROM {table} WHERE {condition}"
        dfs[table] = pd.read_sql(query, connection)
        posting_ids = dfs[table]['posting_id'].unique()
    if table == "countries":
        query = f"SELECT name,iso2 FROM {table}"
        dfs[table] = pd.read_sql(query, connection)
    else:
        if posting_ids is not None and len(posting_ids) > 0:
            query = f"SELECT * FROM {table} WHERE posting_id IN ({','.join(map(str, posting_ids))})"
            dfs[table] = pd.read_sql(query, connection)
        else:
            print("posting_ids tender is empty")

        
        # query = f"SELECT * FROM {table} WHERE posting_id IN ({','.join(map(str, posting_ids))})"
        # dfs[table] = pd.read_sql(query, connection)

# Check if the DataFrame is empty
if dfs['tender'].empty:
    print("DataFrame is empty")
else:
   # Perform column transformations
    # Add a new column 'update' with boolean value True where 'notice_type' is equal to 16
    dfs['tender']['UPDATE'] = dfs['tender']['notice_type'] == 16

    # Convert the boolean values in the 'update' column to True
    dfs['tender']['UPDATE'] = dfs['tender']['UPDATE'].astype(bool)

    # Rename the 'notice_type' column to 'TYPE'
    dfs['tender'].rename(columns={'notice_type': 'TYPE'}, inplace=True)

    # Replace values in the 'TYPE' column
    dfs['tender']['TYPE'] = dfs['tender']['TYPE'].replace({
        0: 'others',
        1: 'pn',
        2: 'gpn',
        3: 'pp',
        4: 'spn',
        5: 'rei',
        6: 'ppn',
        7: 'ca',
        8: 'rfc',
        9: 'acn',
        10: 'prj',
        11: 'vc',
        12: 'grn',
        13: 'acq',
        14: 'mrg',
        15: 'rpt',
        16: 'spn',
        # Add other mappings here
    })

    dfs['tender']['class_at_source'] = dfs['tender']['class_at_source'].replace({
        'OTHERS': ''
        # Add other mappings here
    })
    dfs['tender']['notice_contract_type'] = dfs['tender']['notice_contract_type'].replace({
        'Service': 'Services',
        'Works': 'Works',
        'Consultancy': 'Consultancy',
        'Non consultancy': 'Services',
        'Supply': 'Goods'})                
    
    dfs['tender']['source_of_funds'] = dfs['tender']['source_of_funds'].replace({
        'International agencies': 'MFA',
        'NGO':'MFA',
        'Own':'Own',
        'Others':'Own',
        'Self Funded':'Own',
        'Government funded':'Own'
        # Add other mappings here
    })

    dfs['tender']['procurement_method'] = dfs['tender']['procurement_method'].replace({
        2: 'Other',
        0: 'National Competitive Bidding (NCB)',
        1: 'International Competitive Bidding (ICB)',
        # Add other mappings here
    })
    # Rename the 'procurement_method' column to 'METHOD'
    dfs['tender'].rename(columns={'procurement_method': 'METHOD'}, inplace=True)


    # Define the list of all columns
    all_columns = [
        "notice_summary_english", "tender_quantity",
        "additional_tender_url", "dispatch_date",
        "local_title", "grossbudgeteuro", "netbudgeteuro", "grossbudgetlc",
        "netbudgetlc", "type_of_procedure",
        "bidding_response_method",
        "tender_cancellation_date", "tender_contract_end_date",
        "tender_contract_start_date", "tender_contract_number",
        "tender_is_canceled", "tender_award_date"
    ]
    
    # Fill blank or None values in 'notice_summary_english' with values from 'notice_title'
    dfs['tender']['notice_summary_english'] = dfs['tender']['notice_summary_english'].fillna(dfs['tender']['notice_title'])
    
    # Define a function to concatenate columns and limit to 2000 characters
    def concat_columns(row):
        summary = ""
        for col in all_columns:
            value = row[col]
            # Exclude columns with a value of 0.0
            if pd.notna(value) and value != "" and value != 0.0:
                summary += f"{col}: {value}\n"
        return summary[:2000]  # Limit to 2000 characters
    
    # Apply the function to concatenate columns
    dfs['tender']['notice_summary_english'] = dfs['tender'].apply(concat_columns, axis=1)

    
    # Rename the 'notice_summary_english' column to 'NOTICE_SUMMARY_ENGLISH'
    dfs['tender'].rename(columns={'notice_summary_english': 'NOTICE_SUMMARY_ENGLISH'}, inplace=True)

    # Selecting and renaming columns for performance_country DataFrame
    dfs['performance_country'] = dfs['performance_country'].groupby('posting_id').head(1).rename(columns={'performance_country': 'PERFORMANCE_COUNTRY'})[['posting_id', 'PERFORMANCE_COUNTRY']]

    # Selecting and renaming columns for performance_state DataFrame
    dfs['performance_state'] = dfs['performance_state'].groupby('posting_id').head(1).rename(columns={'performance_state': 'CITY_LOCALITY'})[['posting_id', 'CITY_LOCALITY']]

    # Selecting and renaming columns for customer_details DataFrame
    customer_details_grouped = dfs['customer_details'].groupby('posting_id').head(1)
    customer_details_grouped['ADDRESS'] = customer_details_grouped[['org_address', 'org_state', 'org_fax', 'org_website']].apply(lambda row: ' '.join(row.dropna()), axis=1)
    customer_details = customer_details_grouped.rename(columns={
        'org_name': 'ORGANIZATION',
        'contact_person': 'CONTACT_NAME',
        'org_phone': 'CONTACT_PHONE',
        'org_email': 'CONTACT_EMAIL',
        'org_city': 'CITY',
        'org_country': 'COUNTRY',
    })[['posting_id', 'ORGANIZATION', 'CONTACT_NAME', 'ADDRESS', 'CONTACT_PHONE', 'CONTACT_EMAIL', 'CITY', 'COUNTRY']]

    # Copy 'ORGANIZATION' column as 'BUYER'
    customer_details['BUYER'] = customer_details['ORGANIZATION']

    dfs['customer_details'] = customer_details


    
    # Selecting and renaming columns for award_details DataFrame
    dfs['award_details'] = dfs['award_details'].groupby('posting_id').head(1).rename(columns={
        'bidder_name': 'AWARDING_COMPANY',
        'bidder_country': 'AWARDING_COMPANY_COUNTRY',
        'address': 'AWARDING_COMPANY_ADDRESS',
        'initial_estimated_value': 'AWARDING_INITIAL_ESTIMATED',
        'final_estimated_value': 'AWARDING_FINAL_VALUE',
        'bid_recieved': 'AWARDING_BIDS_RECEIVED',
        'contract_duration': 'AWARDING_CONTRACT_DURATION',
        'award_date': 'AWARDING_AWARD_DATE'
    })[['posting_id', 'AWARDING_COMPANY', 'AWARDING_COMPANY_COUNTRY', 'AWARDING_COMPANY_ADDRESS', 'AWARDING_INITIAL_ESTIMATED', 'AWARDING_FINAL_VALUE', 'AWARDING_BIDS_RECEIVED', 'AWARDING_CONTRACT_DURATION', 'AWARDING_AWARD_DATE']]

    # Merge award_details with tender DataFrame
    dfs['tender'] = pd.merge(dfs['tender'], dfs['award_details'], on='posting_id', how='left')

    # Merge customer_details with tender DataFrame
    dfs['tender'] = pd.merge(dfs['tender'], dfs['customer_details'], on='posting_id', how='left')

    # Merge performance_country with tender DataFrame
    dfs['tender'] = pd.merge(dfs['tender'], dfs['performance_country'], on='posting_id', how='left')

    # Merge performance_state with tender DataFrame
    dfs['tender'] = pd.merge(dfs['tender'], dfs['performance_state'], on='posting_id', how='left')
    
    # Add a new column 'AWARDING_CURRENCY' to 'dfs['tender']'
    dfs['tender']['AWARDING_CURRENCY'] = np.where(
        (dfs['tender']['AWARDING_INITIAL_ESTIMATED'].apply(is_valid_value)) |
        (dfs['tender']['AWARDING_FINAL_VALUE'].apply(is_valid_value)),
        dfs['tender']['currency'],
        None
    )
    
    
    # Convert float values to strings before concatenating
    dfs['lot_details']['lot_number'] = dfs['lot_details']['lot_number'].astype(str)

    # Concatenate 'lot_title_english' and 'lot_actual_number' columns if 'lot_actual_number' is not None or not ''
    dfs['lot_details']['LOT_TITLE_WITH_NUMBER'] = np.where(
        (dfs['lot_details']['lot_number'].notnull()) & 
        (dfs['lot_details']['lot_number'] != '') & (dfs['lot_details']['lot_number'] != 'None'), 
        
        dfs['lot_details']['lot_number'] + ': ' + dfs['lot_details']['lot_title_english'], 
        dfs['lot_details']['lot_title_english']
    )

    # Convert float values to strings in 'LOT_TITLE_WITH_NUMBER' column
    dfs['lot_details']['LOT_TITLE_WITH_NUMBER'] = dfs['lot_details']['LOT_TITLE_WITH_NUMBER'].astype(str)
    
    # Group by 'posting_id' and concatenate 'LOT_TITLE_WITH_NUMBER'
    lots_info = dfs['lot_details'].groupby('posting_id')['LOT_TITLE_WITH_NUMBER'].apply(lambda x: '\n'.join(x)).reset_index()


    # Merge 'lots_info' into 'dfs['tender']'
    dfs['tender'] = pd.merge(dfs['tender'], lots_info, on='posting_id', how='left')

    # Rename the merged column to 'LOTS_INFO'
    dfs['tender'] = dfs['tender'].rename(columns={'LOT_TITLE_WITH_NUMBER': 'LOTS_INFO'})
    
    # Truncate 'LOTS_INFO' column to 2000 characters
    dfs['tender']['LOTS_INFO'] = dfs['tender']['LOTS_INFO'].str.slice(0, 2000)

    dfs['tender']['EARNEST_MONEY_DEPOSIT'] = dfs['tender']['earnest_money_deposit'].apply(lambda x: '' if len(str(x)) > 10 else x)

    
    # Selecting and renaming columns for tender_criteria DataFrame
    tender_criteria = dfs['tender_criteria'].copy()
    tender_criteria['tender_criteria_weight'] = tender_criteria['tender_criteria_weight'].astype(str)  # Convert weight to string
    
    # Convert 'tender_is_price_related' to string
    tender_criteria['tender_is_price_related'] = tender_criteria['tender_is_price_related'].astype(str)

    # Concatenate selected columns with ': ' separator
    tender_criteria['TENDER_CRITERIA_INFO'] = ( tender_criteria['tender_criteria_title'] )

    # Group by 'posting_id' and join 'TENDER_CRITERIA_INFO' with '; ' separator
    tender_criteria_info = tender_criteria.groupby('posting_id')['TENDER_CRITERIA_INFO'].apply(lambda x: '; \n'.join(x)).reset_index(name='AWARDS_CRITERIA')

    # Restrict length of 'AWARDS_CRITERIA' column to 2000 characters
    tender_criteria_info['AWARDS_CRITERIA'] = tender_criteria_info['AWARDS_CRITERIA'].str[:100]

    # Merge 'tender_criteria_info' into 'dfs['tender']'
    dfs['tender'] = pd.merge(dfs['tender'], tender_criteria_info, on='posting_id', how='left')
    
    # Group attachments by posting_id and concatenate external_url column values into a list
    attachments_urls = dfs['attachments'].groupby('posting_id')['external_url'].apply(list).reset_index(name='RESOURCE_URL')

    # Merge attachments_urls into dfs['tender'] on posting_id
    dfs['tender'] = pd.merge(dfs['tender'], attachments_urls, on='posting_id', how='left')

    # Group notice_cpv_mapping by posting_id and concatenate cpv_code column values into a list
    cpv_codes = dfs['notice_cpv_mapping'].groupby('posting_id')['cpv_code'].apply(list).reset_index(name='CPV')

    # Merge cpv_codes into dfs['tender'] on posting_id
    dfs['tender'] = pd.merge(dfs['tender'], cpv_codes, on='posting_id', how='left')
    
    # Group notice_fundings by posting_id and concatenate funding_agency column values into a list
    funding_agencies = dfs['notice_fundings'].groupby('posting_id')['funding_agency'].apply(list).reset_index(name='FUNDING_AGENCIES')

    # Merge funding_agencies into dfs['tender'] on posting_id
    dfs['tender'] = pd.merge(dfs['tender'], funding_agencies, on='posting_id', how='left')
    

    # Replace '<a>' tags with empty string
    dfs['tender']['NOTICE_TEXT'] = dfs['tender']['notice_text']

    # Replace special characters with spaces
    char_to_replace = {'': ' ','':' '}
    dfs['tender']['NOTICE_TEXT'] = dfs['tender']['NOTICE_TEXT'].apply(lambda text: text.translate(str.maketrans(char_to_replace)))

    # Get the size of the notice_text in KB
    dfs['tender']['NOTICE_TEXT_SIZE_KB'] = dfs['tender']['NOTICE_TEXT'].apply(lambda text: sys.getsizeof(text) / 1024)

    # Remove HTML tags and trim whitespace
    remove_tag = re.compile('<a.*?>|</a>')
    dfs['tender']['NOTICE_TEXT'] = dfs['tender']['NOTICE_TEXT'].apply(lambda text: re.sub(remove_tag, '', text).strip())

    # Get the size of the cleaned notice_text in KB
    dfs['tender']['NOTICE_TEXT_SIZE_KB'] = dfs['tender']['NOTICE_TEXT'].apply(lambda text: sys.getsizeof(text) / 1024)

    # If the size is still greater than 149KB, truncate the notice_text to 75000 characters
    dfs['tender']['NOTICE_TEXT'] = dfs['tender'].apply(lambda row: row['NOTICE_TEXT'][:75000] if row['NOTICE_TEXT_SIZE_KB'] > 149 else row['NOTICE_TEXT'], axis=1)

    # Drop the intermediate column 'NOTICE_TEXT_SIZE_KB'
    dfs['tender'].drop(columns=['NOTICE_TEXT_SIZE_KB'], inplace=True)
    


    
    # Convert 'publish_date' column to datetime format
    dfs['tender']['PUBLISHED_DATE'] = pd.to_datetime(dfs['tender']['publish_date'], errors='coerce')
    
    # Extract only the date part from 'PUBLISHED_DATE' column
    dfs['tender']['PUBLISHED_DATE'] = dfs['tender']['PUBLISHED_DATE'].dt.date
    
    # Fill NaN values with today's date
    dfs['tender']['PUBLISHED_DATE'] = dfs['tender']['PUBLISHED_DATE'].fillna(datetime.now().date())
    
    # Format 'PUBLISHED_DATE' column as '%Y/%m/%d'
    dfs['tender']['PUBLISHED_DATE'] = dfs['tender']['PUBLISHED_DATE'].apply(lambda x: x.strftime('%Y/%m/%d'))


    # Convert 'notice_deadline' column to datetime format with automatic format inference
    dfs['tender']['END_DATE'] = pd.to_datetime(dfs['tender']['notice_deadline'], infer_datetime_format=True, errors='coerce')

    # Format 'END_DATE' column as '%Y/%m/%d'
    dfs['tender']['END_DATE'] = dfs['tender']['END_DATE'].dt.strftime('%Y/%m/%d')
    
    dfs['tender']['DOCUMENT_COST'] = dfs['tender']['document_cost'].astype(int)

    # Convert 'document_purchase_start_time' column to datetime format
    dfs['tender']['DOCUMENT_PURCHASE_START_TIME'] = pd.to_datetime(dfs['tender']['document_purchase_start_time'])

    # Format 'DOCUMENT_PURCHASE_START_TIME' column as '%Y/%m/%d'
    dfs['tender']['DOCUMENT_PURCHASE_START_TIME'] = dfs['tender']['DOCUMENT_PURCHASE_START_TIME'].dt.strftime('%Y-%m-%d %H:%M:%S')

    dfs['tender']['DOCUMENT_PURCHASE_END_TIME'] = pd.to_datetime(dfs['tender']['document_purchase_end_time'])
    dfs['tender']['DOCUMENT_PURCHASE_END_TIME'] = dfs['tender']['DOCUMENT_PURCHASE_END_TIME'].dt.strftime('%Y-%m-%d %H:%M:%S')

    dfs['tender']['PRE_BID_MEETING_DATE'] = pd.to_datetime(dfs['tender']['pre_bid_meeting_date'])
    dfs['tender']['PRE_BID_MEETING_DATE'] = dfs['tender']['PRE_BID_MEETING_DATE'].dt.strftime('%Y-%m-%d')

    dfs['tender']['DOCUMENT_OPENING_TIME'] = pd.to_datetime(dfs['tender']['document_opening_time'])
    dfs['tender']['DOCUMENT_OPENING_TIME'] = dfs['tender']['DOCUMENT_OPENING_TIME'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Update PERFORMANCE_COUNTRY with the corresponding country name
    dfs['tender']['PERFORMANCE_COUNTRY'] = dfs['tender'].merge(dfs['countries'][['iso2', 'name']], how='left', left_on='PERFORMANCE_COUNTRY', right_on='iso2')['name']

    # Update COUNTRY with the corresponding country name
    dfs['tender']['COUNTRY'] = dfs['tender'].merge(dfs['countries'][['iso2', 'name']], how='left', left_on='COUNTRY', right_on='iso2')['name']

    # Update AWARDING_COMPANY_COUNTRY with the corresponding country name
    dfs['tender']['AWARDING_COMPANY_COUNTRY'] = dfs['tender'].merge(dfs['countries'][['iso2', 'name']], how='left', left_on='AWARDING_COMPANY_COUNTRY', right_on='iso2')['name']

    # Drop the unnecessary columns
#     dfs['tender'].drop(columns=['iso2_x', 'iso2_y'], inplace=True)



    
    dfs['tender'] = dfs['tender'].rename(columns={
    'notice_no': 'NOTICE_NO',
    'main_language': 'LANG',
    'notice_title': 'NOTICE_TITLE',
    'eligibility': 'ELIGIBILITY',
    'est_amount': 'EST_COST',
    'category': 'CATEGORY',
    'notice_url': 'NOTICE_URL',
    'currency': 'CURRENCY',
    'contract_duration': 'CONTRACT_DURATION',
    'project_name': 'PROJECT_NAME',
    'notice_contract_type': 'NOTICE_CONTRACT_TYPE',
    'source_of_funds': 'SOURCE_OF_FUNDS',
    'class_at_source': 'CLASS_AT_SOURCE',
    'class_codes_at_source': 'CLASS_CODES_AT_SOURCE',
    'class_title_at_source': 'CLASS_TITLE_AT_SOURCE'})
    
    # List of columns to keep
    columns_to_keep = ['script_name','NOTICE_NO', 'LANG', 'BUYER','PERFORMANCE_COUNTRY', 'NOTICE_TITLE', 'ELIGIBILITY', 'NOTICE_TEXT', 'TYPE', 'METHOD', 'EST_COST', 'PUBLISHED_DATE', 'END_DATE', 'CATEGORY', 'ORGANIZATION', 'CONTACT_NAME',  'ADDRESS', 'CONTACT_PHONE', 'CONTACT_EMAIL', 'CITY', 'COUNTRY', 'RESOURCE_URL', 'NOTICE_URL', 'CURRENCY', 'CITY_LOCALITY', 'AWARDING_COMPANY', 'AWARDING_COMPANY_COUNTRY', 'AWARDING_COMPANY_ADDRESS', 'AWARDING_CURRENCY', 'AWARDING_INITIAL_ESTIMATED', 'AWARDING_FINAL_VALUE', 'AWARDING_BIDS_RECEIVED', 'AWARDING_CONTRACT_DURATION', 'AWARDING_AWARD_DATE', 'UPDATE', 'CPV', 'FUNDING_AGENCIES', 'NOTICE_SUMMARY_ENGLISH', 'CONTRACT_DURATION', 'PROJECT_NAME', 'LOTS_INFO', 'AWARDS_CRITERIA', 'DOCUMENT_COST', 'EARNEST_MONEY_DEPOSIT', 'DOCUMENT_PURCHASE_START_TIME', 'DOCUMENT_PURCHASE_END_TIME', 'PRE_BID_MEETING_DATE', 'DOCUMENT_OPENING_TIME', 'NOTICE_CONTRACT_TYPE', 'SOURCE_OF_FUNDS', 'CLASS_AT_SOURCE', 'CLASS_CODES_AT_SOURCE', 'CLASS_TITLE_AT_SOURCE']

    # Drop columns that are not in the list
    dfs['tender'] = dfs['tender'][columns_to_keep].copy()
    


# Define the main tag
main_tag = "NOTICES"

# Write XML files for each unique script_name
write_xml_files(dfs['tender'], output_folder, main_tag)

# Print a message indicating that XML files have been successfully written
print("XML files have been successfully written!")

sql_query = f"INSERT INTO dgmarket_old_export_log (posting_ids, created_time) VALUES ('{','.join(map(str, posting_ids))}', '{today_date}')"
# Execute the SQL query
cursor.execute(sql_query)

# Commit the transaction and close the connection
connection.commit()

# Close the database connection
connection.close()
