from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CastoramaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "castorama_fr"
    item_attributes = {"brand": "Castorama", "brand_wikidata": "Q966971"}
    sitemap_urls = ["https://www.castorama.fr/robots.txt"]
    sitemap_follow = ["sitemap-magasins.xml"]
    sitemap_rules = [(r"/store/\d+", "parse_sd")]
    time_format = "%H:%M:%S Europe/Paris"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        if item["name"].startswith("Castorama "):
            item["branch"] = item.pop("name").removeprefix("Castorama ")
            item["name"] = "Castorama"
        elif item["name"].startswith("Casto "):
            item["branch"] = item.pop("name").removeprefix("Casto ")
            item["name"] = "Casto"

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
