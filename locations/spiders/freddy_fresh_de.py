from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FreddyFreshDESpider(CrawlSpider, StructuredDataSpider):
    name = "freddy_fresh_de"
    item_attributes = {"brand": "Freddy Fresh", "brand_wikidata": "Q124255344"}
    start_urls = ["https://www.freddy-fresh.de/stores/"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//div[@class="store"]'), "parse")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Freddy Fresh ")

        apply_category(Categories.FAST_FOOD, item)

        yield item
