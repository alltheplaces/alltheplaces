from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RemoveryUSSpider(SitemapSpider, StructuredDataSpider):
    name = "removery_us"
    item_attributes = {"brand": "Removery", "brand_wikidata": "Q119982405"}
    sitemap_urls = ["https://removery.com/locations-sitemap.xml"]
    sitemap_follow = ["storelocator"]
    sitemap_rules = [(r"https://removery.com/tattoo-removal/locations/[\w-]+/[\w-]+/[\w-]+/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["image"] = None
        yield item
