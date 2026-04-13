from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KonaGrillUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kona_grill_us"
    item_attributes = {"brand": "Kona Grill", "brand_wikidata": "Q6428706"}
    sitemap_urls = ["https://konagrill.com/locations-sitemap.xml"]
    sitemap_rules = [(r"/location/([^/]+)/$", "parse_sd")]
    wanted_types = [["Restaurant"]]
    drop_attributes = {"name", "image"}
    search_for_facebook = False
