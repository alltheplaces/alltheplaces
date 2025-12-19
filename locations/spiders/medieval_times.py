from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MedievalTimesSpider(CrawlSpider, StructuredDataSpider):
    name = "medieval_times"
    item_attributes = {"name": "Medieval Times", "brand": "Medieval Times", "brand_wikidata": "Q6806841"}
    start_urls = ["https://www.medievaltimes.com/locations"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[@gtm-category="locations"]'), "parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        apply_category(Categories.THEATRE, item)
        yield item
