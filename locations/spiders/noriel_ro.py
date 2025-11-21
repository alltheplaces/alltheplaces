from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.items import Feature


class NorielROSpider(Spider):
    name = "noriel_ro"
    item_attributes = {"brand": "Noriel", "brand_wikidata": "Q18544426"}
    no_refs = True

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://noriel.ro/noriel_stores/filter/products/",
            formdata={"selected_products[]": ["Jucarii", "Bebelusi", "Fashion"]},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            item = Feature()
            item["name"] = location["title"]
            item["phone"] = location["telephone"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["street_address"] = location["address"]
            item["city"] = location["city"]
            item["email"] = location["email"]
            yield item
