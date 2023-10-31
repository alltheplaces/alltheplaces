from locations.storefinders.yext import YextSpider


class VodafoneITSpider(YextSpider):
    name = "vodafone_it"
    item_attributes = {"brand": "Vodafone", "brand_wikidata": "Q122141"}
    api_key = "07377ddb3ff87208d4fb4d14fed7c6ff"
    api_version = "20220511"
