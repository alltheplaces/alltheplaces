from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CabelasSpider(SitemapSpider, StructuredDataSpider):
    name = "cabelas"
    item_attributes = {"brand": "Cabela's", "brand_wikidata": "Q2793714"}
    allowed_domains = ["stores.cabelas.com", "cabelas.ca"]
    sitemap_urls = ["https://stores.cabelas.com/sitemap.xml", "https://www.cabelas.ca/sitemap.xml"]
    sitemap_rules = [
        (r"https://stores.cabelas.com/[-\w]+", "parse_sd"),
        ("/find-a-store/", "parse_sd"),
    ]
    wanted_types = ["SportingGoodsStore", "Store"]
    drop_attributes = {"image"}
