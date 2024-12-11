from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature


class HipermaxiBOSpider(Spider):
    name = "hipermaxi_bo"
    item_attributes = {
        "brand_wikidata": "Q81968262",
        "brand": "Hipermaxi",
    }

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://tienda-api.hipermaxi.com/api/v1/markets/activos?IdMarket=0&IdTipoServicio=0",
            headers={
                "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJJZEFwbGljYWNpb24iOiIyMDIwMDAyIiwiSWRVc3VhcmlvIjoiNjI3NjY3IiwiSWRQZXJmaWwiOiIxMDAwIiwic3ViIjoiMCIsInJvbGUiOiJ1c2VyIiwiQWNjZXNvIjoiNyIsImV4cCI6MTczMzkxODY3NiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo3MTAwIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdDo3MTAwIn0.0H2LXYMBc5cTpYGLKtpwqKgyOjz5fgjLkcyP4Vq1QKc"
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for locations in response.json()["Dato"]:
            for location_info in locations["Locatarios"]:
                item = Feature()
                item["ref"] = location_info.get("IdSucursal")
                item["lat"] = location_info.get("Latitud")
                item["lon"] = location_info.get("Longitud")
                item["branch"] = (
                    location_info.get("Descripcion", "").removeprefix("FARMACIA ").removeprefix("HIPERMAXI ")
                )
                item["street_address"] = location_info.get("Direccion")
                yield item
