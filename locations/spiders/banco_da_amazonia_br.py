from typing import Any

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class BancoDaAmazoniaBRSpider(Spider):
    name = "banco_da_amazonia_br"
    item_attributes = {"brand": "Banco da Amazônia", "brand_wikidata": "Q16496429"}
    start_urls = ["https://www.bancoamazonia.com.br/o-banco/agencias"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 300}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for state, city_locations in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var dadosEstados")]/text()').get()
        ).items():
            for city_location in city_locations:
                item = Feature()
                item["state"] = state
                # city_location["municipio"] info is not reliable, lots of duplicate location details occur under different cities of the same state
                if isinstance(city_location["endereco"], str):
                    city_location["endereco"] = [city_location["endereco"]]
                for location in city_location["endereco"]:
                    location_html = Selector(text=location)
                    item["ref"] = item["branch"] = (
                        location_html.xpath(".//strong/text()").get("").removeprefix("AGÊNCIA ")
                    )
                    if address_contact_info := location_html.xpath(".//body/text()").getall():
                        item["street_address"] = address_contact_info[0]
                        if len(address_contact_info) > 1:
                            for info_text in address_contact_info[1:]:
                                if info_text.strip().startswith("CEP"):
                                    item["postcode"] = (
                                        info_text.removeprefix("CEP").replace(".", "").replace(":", "").strip()
                                    )
                                elif "CONTATO:" in info_text.strip():
                                    item["phone"] = self.parse_phone(
                                        info_text.removeprefix("CONTATO:").split("(FAX)")[0]
                                    )
                    else:  # skip invalid html
                        continue

                    apply_category(Categories.BANK, item)
                    yield item

    def parse_phone(self, phone_text: str) -> str:
        if "/" not in phone_text:
            return phone_text
        else:
            phones = ""
            base_digits = phone_text.split("-", maxsplit=1)[0]
            phones += phone_text.split("/")[0].strip()
            for phone in phone_text.split("/")[1:]:
                if "-" in phone:
                    phones = phones + ";" + phone.strip()
                else:
                    phones = phones + ";" + base_digits + "-" + phone.strip()
            return phones
