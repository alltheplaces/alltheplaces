from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CrateandbarrelSpider(CrawlSpider, StructuredDataSpider):
    name = "crateandbarrel"
    allowed_domains = ["www.crateandbarrel.com"]
    item_attributes = {"brand": "Crate & Barrel", "brand_wikidata": "Q5182604"}
    start_urls = ["https://www.crateandbarrel.com/stores/list-state/retail-stores"]
    requires_proxy = True
    rules = [
        Rule(
            LinkExtractor(allow=r"stores\/list-state\/retail-stores\/([a-zA-Z]{2})$"),
        ),
        Rule(
            LinkExtractor(allow=r"stores\/.+\/.+$"),
            callback="parse_sd",
        ),
    ]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"] = response.url
        item["branch"] = item.pop("name")
        yield item
