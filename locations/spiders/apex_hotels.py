from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class ApexHotelsSpider(SitemapSpider):
    name = "apex_hotels"
    item_attributes = {"brand": "Apex Hotels", "brand_wikidata": "Q4779426"}
    sitemap_urls = ["https://www.apexhotels.co.uk/sitemapxml/"]
    sitemap_rules = [(r"https:\/\/www\.apexhotels\.co\.uk\/destinations\/([-\w]+)\/([-\w]+)\/$", "parse_item")]
    custom_settings = {"REDIRECT_ENABLED": "False"}

    def parse_item(self, response):
        item = LinkedDataParser.parse(response, "Hotel")
        if item:
            item["ref"] = response.url.split("/")[5]

            apply_category(Categories.HOTEL, item)

            return item
