import json
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature, set_lat_lon
from locations.licenses import Licenses


class GovSaluteParafarmacieITSpider(Spider):
    name = "gov_salute_parafarmacie_it"
    # Source: https://www.dati.salute.gov.it/it/dataset/parafarmacie/
    start_urls = ["https://www.dati.salute.gov.it/it/dataset/parafarmacie/"]
    dataset_attributes = Licenses.IT_IODL2.value | {
        "attribution:name": "Ministero della Salute",
        "attribution:website": "https://www.dati.salute.gov.it/it/dataset/parafarmacie/",
        "use:openstreetmap": "yes",
    }

    def parse(self, response: Response) -> Iterable:
        url = response.xpath('//a[contains(@href, "FRM_PFARMA") and contains(@href, ".json")]/@href').get()
        if url:
            yield response.follow(url, callback=self.parse_data)

    def parse_data(self, response: Response) -> Iterable[Feature]:
        for record in json.loads(response.text):
            if record.get("data_fine_validita", "-") != "-":
                continue

            item = Feature()
            item["ref"] = record["codice_identificativo_sito"]
            item["name"] = record["sito_logistico"]
            item["street_address"] = record["indirizzo"]
            item["city"] = record["comune"]
            item["postcode"] = record["cap"]
            item["state"] = record["regione"].title()

            if vat := record.get("partita_iva", "").strip():
                item["extras"]["ref:vatin"] = "IT" + vat.zfill(11)

            lat_raw = record.get("latitudine", "-")
            lon_raw = record.get("longitudine", "-")
            if lat_raw != "-" and lon_raw != "-":
                try:
                    set_lat_lon(item, float(lat_raw.replace(",", ".")), float(lon_raw.replace(",", ".")))
                except ValueError:
                    pass

            apply_category(Categories.PHARMACY, item)
            item["extras"]["dispensing"] = "no"

            yield item
