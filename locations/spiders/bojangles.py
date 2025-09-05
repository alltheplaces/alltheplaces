from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BojanglesSpider(SitemapSpider, StructuredDataSpider):
    name = "bojangles"
    item_attributes = {"brand": "Bojangles'", "brand_wikidata": "Q891163"}
    allowed_domains = ["locations.bojangles.com"]
    sitemap_urls = ["https://locations.bojangles.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations.bojangles.com/[^/]+/[^/]+/[^/]+.html$", "parse")]
    drop_attributes = {"image"}
    wanted_types = ["FastFoodRestaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Bojangles ")
        item["ref"] = response.url.replace("https://locations.bojangles.com/", "").replace(".html", "")
        yield item
