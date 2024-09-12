from typing import Dict, Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class BabyCityZASpider(AmastyStoreLocatorSpider):
    name = "baby_city_za"
    item_attributes = {"brand": "Baby City", "brand_wikidata": "Q116732888"}
    allowed_domains = ["www.babycity.co.za"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    opening_hours_map = {}

    def parse(self, response: Response) -> Iterable[Feature]:
        self.opening_hours_map = self.parse_opening_hours(response.json()["block"])
        yield from self.parse_features(response.json()["items"])

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector):
        item.pop("website")  # Websites don't seem to be provided or are the homepage
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        info = popup_html.xpath('.//div[@class="amlocator-info-popup"]/text()').getall()
        for line in info:
            if line.strip().startswith("City:"):
                item["city"] = line.replace("City:", "").strip()
            elif line.strip().startswith("Postal Code:"):
                item["postcode"] = line.replace("Postal Code:", "").strip()
            elif line.strip().startswith("State:"):
                item["state"] = line.replace("State:", "").strip()
            elif line.strip().startswith("Address:"):
                item["street_address"] = line.replace("Address:", "").strip()

        item["opening_hours"] = self.opening_hours_map.get(str(item["ref"]))

        yield item

    @staticmethod
    def parse_opening_hours(html: str) -> Dict[str, OpeningHours]:
        hours_map = {}
        for x in Selector(text=html).xpath('//div[@class="amlocator-store-desc"]'):
            _id = x.xpath("@data-amid").get()
            oh = OpeningHours()
            hours = " ".join(x.xpath('.//div[@class="amlocator-schedule-table"]//text()').getall())
            oh.add_ranges_from_string(hours)
            hours_map[_id] = oh
        return hours_map
