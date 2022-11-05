import scrapy

from locations.linked_data_parser import LinkedDataParser


class MichaelsSpider(scrapy.spiders.SitemapSpider):
    name = "michaels"
    item_attributes = {"brand": "Michaels", "brand_wikidata": "Q6835667"}
    allowed_domains = ["michaels.com"]
    sitemap_urls = [
        "https://locations.michaels.com/robots.txt",
    ]
    sitemap_rules = [
        (r"^https://locations\.michaels\.com/[^/]+/[^/]+/[^/]+/$", "parse")
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "HobbyShop")
        item["name"] = response.css(".address-block div:first-of-type::text").get()
        yield item
