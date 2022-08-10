from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class BupaSpider(SitemapSpider):
    name = "bupa"
    item_attributes = {
        "brand": "Bupa",
        "brand_wikidata": "Q931628",
        "country": "GB",
    }
    sitemap_urls = ["https://www.bupa.co.uk/dentalsitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.bupa\.co\.uk\/dental\/dental-care\/practices\/([-\w]+)$",
            "parse_item",
        )
    ]

    def parse_item(self, response):
        item = LinkedDataParser.parse(response, "Dentist")

        if not item:
            return

        item["ref"] = item["website"].split("/")[6]

        if "Total Dental Care" in item["name"]:
            item["brand"] = "Total Dental Care"

        return item
