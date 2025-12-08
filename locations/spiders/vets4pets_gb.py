from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.pets_at_home_gb import PetsAtHomeGBSpider
from locations.spiders.tesco_gb import set_located_in
from locations.structured_data_spider import StructuredDataSpider


class Vets4petsGBSpider(CrawlSpider, StructuredDataSpider):
    name = "vets4pets_gb"
    item_attributes = {"brand": "Vets4Pets", "brand_wikidata": "Q16960196"}
    start_urls = ["https://www.vets4pets.com/practices/"]
    rules = [
        Rule(LinkExtractor(allow=r"/practices/\?page=\d+")),
        Rule(
            LinkExtractor(allow="/practices/", restrict_xpaths="//a[contains(@class, 'listingBlock')]"),
            callback="parse_sd",
        ),
    ]
    allowed_domains = ["vets4pets.com"]
    drop_attributes = {"image"}
    wanted_types = ["VeterinaryCare"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        extract_google_position(item, response)
        if "petsathome" in item["street_address"].lower().replace(" ", ""):
            set_located_in(PetsAtHomeGBSpider.item_attributes, item)
        yield item
