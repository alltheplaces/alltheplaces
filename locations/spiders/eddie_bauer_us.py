from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class EddieBauerUSSpider(SitemapSpider, StructuredDataSpider):
    name = "eddie_bauer_us"
    item_attributes = {"brand": "Eddie Bauer", "brand_wikidata": "Q842174"}
    sitemap_urls = ["https://stores.eddiebauer.com/sitemap.xml"]
    sitemap_rules = [(r"stores.eddiebauer.com/\w{2}/[-.\w]+/[-\w]+", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CLOTHES, item)
        item["image"] = None
        yield item
