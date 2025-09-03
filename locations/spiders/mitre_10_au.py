import json

import scrapy
from scrapy.http import Response

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class Mitre10AUSpider(StructuredDataSpider):
    name = "mitre_10_au"
    item_attributes = {"brand": "Mitre 10", "brand_wikidata": "Q6882393"}
    allowed_domains = ["mitre10.com.au"]
    start_urls = ["https://www.mitre10.com.au/stores"]

    def parse(self, response):
        data_raw = response.xpath(
            '//div[contains(@class, "store-search")]/following::script[@type="text/x-magento-init"]/text()'
        ).extract_first()
        data_clean = " ".join(data_raw.splitlines()).replace("\\/", "/")
        data_json = json.loads(data_clean)
        stores = data_json["*"]["Magento_Ui/js/core/app"]["components"]["store-locator-search"]["markers"]
        for store in stores:
            yield scrapy.Request(store["url"], self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item.pop("facebook")
        item.pop("image")
        item["branch"] = item.pop("name").removesuffix("Mitre 10")
        item["addr_full"] = response.xpath('//*[@class="address"]').xpath("normalize-space()").get()
        yield item
