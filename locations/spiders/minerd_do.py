from json import dumps
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

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

    def parse_regions(self, response, **kwargs):
        yield JsonRequest(
            url="https://apps.minerd.gob.do/Maps/MapsWebServices/DistritoWS.asmx/getDistritosByCodigosRegionales",
            data={"codigosRegionales": ",".join([region["CodigoRegional"] for region in response.json()["d"]])},
            callback=self.parse_districts,
        )

    def parse_districts(self, response, **kwargs):
        yield JsonRequest(
            url="https://apps.minerd.gob.do/Maps/MapsWebServices/PlantaFisicaWS.asmx/getPlantasFisicasByFilter",
            data={
                "parametros": dumps(
                    [
                        {
                            "ParameterName": "#selectDistritos",
                            "ParameterValue": ",".join([region["CodigoDistrito"] for region in response.json()["d"]]),
                        }
                    ]
                )
            },
            callback=self.parse_schools,
        )

    def parse_schools(self, response, **kwargs):
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

            # More info?
            # yield JsonRequest(
            #                 url="https://apps.minerd.gob.do/Maps/MapsWebServices/PlantaFisicaWS.asmx/getPlantaFisicaDetallesByFilter",
            #                 data={"parametros": json.dumps([{"ParameterName": "PF.Codigo", "ParameterValue": school["Codigo"]}])},
            #             )
