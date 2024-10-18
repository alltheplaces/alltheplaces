import json
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LeadersRomansGroupGBSpider(JSONBlobSpider):
    name = "leaders_romans_group_gb"
    BRANDS = {
        "leaders": {"brand": "Leaders", "brand_wikidata": "Q111522674"},
        "romans": {"brand": "Romans", "brand_wikidata": "Q113562519"},
    }
    start_urls = [
        "https://www.leaders.co.uk/contact-us",
        "https://www.romans.co.uk/contact-us",
    ]

    def extract_json(self, response: Response) -> list:
        return json.loads(response.xpath("//@data-branches").get())

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = item["website"]
        item["branch"] = item.pop("name")
        item_properties = response.xpath(
            f'//img[contains(@alt, "{item["branch"]}")]/ancestor::div[@class="slider-item properties-contacts-slider-item"]'
        )
        item["addr_full"] = item_properties.xpath('.//*[@class="slider-item-description"]/text()').get()
        item["phone"] = item_properties.xpath('.//a[contains(@href,"tel:")]/@href').get()
        brand_key = response.url.split(".")[1]
        if brand := self.BRANDS.get(brand_key):
            item.update(brand)
        yield item
