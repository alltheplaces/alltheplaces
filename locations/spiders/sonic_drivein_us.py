import uuid
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class SonicDriveinUSSpider(Spider):
    name = "sonic_drivein_us"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    item_attributes = {"brand": "Sonic", "brand_wikidata": "Q7561808"}
    session_id = uuid.uuid4().hex
    headers = {"x-channel": "WEBOA", "x-session-id": session_id}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"https://api-idp.sonicdrivein.com/snc/digital-exp-api/v1/locations/regions?countryCode=US",
            headers=self.headers,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for region in response.json()["locations"][0]["regions"]:
            yield JsonRequest(
                url=f'https://api-idp.sonicdrivein.com/snc/digital-exp-api/v1/locations/regions?regionCode={region["code"]}&countryCode=US',
                headers=self.headers,
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for region in response.json()["locations"][0]["regions"]:
            for city in region["cities"]:
                for location in city.get("locations", []):
                    location.update(location.pop("contactDetails", {}))
                    item = DictParser.parse(location)
                    item["state"] = location["address"]["stateProvinceCode"]
                    item["street_address"] = merge_address_lines(
                        [location["address"].get("line1"), location["address"].get("line2")]
                    )
                    item["name"] = None
                    if label := location["address"].get("label"):
                        item["branch"] = label.split(",")[0].strip()
                    item["website"] = (
                        f'https://www.sonicdrivein.com/locations/us/{item["state"]}/{item["city"]}/{location["address"]["line1"]}/store-{item["ref"]}/'.replace(
                            " ", "-"
                        ).lower()
                    )
                    yield item
