from urllib.parse import urlparse

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MichaelKorsSpider(SitemapSpider, StructuredDataSpider):
    name = "michael_kors"
    item_attributes = {"brand": "Michael Kors", "brand_wikidata": "Q134612138"}
    sitemap_urls = ["https://locations.michaelkors.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations.michaelkors.com/[\w-]+(?:/[\w-]+)?/[\w-]+/[\w-]+$", "parse_sd")]
    search_for_twitter = False
    search_for_fimage = False
    drop_attributes = {"facebook"}

    def sitemap_filter(self, entries):
        # Skip alternate-language versions of each page
        for entry in entries:
            url = urlparse(entry["loc"])
            if not url.path.startswith("/es/") and not url.path.startswith("/fr/"):
                yield entry

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].startswith("Michael Kors Outlet "):
            item["branch"] = item.pop("name").removeprefix("Michael Kors Outlet ")
            item["name"] = "Michael Kors Outlet"
        else:
            item["branch"] = item.pop("name").removeprefix("Michael Kors ")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
