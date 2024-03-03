from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CaliforniaClosetsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "california_closets_us"
    item_attributes = {
        "brand_wikidata": "Q5020325",
        "brand": "California Closets",
    }
    sitemap_urls = ["https://www.locations.californiaclosets.com/sitemap.xml"]
    wanted_types = ["HomeGoodsStore"]
    sitemap_rules = [
        # Target specific stores like:
        # https://www.locations.californiaclosets.com/california-closets-charlotte-3ebf37abb3c4
        # Rather than /designer/ or
        # https://www.locations.californiaclosets.com/tx/houston
        (r"california-closets-(.*)$", "parse_sd"),
    ]
