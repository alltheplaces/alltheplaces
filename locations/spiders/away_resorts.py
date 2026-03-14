from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AwayResortsSpider(CrawlSpider, StructuredDataSpider):
    name = "away_resorts"
    item_attributes = {"brand": "Away Resorts", "brand_wikidata": "Q108045050"}
    start_urls = ["https://www.awayresorts.co.uk/parks/"]
    rules = [Rule(LinkExtractor(r"parks/[^/]+/([^/]+)/$"), callback="parse")]
    wanted_types = ["Resort"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["addr_full"] = item.pop("street_address")

        apply_category(Categories.LEISURE_RESORT, item)
        yield item
