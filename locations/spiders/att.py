from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ATTSpider(SitemapSpider, StructuredDataSpider):
    name = "att"
    item_attributes = {"brand": "AT&T", "brand_wikidata": "Q298594"}
    allowed_domains = ["www.att.com"]
    sitemap_urls = ["https://www.att.com/stores/sitemap.xml"]
    sitemap_rules = [(r"/\d+$", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        name = ""
        for part in item["name"].strip().split("\n"):
            if name:
                name += " "
            name += part.strip()
        item["name"] = name

        yield item
