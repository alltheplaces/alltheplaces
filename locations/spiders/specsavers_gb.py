from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SpecsaversGBSpider(CrawlSpider, StructuredDataSpider):
    name = "specsavers_gb"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    start_urls = ["https://www.specsavers.co.uk/stores/full-store-list"]
    rules = [Rule(LinkExtractor(allow=r"https:\/\/www\.specsavers\.co\.uk\/stores\/(.+)"), callback="parse_sd")]

    # Stores that include hearing tests are given an extra page e.g.
    # https://www.specsavers.co.uk/stores/barnsley-hearing
    # We can't just ignore any that end with "-hearing" as some are valid e.g
    # https://www.specsavers.co.uk/stores/eastdereham-hearing
    # However the fake ones currently redirect to "?hearing=true"
    # So we can disable redirecting
    custom_settings = {"REDIRECT_ENABLED": False}
    download_delay = 1
    wanted_types = ["Optician"]
