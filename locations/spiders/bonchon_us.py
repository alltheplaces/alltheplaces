from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BonchonUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bonchon_us"
    item_attributes = {"brand": "Bonchon Chicken", "brand_wikidata": "Q4941248"}
    drop_attributes = {"facebook"}

    sitemap_urls = ["https://restaurants.bonchon.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").split("Bonchon")[1].strip(" -")

        yield item
