from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BakkerBartNLSpider(CrawlSpider, StructuredDataSpider):
    name = "bakker_bart_nl"
    item_attributes = {"brand": "Bakker Bart", "brand_wikidata": "Q2177445"}
    start_urls = ["https://www.bakkerbart.nl/vestigingen"]
    rules = [Rule(LinkExtractor(allow="/vestigingen/"), callback="parse_sd")]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").replace("Bakker Bart 's-", "").replace("Bakker Bart ", "")
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
