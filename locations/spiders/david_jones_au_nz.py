from chompjs import parse_js_object
import re
from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DavidJonesAUNZSpider(StructuredDataSpider):
    name = "david_jones_au_nz"
    item_attributes = {"brand": "David Jones", "brand_wikidata": "Q5235753"}
    allowed_domains = ["www.davidjones.com"]
    start_urls = ["https://www.davidjones.com/stores"]

    def parse(self, response: Response) -> Iterable[Request]:
        js_blob = response.xpath('//script[contains(text(), "stores: [")]/text()').get()
        js_blob = "[" + js_blob.split("stores: [", 1)[1].split("// ]]>", 1)[0]
        js_blob = re.sub(r"\s+", " ", js_blob)
        js_blob = js_blob.removesuffix("}")
        features = parse_js_object(js_blob)
        for feature in features:
            url = "https://www.davidjones.com" + feature["url"]
            yield Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["street_address"] = response.xpath('//span[@class="store-suburb"]/text()').get()
        item.pop("facebook", None)
        item.pop("twitter", None)
        if item["phone"] == "133 357":
            item.pop("phone", None)
        hours_text = " ".join(response.xpath('//div[@class="opening-hours"]//td/text()').getall())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
