
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class YoSushiGBSpider(SitemapSpider, StructuredDataSpider):
    name = "yo_sushi_gb"
    item_attributes = {"brand": "Yo! Sushi", "brand_wikidata": "Q3105441"}
    sitemap_urls = ["https://yosushi.com/sitemap.xml"]
    sitemap_rules = [(r"https://yosushi.com/restaurants/[-\w]+", "parse")]
    wanted_types = ["Restaurant"]
    drop_attributes = {"facbook", "twitter", "email"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"], item["lon"] = ld_data["latitude"], ld_data["longitude"]
        item["branch"] = item.pop("name")
        yield item
