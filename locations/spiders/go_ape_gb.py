import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoApeGB(SitemapSpider, StructuredDataSpider):
    name = "go_ape_gb"
    item_attributes = {"brand": "Go Ape", "brand_wikidata": "Q5574692"}
    sitemap_urls = ["https://goape.co.uk/googlesitemap.xml"]
    sitemap_rules = [(r"https:\/\/goape\.co\.uk\/locations\/([-\w]+)$", "parse_sd")]
    wanted_types = ["SportsActivityLocation"]

    def inspect_item(self, item, response):
        item["ref"] = re.match(self.sitemap_rules[0][0], response.url).group(1)

        yield item
