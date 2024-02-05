from urllib.parse import urljoin

from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class SofologyGBSpider(Spider):
    name = "sofology_gb"
    item_attributes = {"brand": "Sofology", "brand_wikidata": "Q5014159"}
    start_urls = ["https://api.sofology.co.uk/api/store/"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = clean_address(
                [location.pop("addressOne"), location.pop("addressTwo"), location.pop("addressThree")]
            )
            item = DictParser.parse(location)

            item["branch"] = location["outlet"]
            item["image"] = location["imageOutside"]
            item["website"] = urljoin(
                "https://www.sofology.co.uk/stores/", location["outlet"].lower().replace(" ", "-")
            )

            yield item
