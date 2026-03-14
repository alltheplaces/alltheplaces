from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class TorfsBESpider(SitemapSpider, StructuredDataSpider):
    name = "torfs_be"
    item_attributes = {"brand": "Schoenen Torfs", "brand_wikidata": "Q2547484"}
    sitemap_urls = ["https://www.torfs.be/sitemap-Torfs-WebshopBE-storeSitemap.xml"]
    sitemap_rules = [(r"/fr/magasins-", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_SHOES, item)
        yield item
