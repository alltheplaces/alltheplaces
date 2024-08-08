import re
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Access, Categories, Extras, Fuel, FuelCards, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES
from locations.structured_data_spider import extract_phone

FUELS_AND_SERVICES_MAPPING = {
    # Fuels
    "AdBluePompa": Fuel.ADBLUE,
    "Diesel": Fuel.DIESEL,
    "DieselGold": Fuel.DIESEL,
    "DieselONTIR": Fuel.DIESEL,
    "Benzyna98": Fuel.OCTANE_98,
    "Benzyna95": Fuel.OCTANE_95,
    "LPG": Fuel.LPG,
    # Services
    "Gastro": Extras.FAST_FOOD,
    "HS": Access.HGV,
    "Myjnia": Extras.CAR_WASH,
    "Myjniatir": Extras.CAR_WASH,
    "Wjazdtir": Access.HGV,
    "Parkingtir": Access.HGV,
    # Fuel cards
    "Eurowag": FuelCards.EUROWAG,
    "Dkv": FuelCards.DKV,
    "Uta": FuelCards.UTA,
    "Aviacard": FuelCards.AVIA,
    "e100": FuelCards.E100,
}


class AviaPLSpider(Spider):
    name = "avia_pl"
    item_attributes = AVIA_SHARED_ATTRIBUTES
    start_urls = ["https://aviastacjapaliw.pl/mapa-2/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for lat, lon, name, html_blob in re.findall(
            r"\[{ lat: (-?\d+\.\d+), ?lng:\s+(-?\d+\.\d+)\s+}, \"(.+?)\", \"(.+?)\"],", response.text
        ):
            item = Feature()
            item["lat"] = lat
            item["lon"] = lon
            item["branch"] = name.removeprefix("AVIA ")

            sel = Selector(text=html_blob)
            item["ref"] = item["website"] = sel.xpath("//a/@href").get().strip('\\"')
            item["addr_full"] = merge_address_lines(sel.xpath('//div[@class="content"]/text()').getall())
            extract_phone(item, sel)

            for key, tag in FUELS_AND_SERVICES_MAPPING.items():
                if sel.xpath(f'//div[contains(text(), "+{key}+")]').get():
                    apply_yes_no(tag, item, True)

            if sel.xpath('//div[contains(text(), "+h24+")]').get():
                item["opening_hours"] = "24/7"

            apply_category(Categories.FUEL_STATION, item)

            yield item
