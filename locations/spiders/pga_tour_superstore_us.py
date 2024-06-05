from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class PgaTourSuperstoreUSSpider(CrawlSpider, StructuredDataSpider):
    name = "pga_tour_superstore_us"
    item_attributes = {"brand_wikidata": "Q125705404"}
    start_urls = ["https://www.pgatoursuperstore.com/stores"]
    rules = [Rule(LinkExtractor(r"stores/detail\?StoreID=(\d+)$"), "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "Club Fittings" in item["name"]:
            return None
        item["branch"] = item.pop("name")
        item["website"] = response.url
        yield item
