from typing import Any, AsyncIterator

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class DavitaUSSpider(Spider):
    name = "davita_us"
    item_attributes = {"operator": "DaVita Dialysis", "operator_wikidata": "Q5207184", "country": "US"}
    allowed_domains = ["davita.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for state in GeonamesCache().get_us_states():
            yield JsonRequest(
                url=f"https://davita.com/wp-json/davita/v1/find-a-center?location={state}&p=1&lat=32.3182314&lng=-86.902298"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"].get("locations") or []:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["ref"] = location["facilityid"]
            item["name"] = location["facilityname"]
            item["street_address"] = merge_address_lines([location.get("address1"), location.get("adress2")])
            item[
                "website"
            ] = f'https://davita.com/locations/{item["state"]}/{item["city"]}/{location["address1"]}--{location["facilityid"]}'.lower().replace(
                " ", "-"
            )
            yield item
