from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RadleyGBSpider(CrawlSpider, StructuredDataSpider):
    name = "radley_gb"
    item_attributes = {"brand": "Radley London", "brand_wikidata": "Q7281436"}
    start_urls = ["https://www.radley.co.uk/pages/stores"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https?://www\.radley\.co\.uk/pages/radley-[a-zA-Z0-9-]+-store"), callback="parse_sd"
        ),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Radley ")
        extract_google_position(item, response)
        apply_category(Categories.SHOP_FASHION_ACCESSORIES, item)
        yield item
