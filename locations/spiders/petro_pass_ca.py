from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.petro_canada_ca import PetroCanadaCASpider


class PetroPassCASpider(PetroCanadaCASpider):
    name = "petro_pass_ca"
    item_attributes = {"brand": "Petro-Pass"}  # TODO: add brand_wikidata when available
    requires_proxy = True
    start_urls = [
        "https://www.petro-canada.ca/api/petrocanadabusiness/getCardlockLocations?fuel&hours&limit=10000000&place&province&range=10000000&service",
    ]

    def parse(self, response: Response) -> Iterable[Feature]:
        data = response.json()
        for store in data:
            yield from self.parse_store_data(store)

    def apply_website(self, item: Feature) -> None:
        item["website"] = "https://www.petro-canada.ca/en/business/petro-pass-near-me/{}-{}".format(
            "".join(char for char in item["street_address"] if char.isalnum()),
            "".join(char for char in item["city"] if char.isalnum()),
        )
