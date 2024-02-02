from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BelhavenPubsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "belhaven_pubs_gb"
    item_attributes = {
        "brand": "Belhaven Pubs",
        "brand_wikidata": "Q105516156",
    }
    sitemap_urls = ["https://www.belhaven.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.belhaven\.co\.uk\/pubs\/([-\w]+)\/([-\w]+)$", "parse_sd")]
