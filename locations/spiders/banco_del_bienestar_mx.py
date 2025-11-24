from typing import Any

import scrapy
from scrapy import FormRequest
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BancoDelBienestarMXSpider(scrapy.Spider):
    name = "banco_del_bienestar_mx"
    item_attributes = {
        "brand": "Banco del Bienestar",
        "brand_wikidata": "Q5719137",
    }
    start_urls = ["https://directoriodesucursales.bancodelbienestar.gob.mx"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for state_info in response.xpath('//select[@id="bandas"]/option'):
            if state_id := state_info.xpath("./@value").get(""):
                yield FormRequest(
                    url="https://directoriodesucursales.bancodelbienestar.gob.mx/home.php",
                    formdata={"entidadtxt": state_id},
                    callback=self.parse_locations,
                    cb_kwargs={"state": state_info.xpath("./text()").get("")},
                )

    def parse_locations(self, response: Response, state: str) -> Any:
        for location in response.xpath('//*[@class="card hsucursal"]'):
            item = Feature()
            item["state"] = state
            item["ref"] = item["branch"] = location.xpath('.//*[@class="card-title"]/text()').get("").strip()
            item["addr_full"] = clean_address(location.xpath('.//p[@class="card-text"]/text()').getall())
            if map_url := location.xpath('.//a[contains(@href, "maps")]/@href').get():
                item["lat"], item["lon"] = url_to_coords(map_url)
            apply_category(Categories.BANK, item)
            yield item
