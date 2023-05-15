from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class UbitricitySpider(Spider):
    name = "ubitricity"
    item_attributes = {"brand": "Ubitricity", "brand_wikidata": "Q113699692"}

    def start_requests(self):
        yield JsonRequest(
            url="https://portal-api.mobilstrom.de/v1/external_ssos/search?sso_types%5B%5D=ubitricity&bounds=-90,-180,90,180",
            headers={"X-API-TOKEN": "WEB_1049d590-d150-4f39-8240-3484a64dcc4c"},
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            location["location"] = location["address"].pop("location")
            location["address"]["street_address"] = clean_address(
                [location["address"].pop("street"), location["address"].pop("street2")]
            )
            location["ref"] = location["ssoId"]
            yield DictParser.parse(location)
