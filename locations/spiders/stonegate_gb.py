import scrapy

from locations.linked_data_parser import LinkedDataParser


class StonegateGBSpider(scrapy.spiders.SitemapSpider):
    name = "stonegate_gb"
    item_attributes = {
        "brand": "Stonegate",
        "brand_wikidata": "Q7619176",
    }
    sitemap_urls = ["https://great-british-pubs.co.uk/sitemap_index.xml"]
    sitemap_rules = [("/locations/", "parse")]
    download_delay = 0.2

    def parse(self, response):
        item = LinkedDataParser.parse(response, "BarOrPub")
        if item:
            item["ref"] = response.url
            item["website"] = response.url
            return item
