from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GermanAmericanUSSpider(CrawlSpider, StructuredDataSpider):
    name = "german_american_us"
    item_attributes = {"brand": "German American", "brand_wikidata": "Q120753420"}
    start_urls = ["https://germanamerican.com/locations/locations-overview/"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//li[contains(@data-services, "143")]//a'), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.BANK, item)
        yield item
