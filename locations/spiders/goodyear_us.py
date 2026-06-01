from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoodyearUSSpider(SitemapSpider, StructuredDataSpider):
    name = "goodyear_us"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    sitemap_urls = ["https://www.goodyear.com/en-us/retail-locations-sitemap.xml"]
    sitemap_rules = [(r"^https://www.goodyear.com/en-us/shops/[^/]+/[^/]+/Goodyear-.+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["branch"] = item.pop("name").replace("Goodyear Auto Service - ", "")
        yield item
