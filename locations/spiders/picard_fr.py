from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PicardFRSpider(SitemapSpider, StructuredDataSpider):
    name = "picard_fr"
    item_attributes = {"brand": "Picard", "brand_wikidata": "Q3382454"}
    allowed_domains = ["magasins.picard.fr"]
    sitemap_urls = ["https://magasins.picard.fr/sitemap.xml"]
    sitemap_follow = [r"https:\/\/magasins\.picard\.fr\/locationsitemap\d+\.xml"]
    drop_attributes = {"image"}
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("PICARD ")
        yield item
