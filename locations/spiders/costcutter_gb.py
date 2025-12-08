import scrapy

from locations.linked_data_parser import LinkedDataParser


class CostcutterGBSpider(scrapy.spiders.SitemapSpider):
    name = "costcutter_gb"
    item_attributes = {
        "brand": "Costcutter",
        "brand_wikidata": "Q5175072",
        "country": "GB",
    }
    allowed_domains = ["costcutter.co.uk"]
    sitemap_urls = ["https://store-locator.costcutter.co.uk/sitemap.xml"]
    sitemap_rules = [("/costcutter-*", "parse_store")]
    drop_attributes = {"image"}

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "ConvenienceStore")
        if item and "closed" not in item["name"].lower():
            return item
