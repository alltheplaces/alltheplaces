from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class ApcoaSpider(CrawlSpider, StructuredDataSpider):
    name = "apcoa"
    item_attributes = {"brand": "APCOA Parking", "brand_wikidata": "Q296108"}
    allowed_domains = [
        "www.apcoa.at",
        "www.apcoa.be",
        "www.apcoa.dk",
        "www.apcoa.de",
        "www.apcoa.ie",
        "www.apcoa.it",
        "www.apcoa.nl",
        "www.apcoa.no",
        "www.apcoa.se",
        "www.apcoa.co.uk",
        "www.apcoa.pl",
        "www.apcoa.ch",
    ]
    start_urls = [
        "https://www.apcoa.at/standorte/staedte/alle-staedte/",  # Austria
        "https://www.apcoa.be/alle-locaties/",  # Belgium
        "https://www.apcoa.dk/alle-lokationer/",  # Denmark
        "https://www.apcoa.de/standorte/alle-standorte/",  # Germany
        "https://www.apcoa.ie/locations/all-locations/",  # Ireland
        "https://www.apcoa.it/parcheggi/",  # Italy
        "https://www.apcoa.nl/alle-locaties/",  # Netherlands
        "https://www.apcoa.no/finnparkering/parkering/",  # Norway
        "https://www.apcoa.se/alla-staeder/",  # Sweden
        "https://www.apcoa.co.uk/parking-locations/all-locations/",  # UK
        "https://www.apcoa.pl/en/parking-locations/all-locations/",  # Poland
        "https://www.apcoa.ch/en/parking-locations/cities/all-cities/",  # Switzerland
    ]
    rules = [
        Rule(
            LinkExtractor(
                allow=[
                    ".*/parken/.*",  # Austria, Germany
                    ".*/parkings-per-stad/.*",  # Belgium
                    ".*/all-locations-by-city/.*",  # Denmark
                    ".*/parking/.*",  # Ireland
                    ".*/parcheggi-in/.*",  # Italy
                    ".*/parkeerplaats/.*",  # Netherlands
                    ".*/finn-parkering/.*",  # Norway
                    ".*/parkering-i/.*",  # Sweden
                    ".*/parking-in/.*",  # UK
                ]
            ),
            callback="parse_sd",
            follow=True,
        )
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["image"] = None
        extract_google_position(item, response)
        yield item
