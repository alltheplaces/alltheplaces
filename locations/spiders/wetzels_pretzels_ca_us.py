from locations.storefinders.storemapper import StoremapperSpider


class WetzelsPretzelsCAUSSpider(StoremapperSpider):
    name = "wetzels_pretzels_ca_us"
    item_attributes = {"brand": "Wetzel's Pretzels", "brand_wikidata": "Q7990205"}
    company_id = "13346"
