from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import url_to_coords
from locations.structured_data_spider import StructuredDataSpider
from locations.spiders.pets_at_home_gb import PetsAtHomeGBSpider


def extract_google_position(item, response):
    for link in response.xpath("//iframe/@src").extract():
        if "google.com" in link:
            item["lat"], item["lon"] = url_to_coords(link)
            return


def set_located_in(item, location):
    item["located_in"] = location["brand"]
    item["located_in_wikidata"] = location["brand_wikidata"]


class Vets4petsGBSpider(CrawlSpider, StructuredDataSpider):
    name = "vets4pets_gb"
    item_attributes = {
        "brand": "Vets4Pets",
        "brand_wikidata": "Q16960196",
    }
    start_urls = ["https://www.vets4pets.com/practices/"]
    rules = [Rule(LinkExtractor(allow="/practices/"), callback="parse_sd", follow=True)]
    allowed_domains = ["vets4pets.com"]
    download_delay = 0.2
    drop_attributes = {"image"}
    wanted_types = ["VeterinaryCare"]

    def post_process_item(self, item, response, location):
            extract_google_position(item, response)
            if "petsathome" in item["street_address"].lower().replace(" ", ""):
                set_located_in(item, PetsAtHomeGBSpider.item_attributes)
            yield item
