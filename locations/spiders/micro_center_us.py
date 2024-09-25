from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MicroCenterUSSpider(CrawlSpider, StructuredDataSpider):
    name = "micro_center_us"
    item_attributes = {"brand": "Micro Center", "brand_wikidata": "Q6839153"}
    allowed_domains = ["www.microcenter.com"]
    start_urls = ["https://www.microcenter.com/site/stores/default.aspx"]
    rules = [Rule(LinkExtractor(r"/site/stores/[^.]+\.aspx$"), "parse")]
    wanted_types = ["ComputerStore"]
    time_format = "%H"
    convert_microdata = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Micro Center").strip(" -")
        apply_category(Categories.SHOP_COMPUTER, item)
        yield item
