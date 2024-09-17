from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HirebaseGBSpider(SitemapSpider, StructuredDataSpider):
    name = "hirebase_gb"
    item_attributes = {
        "brand": "Hirebase",
        "brand_wikidata": "Q100297859",
        # "extras": Categories.SHOP_XYZ.value
    }
    sitemap_urls = ["https://www.hirebase.uk/robots.txt"]
    sitemap_rules = [
        (r"https://www.hirebase.uk/storefinder/store/[\w-]+-\d+", "parse"),
    ]
