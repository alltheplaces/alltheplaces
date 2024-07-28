from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class StonehouseGBSpider(SitemapSpider, StructuredDataSpider):
    name = "stonehouse_gb"
    item_attributes = {"brand": "Stonehouse", "brand_wikidata": "Q78192049"}
    sitemap_urls = ["https://www.stonehouserestaurants.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.stonehouserestaurants\.co\.uk\/nationalsearch\/[-\w]+\/[-\w]+$",
            "parse_sd",
        )
    ]
    wanted_types = ["Restaurant"]
