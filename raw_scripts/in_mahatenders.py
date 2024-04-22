import gec_common.common_eprocure as common_eprocure

script_name = 'in_mahatenders'

domain_url = 'https://mahatenders.gov.in/nicgep'

org_state = 'Maharashtra'

common_eprocure.eprocure(script_name,domain_url,org_state)
