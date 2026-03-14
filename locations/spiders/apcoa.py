from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature


class ApcoaSpider(CrawlSpider):
    name = "apcoa"
    item_attributes = {"operator": "APCOA Parking", "operator_wikidata": "Q296108"}
    allowed_domains = [
        "www.apcoa.at",
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
        "https://www.apcoa.at/kurzparken/staedte-a-z",  # Austria
        "https://www.apcoa.dk/find-en-p-plads/find-en-parkeringsplads/find-en-p-plads",  # Denmark
        "https://www.apcoa.de/einmal-parken/parkplatzsuche",  # Germany
        "https://www.apcoa.ie/location-overview/location-overview/search-for-parking",  # Ireland
        "https://www.apcoa.it/sosta-breve/trovare-un-parcheggio/trova-un-parcheggio",  # Italy
        "https://www.apcoa.nl/kort-parkeren/parkeerplaats-vinden/parkeerplaats-zoeken",  # Netherlands
        "https://www.apcoa.no/finnparkering/parkering/",  # Norway
        "https://www.apcoa.se/hitta-parkering/hitta-en-parkeringsplats/hitta-din-parkeringsplats",  # Sweden
        "https://www.apcoa.co.uk/find-parking/find-parking/search-for-parking-spaces",  # UK
        "https://www.apcoa.pl/en/short-term-parking/find-a-car-park/looking-for-a-parking-space",  # Poland
        "https://www.apcoa.ch/en/short-stay-parking/find-a-car-park/car-park-search",  # Switzerland
    ]
    rules = [
        Rule(
            LinkExtractor(
                allow=[
                    r"/(?:kurzparken|einmal-parken)/standorte/[a-z-]+$",  # Austria, Germany
                    r"/find-en-p-plads/lokationer/[a-z-]+$",  # Denmark
                    r"/location-overview/location/[a-z-]+$",  # Ireland
                    r"/sosta-breve/sedi/[a-z-]+$",  # Italy
                    r"/kort-parkeren/locaties/[a-z-]+$",  # Netherland
                    r"/finn-parkering/lokasjoner/[a-z-]+$",  # Norway
                    r"/hitta-parkering/parkering/[a-z-]+$",  # Sweden
                    r"/find-parking/locations/[a-z-]+$",  # UK
                    r"/en/(?:short-term-parking|short-stay-parking)/locations/[a-z-]+$",  # Poland, Switzerland
                ]
            )
        ),
        Rule(
            LinkExtractor(
                allow=[
                    r"/(?:kurzparken|einmal-parken)/standorte/[a-z-]+/[a-z-0-9]+$",  # Austria, Germany
                    r"/find-en-p-plads/lokationer/[a-z-]+/[a-z-0-9]+$",  # Denmark
                    r"/location-overview/location/[a-z-]+/[a-z-0-9]+$",  # Ireland
                    r"/kort-parkeren/locaties/[a-z-]+/[a-z-0-9]+$",  # Netherland
                    r"/sosta-breve/sedi/[a-z-]+/[a-z-0-9]+$",  # Italy
                    r"/finn-parkering/lokasjoner/[a-z-]+/[a-z-0-9]+$",  # Norway
                    r"/hitta-parkering/parkering/[a-z-]+/[a-z-0-9]+$",  # Sweden
                    r"/find-parking/locations/[a-z-]+/[a-z-0-9]+$",  # UK
                    r"/en/(?:short-term-parking|short-stay-parking)/locations/[a-z-]+/[a-z-0-9]+$",
                ]
            ),
            callback="parse",
        ),
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse(self, response: TextResponse, **kwargs):
        item = Feature()
        item["branch"] = (
            response.xpath('//*[@class="text-h3 inline"]').xpath("normalize-space()").get().replace("| APCOA", "")
        )
        item["addr_full"] = response.xpath('//*[@class="main"]//span[2]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        yield item
