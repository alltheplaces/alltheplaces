from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WrenKitchensGBSpider(CrawlSpider, StructuredDataSpider):
    name = "wren_kitchens_gb"
    item_attributes = {"brand": "Wren Kitchens", "brand_wikidata": "Q8037744"}
    allowed_domains = ["wrenkitchens.com"]
    start_urls = ["https://www.wrenkitchens.com/showrooms/"]
    rules = [Rule(LinkExtractor(allow=r"https:\/\/www\.wrenkitchens\.com\/showrooms\/([-\w]+)$"), callback="parse_sd")]
    wanted_types = ["HomeAndConstructionBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = response.url  # Some URLs redirect
        yield item
