from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class TownFairTireUSSpider(CrawlSpider, StructuredDataSpider):
    name = "town_fair_tire_us"
    item_attributes = {"brand": "Town Fair Tire", "brand_wikidata": "Q121300374"}
    allowed_domains = ["www.townfairtire.com"]
    start_urls = ["https://www.townfairtire.com/store/tires/"]
    rules = [
        Rule(LinkExtractor(allow=r"/store/tires/[a-z-]+/?$"), follow=True),
        Rule(LinkExtractor(allow=r"/store/tires/[a-z-]+/[a-z0-9-]+/?$"), callback="parse_sd"),
    ]
    wanted_types = ["AutoPartsStore"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.removeprefix("https://www.townfairtire.com/store/tires/").removesuffix("/")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
