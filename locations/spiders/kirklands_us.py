from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class KirklandsUSSpider(CrawlSpider, StructuredDataSpider):
    name = "kirklands_us"
    item_attributes = {
        "brand": "Kirkland's",
        "brand_wikidata": "Q6415714",
    }
    start_urls = ["https://www.kirklands.com/custserv/locate_store.cmd"]
    rules = [Rule(LinkExtractor(allow="/store.jsp?"), callback="parse_sd")]
    time_format = "%I %p"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        if isinstance(item.get("city"), list):  # e.g. ['Suite A-1', 'Huntsville']
            item["street_address"] = merge_address_lines([item["street_address"], item["city"][0]])
            item["city"] = item["city"][-1]
        yield item
