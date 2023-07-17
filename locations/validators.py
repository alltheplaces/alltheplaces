from schematics.models import Model
from schematics.types import (
    DateType,
    DecimalType,
    DictType,
    ListType,
    StringType,
    URLType,
)


class LocationItem(Model):
    ref = StringType(required=True)
    name = StringType(required=True)
    brand = StringType(required=True)
    categories = ListType(StringType, required=True, min_size=1)
    latitude = DecimalType(required=True, min_value=-90, max_value=90)
    longitude = DecimalType(required=True, min_value=-180, max_value=180)
    addr_full = StringType(required=True)
    street = StringType(required=True)
    city = StringType(required=True)
    postcode = StringType(required=True)
    country = StringType(required=True, min_length=2, max_length=2)
    url_source = URLType(required=True)
    extras = StringType()
    opening_hours = StringType()

    spider_name = StringType(required=True)
    schedule_date = DateType(required=True)
    scrapy_cloud_ref = StringType()
