from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SunAndSkiSportsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "sun_and_ski_sports_us"
    item_attributes = {"brand": "Sun & Ski Sports", "brand_wikidata": "Q7638173"}
    sitemap_urls = ["https://www.sunandski.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/[^/]+$", "parse_sd")]
    wanted_types = ["SportingGoodsStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
