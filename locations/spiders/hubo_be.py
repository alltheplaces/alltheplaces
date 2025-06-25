from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HuboBESpider(SitemapSpider, StructuredDataSpider):
    name = "hubo_be"
    item_attributes = {"brand": "Hubo", "brand_wikidata": "Q3142153"}
    sitemap_urls = ["https://www.hubo.be/sitemap/central-sitemap-index.xml"]
    sitemap_rules = [("/winkels/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_HARDWARE, item)
        yield item
