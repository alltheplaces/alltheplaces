from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AkzentHotelsDESpider(SitemapSpider, StructuredDataSpider):
    name = "akzent_hotels_de"
    item_attributes = {"brand": "AKZENT Hotels", "brand_wikidata": "Q122384815"}
    sitemap_urls = ["https://www.akzent.de/sitemap.xml"]
    sitemap_rules = [(r"\/hotels\/[a-z-]+$", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("AKZENT ", "")
        apply_category(Categories.HOTEL, item)
        yield item
