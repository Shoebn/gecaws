import gec_common.common_eprocure as common_eprocure

from gec_common import log_config
SCRIPT_NAME = 'in_wbtenders'
log_config.log(SCRIPT_NAME)

domain_url = 'https://wbtenders.gov.in/nicgep'

org_state = 'West Bengal'

common_eprocure.eprocure(SCRIPT_NAME,domain_url,org_state)
