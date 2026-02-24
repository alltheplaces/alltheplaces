from typing import Any

import scrapy
from requests import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class KutxabankESSpider(scrapy.Spider):
    name = "kutxabank_es"
    item_attributes = {"brand": "Kutxabank", "brand_wikidata": "Q5139377"}
    start_urls = [
        "https://portal.kutxabank.es/cs/jsp/oficinascajeros/buscaroficinascajeros.jsp?idioma=03&entidad=2095&tipo=2&longMax=180&longMin=-180&latMax=90&latMin=-90&zoom=13",
        "https://portal.kutxabank.es/cs/jsp/oficinascajeros/buscaroficinascajeros.jsp?idioma=03&entidad=2095&tipo=1&servicios=todos&longMax=180&longMin=-180&latMax=90&latMin=-90&zoom=14",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for bank in response.xpath("//centro"):
            item = Feature()
            item["branch"] = bank.xpath(".//nombre/text()").get()
            item["street_address"] = bank.xpath("./direccion/text()").get()
            item["postcode"] = bank.xpath("./codigoPostal/text()").get()
            item["city"] = bank.xpath("./municipio/text()").get()
            item["state"] = bank.xpath("./provincia/text()").get()
            item["phone"] = bank.xpath("./telefono/text()").get()
            item["lat"] = bank.xpath("./localizacion/@latitude").get()
            item["lon"] = bank.xpath("./localizacion/@longitude").get()
            item["website"] = "https://portal.kutxabank.es/"
            if "cajero" in bank.xpath("./@tipo").get():
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
            yield item
