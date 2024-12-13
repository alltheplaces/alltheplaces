from urllib.parse import urljoin

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class MarketBasketUSSpider(scrapy.Spider):
    name = "market_basket_us"
    item_attributes = {"brand": "Market Basket", "brand_wikidata": "Q2079198"}
    start_urls = ["https://www.shopmarketbasket.com/store-locations-rest?_format=json"]

    def parse(self, response):
        for poi in response.json():
            item = Feature()
            item["ref"] = poi["nid"]
            item["name"] = poi["title"]
            item["lat"], item["lon"] = poi["field_geolocation"].replace(" ", "").split(",")
            item["street_address"] = " ".join([poi["field_address_address_line1"], poi["field_address_address_line2"]])
            item["state"] = poi["field_address_administrative_area"]
            item["city"] = poi["field_address_locality"]
            item["postcode"] = poi["field_address_postal_code"]
            item["phone"] = poi["field_phone_number"]
            item["website"] = urljoin("https://www.shopmarketbasket.com", poi["path"])
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
