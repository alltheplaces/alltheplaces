import base64
import json
import zlib
from typing import Any, AsyncIterator

import scrapy
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class AllegoSpider(scrapy.Spider):
    name = "allego"
    item_attributes = {"operator": "Allego", "operator_wikidata": "Q75560554"}

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            url="https://alg.viewer.cit-fusion.com/getObjects.php",
            formdata={
                "post": base64.b64encode(
                    json.dumps(
                        {
                            "userId": "47",
                            "swLat": -90,
                            "swLng": -180,
                            "neLat": 90,
                            "neLng": 180,
                            "zoomlevel": 14,
                            "sphere": "ALG",
                            "favoritObjectsFilter": False,
                            "favoritOffersFilter": False,
                            "favoritSubjectsFilter": False,
                            "filters": "{}",
                            "prognosis_offset": -1,
                            "maxObjectCount": 50000,
                            "categories": ["1"],
                            "countAtIndex": -1,
                            "countWithValue": "",
                            "driveModeEnabled": False,
                            "id": None,
                        }
                    ).encode()
                ).decode()
            },
            headers={"Referer": "https://alg.viewer.cit-fusion.com/?language=en"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for ref, location in json.loads(zlib.decompress(base64.b64decode(response.text)))["pois"].items():
            item = Feature()
            item["ref"] = ref
            item["lat"] = location["coordinate"]["latitude"]
            item["lon"] = location["coordinate"]["longitude"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
