import gec_common.common_eprocure as common_eprocure

script_name = 'in_uktenders'

domain_url = 'https://uktenders.gov.in/nicgep'

org_state = 'Uttarakhand '

common_eprocure.eprocure(script_name,domain_url,org_state)
