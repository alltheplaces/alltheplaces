from locations.storefinders.wakefern import WakefernSpider


class PriceriteUSSpider(WakefernSpider):
    name = "pricerite_us"
    item_attributes = {"brand": "Price Rite", "brand_wikidata": "Q7242560"}
    start_urls = ["https://www.priceritemarketplace.com/"]
    requires_proxy = True
