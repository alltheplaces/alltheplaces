from json import dumps
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class MinerdDOSpider(Spider):
    name = "minerd_do"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            method="POST",
            url="https://apps.minerd.gob.do/Maps/MapsWebServices/RegionalWS.asmx/getRegionales",
            callback=self.parse_regions,
        )

    def parse_regions(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://apps.minerd.gob.do/Maps/MapsWebServices/DistritoWS.asmx/getDistritosByCodigosRegionales",
            data={"codigosRegionales": ",".join([region["CodigoRegional"] for region in response.json()["d"]])},
            callback=self.parse_districts,
        )

    def parse_districts(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        # Requesting all districts at once times out, so request each district separately
        for district in response.json()["d"]:
            yield JsonRequest(
                url="https://apps.minerd.gob.do/Maps/MapsWebServices/PlantaFisicaWS.asmx/getPlantasFisicasByFilter",
                data={
                    "parametros": dumps(
                        [{"ParameterName": "#selectDistritos", "ParameterValue": district["CodigoDistrito"]}]
                    )
                },
                callback=self.parse_schools,
            )

    def parse_schools(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for school in response.json()["d"]:
            item = Feature()
            item["ref"] = school["Codigo"]
            item["lat"] = school["Latitud"]
            item["lon"] = school["Longitud"]
            item["name"] = school["Nombre"]
            item["phone"] = school["Telefono"]
            item["extras"]["school:type"] = school["Sector"]

            apply_category(Categories.SCHOOL, item)

            yield item
