from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import apply_category
from locations.structured_data_spider import StructuredDataSpider


class MedievalTimesUSSpider(CrawlSpider, StructuredDataSpider):
    name = "medieval_times"
    item_attributes = {
        "name": "Medieval Times Dinner & Tournament",
        "brand": "Medieval Times Dinner & Tournament",
        "brand_wikidata": "Q6806841",
        "extras": {"short_name": "Medieval Times"},
    }
    start_urls = ["https://www.medievaltimes.com/locations"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[@gtm-category="locations"]'), "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        apply_category({"amenity": "theatre"}, item)
        yield item
