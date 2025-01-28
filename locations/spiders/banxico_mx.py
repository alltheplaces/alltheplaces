import io
import zipfile
from typing import Any, Iterable

from scrapy import FormRequest, Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

"""
Banco de México (Banxico) : Q806208
The Bank of Mexico (Spanish: Banco de México), abbreviated BdeM or Banxico, is Mexico's central bank, monetary authority and lender of last resort.
https://en.wikipedia.org/wiki/Bank_of_Mexico
"""


class BanxicoMXSpider(Spider):
    name = "banxico_mx"
    BRANDS_MAPPING = {
        "37166": ("Banco del Bienestar", "Q5719137"),
        "40014": ("Santander", "Q8965165"),
        "40127": ("Banco Azteca", "Q4854076"),
        "40137": ("BanCoppel", "Q126192396"),
        "37019": ("Banjercito", "Q24655074"),
        "40030": ("BanBajío", "Q5718183"),
        "40002": ("Banamex", "Q2646652"),
        "40072": ("Banorte", "Q806914"),
        "40012": ("BBVA", "Q2876794"),
        "40021": ("HSBC", "Q5635881"),
        "40130": ("Compartamos Banco ICR", "Q2990370"),
        "40036": ("ICR Inbursa", "Q731123"),
        "40044": ("Scotiabank", "Q451476"),
        "40136": ("Intercam Banco", "Q30915645"),
        "40143": ("CIBanco", "Q126539570"),
        "40058": ("BanRegio", "Q4853573"),
        "40132": ("Banco Multiva", "Q2885364"),
        "40106": ("Bank of America", "Q487907"),
        "40042": ("Banca Mifel", "Q5717818"),
        "40062": ("Afirme", "Q60825526"),
        "40060": ("Bansí", "Q5719140"),
        "40133": ("Actinver", None),
        "40128": ("Autofin", None),
        "40037": ("Interacciones", None),
        "40140": ("Consubanco", None),
    }

    def start_requests(self) -> Iterable[Request]:
        yield Request(url="https://www.banxico.org.mx/canje-efectivo/web/ubica-cc")  # branches
        yield Request(
            url="https://www.banxico.org.mx/services/ubicajeros-banxico-mobile-app.html", callback=self.parse_atms
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for state_id in response.xpath('//select[@id="listaEntidadFederativa"]//option/@value').getall():
            yield JsonRequest(
                url=f"https://www.banxico.org.mx/canje-efectivo/web/municipios-de-estado?idEstado={state_id}",
                callback=self.parse_municipalities,
                cb_kwargs=dict(state_id=state_id),
            )

    def parse_municipalities(self, response: Response, state_id: str) -> Any:
        for municipality in response.json():
            yield FormRequest(
                url="https://www.banxico.org.mx/canje-efectivo/web/busca-cc",
                formdata={"estado": state_id, "municipio": municipality["id"], "codigoPostal": "0"},
                callback=self.parse_locations,
                cb_kwargs=dict(city=municipality["nombre"]),
            )

    def parse_locations(self, response: Response, city: str) -> Any:
        for location in response.json():
            location_details = location["domicilio"]
            item = Feature()
            item["ref"] = str(location["id"]) + "-" + location_details["codigoPostal"]
            item["branch"] = location["nombre"]
            item["lat"] = location_details["ubicacion"]["latitud"]
            item["lon"] = location_details["ubicacion"]["longitud"]
            item["housenumber"] = location_details["numeroExterior"].replace("SN", "")
            item["street"] = location_details["calle"]
            item["city"] = city
            item["postcode"] = location_details["codigoPostal"]
            item["state"] = location_details["estado"]["nombre"]
            if brand_info := self.BRANDS_MAPPING.get(location["institucion"]["insititucion"].removeprefix("0")):
                item["brand"], item["brand_wikidata"] = brand_info
            apply_category(Categories.BANK, item)
            yield item

    def parse_atms(self, response: Response, **kwargs: Any) -> Any:
        # Access zip file containing ATM details
        yield response.follow(
            url=response.xpath('//a[contains(@href,".zip")]/@href').get(""), callback=self.parse_atm_details
        )

    def parse_atm_details(self, response: Response, **kwargs: Any) -> Any:
        with zipfile.ZipFile(io.BytesIO(response.body)) as feed_zip:
            for file_name in feed_zip.namelist():
                if file_name.endswith(".txt"):
                    with feed_zip.open(file_name) as file:
                        for line in file.read().decode("utf-8").splitlines():
                            # Refer https://www.banxico.org.mx/servicios/d/%7BD18A66F7-26AF-4BA0-C215-83531E401657%7D.pdf
                            # for fields description
                            location_info = line.split("|")
                            item = Feature()
                            bank_id = location_info[0]
                            item["ref"] = bank_id + "-" + location_info[1]
                            item["addr_full"], item["postcode"], item["lat"], item["lon"] = location_info[2:6]
                            # location_info[7] : opening_hours don't look reliable, hence ignored.
                            if brand_info := self.BRANDS_MAPPING.get(bank_id.removeprefix("0")):
                                item["brand"], item["brand_wikidata"] = brand_info
                            apply_category(Categories.ATM, item)
                            yield item
