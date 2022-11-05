import scrapy

from locations.linked_data_parser import LinkedDataParser


class AmericanFreightSpider(scrapy.spiders.SitemapSpider):
    name = "american_freight"
    item_attributes = {
        "brand": "American Freight",
        "brand_wikidata": "Q94360971",
    }
    allowed_domains = ["www.americanfreight.com"]
    sitemap_urls = [
        "https://www.americanfreight.com/sitemap.xml",
    ]
    sitemap_rules = [
        (r"/store/", "parse"),
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "DepartmentStore")
        item["ref"] = response.url.split("/")[-1]
        yield item
