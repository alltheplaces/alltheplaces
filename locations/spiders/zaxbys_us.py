from scrapy.spiders import SitemapSpider

from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class ZaxbysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "zaxbys_us"
    item_attributes = {"brand": "Zaxby's", "brand_wikidata": "Q8067525"}
    allowed_domains = ["www.zaxbys.com"]
    sitemap_urls = ["https://www.zaxbys.com/server-sitemap.xml"]
    sitemap_rules = [(r"\/locations\/[a-z]{2}\/[\w\-]+\/[\w\-]+\/?$", "parse_sd")]
    wanted_types = ["Restaurant"]
    custom_settings = {"REDIRECT_ENABLED": False}
    search_for_facebook = False
    search_for_twitter = False

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].rstrip("/")
            yield entry

    def post_process_item(self, item, response, ld_data):
        if "undefined" in item["website"]:
            return
        if "Closed" in item["name"]:
            set_closed(item)
        item["branch"] = item.pop("name")
        item.pop("image")
        item.pop("opening_hours")

        yield item
