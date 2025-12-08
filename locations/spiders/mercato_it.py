from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class MercatoITSpider(Spider):
    name = "mercato_it"
    item_attributes = {"brand": "Mercatò", "brand_wikidata": "Q127389715"}

    items = None

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            "https://www.mymercato.it/action/getStoresList",
            data={
                "openToday": False,
                "servicesFilter": [],
                "brandsFilter": ["MERCATOBIG", "MERCATOLOCAL", "MERCATO", "MERCATOEXTRA"],
                "typesFilter": [],
                "partnersFilter": [],
                "registration": False,
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.items = {}
        for location in response.xpath("//div[@data-store-code]"):
            item = Feature()
            item["ref"] = location.xpath("@data-store-code").get()
            item["postcode"] = location.xpath("@data-cap").get()
            item["website"] = response.urljoin(location.xpath(".//a/@href").get())
            self.items[item["ref"]] = item

        yield JsonRequest(
            "https://www.mymercato.it/action/getStoresMapData",
            data={
                "openToday": False,
                "servicesFilter": [],
                "brandsFilter": ["MERCATOBIG", "MERCATOLOCAL", "MERCATO", "MERCATOEXTRA"],
                "typesFilter": [],
                "partnersFilter": [],
                "registration": False,
            },
            callback=self.parse_coords,
        )

    def parse_coords(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["features"]:
            item = self.items[location["properties"]["storeCode"]]
            item["geometry"] = location["geometry"]

            if location["properties"]["storeType"] == "mercato":
                item["branch"] = location["properties"]["name"].removeprefix("Mercatò").strip(" -")
                item["name"] = "Mercatò"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif location["properties"]["storeType"] == "mercato-big":
                item["branch"] = location["properties"]["name"].removeprefix("Mercatò Big").strip(" -")
                item["name"] = "Mercatò Big"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif location["properties"]["storeType"] == "mercato-local":
                item["branch"] = location["properties"]["name"].removeprefix("Mercatò Local").strip(" -")
                item["name"] = "Mercatò Local"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif location["properties"]["storeType"] == "mercatoextra":
                item["branch"] = location["properties"]["name"].removeprefix("Mercatò Extra").strip(" -")
                item["name"] = "Mercatò Extra"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                self.logger.error("Unexpected type: {}".format(location["properties"]["storeType"]))

            yield item
