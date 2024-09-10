from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CarpetrightGBSpider(CrawlSpider, StructuredDataSpider):
    name = "carpetright_gb"
    item_attributes = {"brand": "Carpetright", "brand_wikidata": "Q5045782"}
    start_urls = ["https://www.carpet-right.co.uk/stores/search"]
    rules = [Rule(LinkExtractor(r"https://www.carpet-right.co.uk/stores/(.+-carpetright)$"), "parse")]
    wanted_types = ["HomeGoodsStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = None
        item["branch"] = item.pop("name").removesuffix(" Carpetright")
        item["website"] = response.url

        yield item
