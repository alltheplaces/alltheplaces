from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MccoysSpider(Spider, StructuredDataSpider):
    name = "mccoys"
    item_attributes = {"brand": "McCoy's", "brand_wikidata": "Q27877295"}
    allowed_domains = ["www.mccoys.com"]
    start_urls = ["https://www.mccoys.com/stores"]
    drop_attributes = {"image"}

    def parse(self, response: Response, **kwargs):
        # Extract all store URLs from links containing "View Store Details"
        for store_path in response.xpath('//a[contains(text(), "View Store Details")]/@href').getall():
            yield response.follow(url=store_path, callback=self.parse_sd)

    def pre_process_data(self, ld_data, **kwargs):
        # Fix the key name to match what StructuredDataSpider expects
        ld_data["openingHoursSpecification"] = ld_data.pop("OpeningHoursSpecification", None)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_TRADE, item)
        yield item
