import re
from urllib.parse import urljoin

from chompjs import parse_js_object
from scrapy import Selector

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MccormickAndSchmicksUSSpider(JSONBlobSpider):
    name = "mccormick_and_schmicks_us"
    item_attributes = {"brand": "McCormick & Schmick's", "brand_wikidata": "Q6800562"}
    start_urls = ["https://www.mccormickandschmicks.com/store-locator/"]

    def extract_json(self, response):
        script = response.xpath('//script[contains(text(), "storeLocatorConfig(")]/text()').get()
        return parse_js_object(script.split("storeLocatorConfig(", 1)[1].rsplit(");", 1)[0])["locations"]

    def pre_process_data(self, location: dict) -> None:
        location["street_address"] = location.pop("street", None)
        location["url"] = urljoin(self.start_urls[0], location["url"])
        location["website"] = location["url"]
        location["phone"] = location.get("phone_number")

        if image := location.get("image"):
            location["image"] = image["url"]

    def post_process_item(self, item: Feature, response, location: dict):
        item["name"] = "McCormick & Schmick's"
        item["branch"] = location["name"]
        item.pop("addr_full", None)

        if opening_hours := self.parse_hours(location.get("hours")):
            item["opening_hours"] = opening_hours

        yield item

    @staticmethod
    def parse_hours(hours: str | None) -> OpeningHours | None:
        if not hours:
            return None

        opening_hours = OpeningHours()
        for line in Selector(text=hours).xpath("//text()").getall():
            line = line.strip()
            if line in ["Pick Up:", "Delivery:"]:
                break
            if re.match(r"^[A-Z]{3}(?:\s*-\s*[A-Z]{3})?:\s*\d{1,2}:\d{2} [AP]M - \d{1,2}:\d{2} [AP]M$", line):
                opening_hours.add_ranges_from_string(line)

        return opening_hours if opening_hours.as_opening_hours() else None
