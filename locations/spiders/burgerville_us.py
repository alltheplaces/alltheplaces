from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BurgervilleUSSpider(SitemapSpider, StructuredDataSpider):
    name = "burgerville_us"
    item_attributes = {"brand": "Burgerville", "brand_wikidata": "Q4998570"}
    allowed_domains = ["locations.burgerville.com"]
    sitemap_urls = ["https://locations.burgerville.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/locations.burgerville.com\/burgerville-.*",
            "parse_store",
        ),
    ]
    wanted_types = ["Restaurant"]
    drop_attributes = {"image"}
