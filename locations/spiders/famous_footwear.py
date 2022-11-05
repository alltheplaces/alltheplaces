import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FamousFootwearSpider(SitemapSpider, StructuredDataSpider):
    name = "famous_footwear"
    item_attributes = {"brand": "Famous Footwear", "brand_wikidata": "Q5433457"}
    sitemap_urls = ["https://www.famousfootwear.com/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]
    download_delay = 5.0
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }
    wanted_types = ["Store"]

    def inspect_item(self, item, response):
        matches = re.search(r'location: \["(.*)", "(.*)"\],', response.text)
        item["lat"], item["lon"] = matches.group(1), matches.group(2)
        yield item
