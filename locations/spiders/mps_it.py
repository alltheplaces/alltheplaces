from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import city_locations
from locations.items import Feature


class MpsITSpider(Spider):
    name = "mps_it"
    item_attributes = {"brand": "Monte dei Paschi di Siena", "brand_wikidata": "Q46730"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("IT"):
            yield JsonRequest(
                url=f'https://appx.mps.it/VWRestServices/client/public/filiale/elenco?elemPag=999&ckF=true&ckB=true&pk=1&lat={city["latitude"]}&lon={city["longitude"]}&output=json',
                callback=self.parse,
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for bank in response.json()["listaFiliali"]:
            item = Feature()
            item["street_address"] = bank["indirizzo"]
            item["postcode"] = bank["cap"]
            item["city"] = bank["comune"]
            item["state"] = bank["provincia"]
            item["lat"] = bank["latitudine"]
            item["lon"] = bank["longitudine"]
            item["ref"] = bank["entitaBanca"][-1]["codiceFiliale"]
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, True)
            yield item
