import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class BojanglesSpider(scrapy.spiders.SitemapSpider):
    name = "bojangles"
    item_attributes = {"brand": "Bojangles'", "brand_wikidata": "Q891163"}
    download_delay = 0.5
    allowed_domains = ["locations.bojangles.com"]
    sitemap_urls = ["https://locations.bojangles.com/sitemap.xml"]
    sitemap_rules = [
        (r"^https://locations.bojangles.com/[^/]+/[^/]+/[^/]+.html$", "parse_store"),
    ]
    drop_attributes = {"image"}

    def parse_store(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "FastFoodRestaurant")
        item["ref"] = response.url.replace("https://locations.bojangles.com/", "").replace(".html", "")
        yield item
