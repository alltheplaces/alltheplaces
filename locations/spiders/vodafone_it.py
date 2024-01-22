from locations.spiders.vodafone_de import VODAFONE_SHARED_ATTRIBUTES
from locations.storefinders.yext import YextSpider


class VodafoneITSpider(YextSpider):
    name = "vodafone_it"
    item_attributes = VODAFONE_SHARED_ATTRIBUTES
    api_key = "07377ddb3ff87208d4fb4d14fed7c6ff"
    api_version = "20220511"
