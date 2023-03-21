from locations.storefinders.storerocket import StoreRocketSpider


class SoapyNobleUSSpider(StoreRocketSpider):
    name = "soapy_noble_us"
    item_attributes = {"brand": "Soapy Noble", "brand_wikidata": "Q117237115"}
    storerocket_id = "vo8xZwy4gn"
