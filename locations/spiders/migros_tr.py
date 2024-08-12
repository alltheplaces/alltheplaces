import json
from typing import Iterable

import scrapy

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class MigrosTRSpider(scrapy.Spider):
    name = "migros_tr"
    start_urls = ["https://www.migros.com.tr/rest/api/external-warehouses"]
    item_attributes = {"brand": "Migros", "brand_wikidata": "Q1754510"}

    def start_requests(self) -> Iterable[scrapy.Request]:
        # geonamescache does not a list of only provinces in Turkey
        # it only has a list of cities (which can be provinces (il) or districts (ilçe))
        # so we have to manually create a list of provinces
        provinces = [
            "Adana",
            "Adıyaman",
            "Afyon",
            "Ağrı",
            "Amasya",
            "Ankara",
            "Antalya",
            "Artvin",
            "Aydın",
            "Balıkesir",
            "Bilecik",
            "Bingöl",
            "Bitlis",
            "Bolu",
            "Burdur",
            "Bursa",
            "Çanakkale",
            "Çankırı",
            "Çorum",
            "Denizli",
            "Diyarbakır",
            "Edirne",
            "Elazığ",
            "Erzincan",
            "Erzurum",
            "Eskişehir",
            "Gaziantep",
            "Giresun",
            "Gümüşhane",
            "Hakkâri",
            "Hatay",
            "Isparta",
            "Mersin",
            "İstanbul",
            "İzmir",
            "Kars",
            "Kastamonu",
            "Kayseri",
            "Kırklareli",
            "Kırşehir",
            "Kocaeli",
            "Konya",
            "Kütahya",
            "Malatya",
            "Manisa",
            "Kahramanmaraş",
            "Mardin",
            "Muğla",
            "Muş",
            "Nevşehir",
            "Niğde",
            "Ordu",
            "Rize",
            "Sakarya",
            "Samsun",
            "Siirt",
            "Sinop",
            "Sivas",
            "Tekirdağ",
            "Tokat",
            "Trabzon",
            "Tunceli",
            "Şanlıurfa",
            "Uşak",
            "Van",
            "Yozgat",
            "Zonguldak",
            "Aksaray",
            "Bayburt",
            "Karaman",
            "Kırıkkale",
            "Batman",
            "Şırnak",
            "Bartın",
            "Ardahan",
            "Iğdır",
            "Yalova",
            "Karabük",
            "Kilis",
            "Osmaniye",
            "Düzce",
        ]

        for province in provinces:
            yield scrapy.Request(
                method="POST",
                url=self.start_urls[0],
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                body=json.dumps({"cityName": province}),
                callback=self.parse,
            )

    def parse(self, response):
        for store in response.json()["data"]:
            item = DictParser.parse(store)

            if "MJET" in store["name"]:
                item["name"] = "Migros Jet"
                item["branch"] = store["name"].replace("MJET", "").strip()
            else:
                item["name"] = "Migros"
                item["branch"] = store["name"].replace("MIGROS", "").replace("MİGROS", "").strip()

            item["city"] = store["townName"]
            item["state"] = store["cityName"]
            item["street_address"] = store["addressDetail"]
            item["addr_full"] = clean_address([store["addressDetail"], store["townName"], store["cityName"]])
            item["phone"] = store.get("fixedPhoneNumber")

            yield item
