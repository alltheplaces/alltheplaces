from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingBOSpider(Spider):
    name = "burger_king_bo"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://cmsappbk.burgerking.com.bo/api/cliente-invitado/generar-token"]
    access_token = ""
    client_id = "00000000-0000-0000-0000-000000000000"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.access_token = response.json()["data"]["token"]
        yield JsonRequest(
            url="https://cmsappbk.burgerking.com.bo/api/ciudad/listar",
            callback=self.parse_cities,
        )

    def parse_cities(self, response: Response, **kwargs: Any) -> Any:
        for city in response.json()["data"]:
            yield JsonRequest(
                url="https://cmsappbk.burgerking.com.bo/api/comercio/filtro",
                data={
                    "id_tipo_pedido": 2,  # 1: pick up  2: restaurant, both results same.
                    "id_cliente": self.client_id,
                    "id_ciudad": int(city["id"]),
                    "latitud": city["latitud"],
                    "longitud": city["longitud"],
                },
                headers={"Authorization": f"Bearer {self.access_token}"},
                callback=self.parse_locations,
                cb_kwargs=dict(city=city["nombre"]),
            )

    def parse_locations(self, response: Response, city: str) -> Any:
        for location in response.json().get("data", []):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("BK ").removeprefix("Bk ")
            item["street"] = item.pop("addr_full")
            item["city"] = city
            apply_category(Categories.FAST_FOOD, item)
            yield item
