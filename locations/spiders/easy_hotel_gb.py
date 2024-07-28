from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class EasyHotelGBSpider(SitemapSpider, StructuredDataSpider):
    name = "easy_hotel_gb"
    item_attributes = {"brand": "Easy Hotel", "brand_wikidata": "Q17011598"}
    sitemap_urls = ["https://www.easyhotel.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.easyhotel\.com\/hotels\/([-\w]+\/[-\w]+\/[-\w]+)$",
            "parse_sd",
        )
    ]
    wanted_types = ["Hotel"]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("www.www.", "www.")
            yield entry

    def inspect_item(self, item, response):
        item["state"] = None
        yield item
