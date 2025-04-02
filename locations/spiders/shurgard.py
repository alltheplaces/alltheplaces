from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class ShurgardSpider(CrawlSpider, StructuredDataSpider):
    name = "shurgard"
    item_attributes = {"brand": "Shurgard", "brand_wikidata": "Q3482670"}

    start_urls = [
        "https://www.shurgard.com/nl-be/opslagruimte-huren",
        "https://www.shurgard.com/da-dk/opbevaringsrum",
        "https://www.shurgard.com/fr-fr/garde-meuble",
        "https://www.shurgard.com/de-de/lagerraum-mieten",
        "https://www.shurgard.com/nl-nl/opslagruimte-in-nederland",
        "https://www.shurgard.com/sv-se/hyra-forrad",
        "https://www.shurgard.com/en-gb/self-storage-uk",
    ]

    rules = [
        Rule(LinkExtractor("/opslagruimte-huren/"), callback="parse_sd"),
        Rule(LinkExtractor("/opbevaringsrum/"), callback="parse_sd"),
        Rule(LinkExtractor("/garde-meuble/"), callback="parse_sd"),
        Rule(LinkExtractor("/lagerraum-mieten/"), callback="parse_sd"),
        Rule(LinkExtractor("/opslagruimte-in-nederland/"), callback="parse_sd"),
        Rule(LinkExtractor("-forrad/"), callback="parse_sd"),
        Rule(LinkExtractor("/self-storage-uk/"), callback="parse_sd"),
    ]
