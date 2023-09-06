from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ZaxbysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "zaxbys_us"
    item_attributes = {"brand": "Zaxby's", "brand_wikidata": "Q8067525"}
    allowed_domains = ["www.zaxbys.com"]
    sitemap_urls = ["https://www.zaxbys.com/server-sitemap.xml"]
    sitemap_rules = [(r"\/locations\/[a-z]{2}\/[\w\-]+\/[\w\-]+\/?$", "parse_sd")]
    wanted_types = ["Restaurant"]
    custom_settings = {"REDIRECT_ENABLED": False}
    requires_proxy = True

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].rstrip("/")
            yield entry

    def post_process_item(self, item, response, ld_data):
        if "undefined" in item["website"]:
            return
        item.pop("image")
        item.pop("facebook")
        item.pop("twitter")
        yield item
