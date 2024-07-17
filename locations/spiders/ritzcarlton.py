from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.linked_data_parser import LinkedDataParser


class RitzCarltonSpider(SitemapSpider):
    name = "ritzcarlton"
    item_attributes = {"brand": "The Ritz Carlton", "brand_wikidata": "Q782200"}
    sitemap_urls = ["https://www.ritzcarlton.com/robots.txt"]
    sitemap_rules = [(r"/en/hotels/[a-z-]+/overview/$", "parse")]

    def parse(self, response):
        if item := LinkedDataParser.parse(response, "Hotel"):
            extract_google_position(item, response)
            item["ref"] = response.url
            yield item
