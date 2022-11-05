import scrapy

from locations.google_url import extract_google_position
from locations.linked_data_parser import LinkedDataParser


class BritishHeartFoundationGBSpider(scrapy.spiders.SitemapSpider):
    name = "bhf_gb"
    item_attributes = {
        "brand": "British Heart Foundation",
        "brand_wikidata": "Q4970039",
    }
    sitemap_urls = ["https://www.bhf.org.uk/sitemap.xml"]
    sitemap_rules = [("-bhf-shop", "parse_shop")]
    download_delay = 0.5

    def parse_shop(self, response):
        if "news-archive" in response.url:
            return
        for store_type in ["ClothingStore", "Store"]:
            item = LinkedDataParser.parse(response, store_type)
            if item:
                item["website"] = response.url
                item["ref"] = response.url
                extract_google_position(item, response)
                return item
