import json
from typing import Any, Iterable

from scrapy import Selector
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.paul_fr import PAUL_SHARED_ATTRIBUTES


class PaulGBSpider(JSONBlobSpider):
    name = "paul_gb"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    start_urls = ["https://www.paul-uk.com/find-a-paul"]
    websites = {}

    def extract_json(self, response: Response) -> Iterable[dict[str, Any]]:
        for location in response.xpath('.//div[@class="store"]'):
            self.websites[location.xpath("@id").get()] = location.xpath(
                './/a[contains(@href, "https://www.paul-uk.com/find-a-paul/")]/@href'
            ).get()

        return list(json.loads(response.xpath('//script[@id="find-paul-store-list"]/text()').get()).values())

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("PAUL ")
        item["ref"] = feature.get("axaptaId")
        item["website"] = self.websites.get(item["ref"])
        info = Selector(text=feature["info"])
        item["addr_full"] = clean_address([info.xpath(".//p[1]/text()").get()] + info.xpath(".//div/text()").getall())
        item["phone"] = info.xpath(".//p[2]/text()").get()

        item["opening_hours"] = OpeningHours()
        for day in info.xpath(".//div[2]/p/text()").getall():
            item["opening_hours"].add_ranges_from_string(day)

        apply_category(Categories.SHOP_BAKERY, item)

        yield item
