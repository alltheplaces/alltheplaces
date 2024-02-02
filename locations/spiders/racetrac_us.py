from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RaceTracUSSpider(SitemapSpider, StructuredDataSpider):
    name = "racetrac_us"
    item_attributes = {"brand": "RaceTrac", "brand_wikidata": "Q735942"}
    allowed_domains = ["www.racetrac.com"]
    sitemap_urls = ("https://www.racetrac.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https:\/\/www\.racetrac\.com\/Locations\/", "parse_sd"),
    ]
    wanted_types = ["GasStation"]
