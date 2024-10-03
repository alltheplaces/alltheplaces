from scrapy.http import JsonRequest

from locations.geo import city_locations
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingPESpider(JSONBlobSpider):
    name = "burger_king_pe"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.burgerking.pe/Geolocalizacion/ObtenerTiendasPickupCoordenada"]
    # no_refs = True

    def start_requests(self):
        for city in city_locations("PE"):
            yield JsonRequest(
                url=self.start_urls[0],
                data={
                    "DireccionCliente": {
                        "Direccion": "",
                        "NroMz": "",
                        "Distrito": "",
                        "Latitud": city["latitude"],
                        "Longitud": city["longitude"],
                    }
                },
            )

    def extract_json(self, response):
        # Dict with error message is returned on no results, otherwise a list of results is returned
        if isinstance(response.json(), dict):
            return []
        else:
            return response.json()

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("addr_full")
        yield item
