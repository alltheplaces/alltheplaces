from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import url_to_coords
from locations.linked_data_parser import LinkedDataParser
from locations.spiders.pets_at_home_gb import PetsAtHomeGBSpider


def extract_google_position(item, response):
    for link in response.xpath("//iframe/@src").extract():
        if "google.com" in link:
            item["lat"], item["lon"] = url_to_coords(link)
            return


def set_located_in(item, location):
    item["located_in"] = location["brand"]
    item["located_in_wikidata"] = location["brand_wikidata"]


class Vets4petsGBSpider(CrawlSpider):
    name = "vets4pets_gb"
    item_attributes = {
        "brand": "Vets4Pets",
        "brand_wikidata": "Q16960196",
    }
    start_urls = ["https://www.vets4pets.com/practices/"]
    rules = [Rule(LinkExtractor(allow="/practices/"), callback="parse_func", follow=True)]
    allowed_domains = ["vets4pets.com"]
    download_delay = 0.2

    def parse_func(self, response):
        item = LinkedDataParser.parse(response, "VeterinaryCare")
        if item:
            item["ref"] = response.url
            extract_google_position(item, response)
            if "petsathome" in item["street_address"].lower().replace(" ", ""):
                set_located_in(item, PetsAtHomeGBSpider.item_attributes)
            return item
