from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BubbakoosBurritosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bubbakoos_burritos_us"
    item_attributes = {"brand": "Bubbakoo's Burritos", "brand_wikidata": "Q114619751"}
    sitemap_urls = ["https://locations.bubbakoos.com/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/locations\.bubbakoos\.com\/locations\/[a-z]{2}\/[\w\-]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict):
        item["branch"] = response.xpath("//h1/text()").get()
        item.pop("facebook", None)
        apply_category(Categories.FAST_FOOD, item)
        yield item
