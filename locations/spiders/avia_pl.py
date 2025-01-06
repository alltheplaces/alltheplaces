import re
from typing import Any, Iterable

import scrapy
from scrapy import Selector, Spider, Request
from scrapy.http import Response

from locations.categories import Access, Categories, Extras, Fuel, FuelCards, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES
from locations.structured_data_spider import extract_phone



class AviaPLSpider(Spider):
    name = "avia_pl"
    item_attributes = AVIA_SHARED_ATTRIBUTES
    start_urls = ["https://aviastacjapaliw.pl/mapa-2/"]

    def start_requests(self) -> Iterable[Request]:
        yield scrapy.Request(url="https://api.mapa.aviapolska.pl/api/stations?populate=logo,address,coordinates,features.fuels,features.cards,features",
                             headers={'Authorization': 'Bearer 6ced00ac9d9a1dcbab299c63f634b1251fd2f99365e59ccc31bf82a4951e15ed679837128fa6e19774b2dee1d2baaa0ffc777cd798d46671d5ea4fbfb2234eb73ba99d66a96636ffaef5d75ee8cebf2803d2a6a24608f222793c4433277ebe83c212268881318437bfdeefac3f37dba695d6a57c814233a6f6ba043ec1481316'},
                             callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for station in response.json()["data"]:
            station.update(station.pop("attributes"))
            item = DictParser.parse(station)
            if item["lat"][-2] ==",":
                item["lat"] = ".".join([item["lat"][0:2],item["lat"][2:].replace(",","")])
            if item["lon"][-2] ==".":
                item["lon"] = ".".join([item["lon"][0:2],item["lon"][2:].replace(".","")])
            apply_category(Categories.FUEL_STATION, item)

            yield item
