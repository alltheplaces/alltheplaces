import re

from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.structured_data_spider import StructuredDataSpider


class GoApeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "go_ape_gb"
    item_attributes = {"brand": "Go Ape", "brand_wikidata": "Q5574692"}
    sitemap_urls = ["https://goape.co.uk/googlesitemap.xml"]
    sitemap_rules = [(r"https:\/\/goape\.co\.uk\/locations\/([-\w]+)$", "parse_sd")]
    wanted_types = ["SportsActivityLocation"]

    def inspect_item(self, item, response):
        item["ref"] = re.match(self.sitemap_rules[0][0], response.url).group(1)
        apply_category({"leisure": "sports_centre", "aerialway": "zip_line"}, item)
        yield item
