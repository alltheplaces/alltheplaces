from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FurnitureVillageGBSpider(SitemapSpider, StructuredDataSpider):
    name = "furniture_village_gb"
    item_attributes = {
        "brand": "Furniture Village",
        "brand_wikidata": "Q5509685",
        "country": "GB",
    }
    sitemap_urls = ["https://www.furniturevillage.co.uk/sitemap_index.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.furniturevillage\.co\.uk\/stores\/([-\w]+)\.html$",
            "parse_sd",
        )
    ]
    wanted_types = ["LocalBusiness"]
