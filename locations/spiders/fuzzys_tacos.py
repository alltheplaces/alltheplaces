from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class FuzzysTacosSpider(SitemapSpider):
    name = "fuzzystacos"
    item_attributes = {"brand": "Fuzzy's Taco Shop", "brand_wikidata": "Q85762348"}
    allowed_domains = ["fuzzystacoshop.com", "restaurants.fuzzystacoshop.com"]
    download_delay = 2
    sitemap_urls = ["https://restaurants.fuzzystacoshop.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/restaurants.fuzzystacoshop.com\/fuzzys-taco-shop-.*",
            "parse_store",
        ),
    ]

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "Restaurant")

        if item is None:
            return

        del item["image"]  # image url returned is not an image
        yield item
