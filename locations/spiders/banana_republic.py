import scrapy

from locations.linked_data_parser import LinkedDataParser


class BananaRepublicSpider(scrapy.spiders.SitemapSpider):
    name = "banana_republic"
    item_attributes = {"brand": "Banana Republic", "brand_wikidata": "Q806085"}
    sitemap_urls = [
        "https://bananarepublic.gap.com/stores/sitemap.xml",
        "https://bananarepublic.gapcanada.ca/stores/sitemap.xml",
    ]
    sitemap_rules = [(".html", "parse"), ("ca/stores", "parse")]

    def parse(self, response):
        if item := LinkedDataParser.parse(response, "ClothingStore"):
            if item.get("lat"):
                item["name"] = "Banana Republic"
                item["ref"] = response.url
                if ("ca/stores") in response.url:
                    item["country"] = "CA"
                else:
                    item["country"] = "US"
                yield item
