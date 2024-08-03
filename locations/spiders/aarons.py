from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class AaronsSpider(SitemapSpider, StructuredDataSpider):
    name = "aarons"
    sitemap_urls = ["https://locations.aarons.com/robots.txt"]
    sitemap_rules = [(r"\.com/\w\w/\w\w/[^/]+/[^/]+$", "parse")]
    item_attributes = {"brand": "Aaron's", "brand_wikidata": "Q10397787", "extras": Categories.SHOP_FURNITURE.value}
    drop_attributes = {"name", "image"}
    wanted_types = ["Store"]
    search_for_twitter = False

    def sitemap_filter(self, entries):
        for entry in entries:
            if any(
                entry["loc"].endswith(s)
                for s in [
                    "/ashley-furniture",
                    "/bedroom-furniture",
                    "/computers",
                    "/gaming",
                    "/ge",
                    "/hp",
                    "/lg",
                    "/living-room-furniture",
                    "/mattresses",
                    "/refrigerators",
                    "/samsung",
                    "/service-area",
                    "/sony",
                    "/televisions",
                    "/washer-dryer",
                    "/woodhaven",
                ]
            ):
                continue
            yield entry
