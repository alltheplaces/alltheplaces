from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature, SocialMedia, set_social_media
from locations.pipelines.address_clean_up import clean_address


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
                item["street_address"] = clean_address(location_info.get("Direccion"), min_length=3)
                if location_info.get("TipoServicio", {}).get("Descripcion") == "Farmacia":
                    apply_category(Categories.PHARMACY, item)
                    item["nsi_id"] = "N/A"
                elif location_info.get("TipoServicio", {}).get("Descripcion") == "Supermercado":
                    apply_category(Categories.SHOP_SUPERMARKET, item)
                services = [service.get("Descripcion", "").upper() for service in location_info.get("TipoEntregas", [])]
                apply_yes_no(Extras.DELIVERY, item, "DELIVERY" in services)
                apply_yes_no(Extras.TAKEAWAY, item, "RECOGER EN SUCURSAL" in services)
                if whatsapp := location_info.get("ContactoWhatsapp"):
                    set_social_media(item, SocialMedia.WHATSAPP, whatsapp)
                yield item
