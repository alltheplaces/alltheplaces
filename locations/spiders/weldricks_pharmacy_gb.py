from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class WeldricksPharmacyGBSpider(CrawlSpider, StructuredDataSpider):
    name = "weldricks_pharmacy_gb"
    item_attributes = {"brand": "Weldricks Pharmacy", "brand_wikidata": "Q123363321"}
    start_urls = ["https://www.weldricks.co.uk/branches"]
    rules = [Rule(LinkExtractor("/branches/"), "parse")]
    wanted_types = ["Pharmacy"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Weldricks Pharmacy ")

        yield item
