import psycopg2
# pip install psycopg2
from gec_common import application_properties
def get_conn():
    db = psycopg2.connect(user=application_properties.DATABASE_USERNAME,
                          password=application_properties.DATABASE_PASSWORD,
                          database=application_properties.DATABASE_NAME,
                          host=application_properties.DATABASE_HOST)
    return db
