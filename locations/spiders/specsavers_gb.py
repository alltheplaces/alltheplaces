import scrapy
import re
from locations.structured_data_spider import StructuredDataSpider


class SpecsaversGBSpider(StructuredDataSpider,scrapy.Spider):
    name = "specsavers_gb"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    allowed_domains = ["specsavers.co.uk"]
    start_urls = ["https://www.specsavers.co.uk/stores/full-store-list"]

    def parse(self, response):
        for link in response.xpath('//*/@href').getall():
            if re.fullmatch("https:\/\/www\.specsavers\.co\.uk\/stores\/(.+)",
                            response.urljoin(link) ):
                yield scrapy.Request(response.urljoin(link), callback=self.parse_sd)

    # Stores that include hearing tests are given an extra page e.g.
    # https://www.specsavers.co.uk/stores/barnsley-hearing
    # We can't just ignore any that end with "-hearing" as some are valid e.g
    # https://www.specsavers.co.uk/stores/eastdereham-hearing
    # However the fake ones currently redirect to "?hearing=true"
    # So we can disable redirecting
    custom_settings = {"REDIRECT_ENABLED": False}
    download_delay = 1
    wanted_types = ["Optician"]
