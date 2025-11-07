from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SaturnDESpider(SitemapSpider, StructuredDataSpider):
    name = "saturn_de"
    item_attributes = {"brand": "Saturn", "brand_wikidata": "Q2543504"}
    allowed_domains = ["www.saturn.de"]
    sitemap_urls = ["https://www.saturn.de/sitemaps/sitemap-marketpages.xml"]
    sitemap_rules = [(r"/de/store/.+", "parse_sd")]
    wanted_types = ["Store"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Saturn ")
        item["phone"] = item["phone"].replace("/", "")

        apply_category(Categories.SHOP_ELECTRONICS, item)

        yield item
