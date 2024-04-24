from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ActivFitnessCHSpider(Spider):
    name = "activ_fitness_ch"
    item_attributes = {"brand": "Activ Fitness", "brand_wikidata": "Q123747318"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            "https://web-api.migros.ch/widgets/stores?aggregation_options%5Bempty_buckets%5D=true&filters%5Bmarkets%5D%5B0%5D%5B0%5D=activ_fitness&verbosity=store&offset=0&limit=5000&key=9e74726846ff4e91a515edd24618d463ae26c89e7ea907fe30db2901da3691ba",
            headers={"Origin": "https://www.activfitness.ch"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            location.update(location.pop("location"))
            location["street_address"] = merge_address_lines([location.pop("address"), location.pop("address2")])
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("ACTIV FITNESS ")

            item["website"] = item["extras"]["website:de"] = "https://www.activfitness.ch/studios/{}/".format(
                location["slug"]
            )
            item["extras"]["website:fr"] = "https://www.activfitness.ch/fr/{}/".format(location["slug"])
            item["extras"]["website:it"] = "https://www.activfitness.ch/it/{}/".format(location["slug"])
            item["extras"]["website:en"] = "https://www.activfitness.ch/en/{}/".format(location["slug"])

            yield item
