from scrapy import Selector

from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class BabyCityZA(AmastyStoreLocatorSpider):
    name = "baby_city_za"
    item_attributes = {"brand": "Baby City", "brand_wikidata": "Q116732888"}
    allowed_domains = ["www.babycity.co.za"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector):
        item.pop("website")  # Websites don't seem to be provided or are the homepage
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        info = popup_html.xpath('.//div[@class="amlocator-info-popup"]/text()').getall()
        for line in popup_html.xpath('.//div[@class="amlocator-info-popup"]/text()').getall():
            if line.strip().startswith("City:"):
                item["city"] = line.replace("City:", "").strip()
            elif line.strip().startswith("Postal Code:"):
                item["postcode"] = line.replace("Postal Code:", "").strip()
            elif line.strip().startswith("State:"):
                item["state"] = line.replace("State:", "").strip()
            elif line.strip().startswith("Address:"):
                item["street_address"] = line.replace("Address:", "").strip()
        yield item
