from typing import Any, AsyncIterator

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class CopecCLSpider(Spider):
    name = "copec_cl"
    item_attributes = {"brand": "Copec", "brand_wikidata": "Q1130956"}

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            url="https://86zpltvria.execute-api.us-east-1.amazonaws.com/Prod/api/station/salesforce?codEs=-1&company=1&region=-1&comuna=-1",
            method="POST",
            headers={"ApiKey": "d47d780f-5efc-4fd2-949c-57703d39013f"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["CodES"]
            item["lat"] = location["Latitud"]
            item["lon"] = location["Longitud"]
            item["street_address"] = location["Direccion"]
            item["city"] = location["Comuna"]
            item["state"] = location["Region"]
            apply_category(Categories.FUEL_STATION, item)
            yield item
