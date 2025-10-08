from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ActionSpider(SitemapSpider, StructuredDataSpider):
    name = "action"
    item_attributes = {"brand": "Action", "brand_wikidata": "Q2634111"}
    sitemap_urls = ["https://www.action.com/robots.txt"]
    sitemap_rules = [(r"^(?!.*nl-be).*", "parse_sd")]
    sitemap_follow = ["store"]

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data["address"]["addressLocality"] = ld_data["address"]["addressLocality"].pop("city")
        ld_data["address"].update(ld_data["address"].pop("postalCode"))
        ld_data.pop("openingHours")

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        yield item
