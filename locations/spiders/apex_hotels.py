from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.linked_data_parser import LinkedDataParser


class ApexHotelsSpider(SitemapSpider):
    name = "apex_hotels"
    item_attributes = {"brand": "Apex Hotels", "brand_wikidata": "Q4779426", "extras": Categories.HOTEL.value}
    sitemap_urls = ["https://www.apexhotels.co.uk/sitemapxml/"]
    sitemap_rules = [(r"https:\/\/www\.apexhotels\.co\.uk\/destinations\/([-\w]+)\/([-\w]+)\/$", "parse_item")]
    custom_settings = {"REDIRECT_ENABLED": "False"}

    def parse_item(self, response):
        item = LinkedDataParser.parse(response, "Hotel")
        if item:
            item["ref"] = response.url.split("/")[5]

            return item
