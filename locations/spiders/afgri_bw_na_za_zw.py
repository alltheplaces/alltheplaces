from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class AfgriBWNAZAZWSpider(AgileStoreLocatorSpider):
    name = "afgri_bw_na_za_zw"
    item_attributes = {"brand": "AFGRI Equipment", "brand_wikidata": "Q119264464"}
    allowed_domains = ["afgriequipment.co.za"]
