import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingITSpider(scrapy.Spider):
    name = "burger_king_it"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.it/trova-un-ristorante"]
    custom_settings = {"METAREFRESH_ENABLED": False, "ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        blob = response.xpath('//script[contains(text(), "dati_pagina")]/text()').re_first(r"JSON.parse\('(.+)'\);")
        data = json.loads(bytes(blob, "utf-8").decode("unicode_escape"))

        for store in data["stores"]:
            if not store["storeId"]:
                continue
            item = DictParser.parse(store)
            item["ref"] = store["storeId"]
            item["branch"] = item.pop("name")
            item["addr_full"] = store["address"]
            item["city"] = store["name"]
            item["country"] = "IT"

            apply_yes_no(Extras.DELIVERY, item, "HomeDelivery" in store["servizi"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, "KingDrive" in store["servizi"])
            apply_yes_no(Extras.WIFI, item, "WIFI" in store["servizi"])

            item["opening_hours"] = OpeningHours()
            for day_name, hours in (store["orari"] or {}).get("ristorante", {}).items():
                if hours["lunch_end"] and hours["dinner_start"]:
                    item["opening_hours"].add_range(DAYS_IT[day_name.title()], hours["lunch_start"], hours["lunch_end"])
                    item["opening_hours"].add_range(
                        DAYS_IT[day_name.title()], hours["dinner_start"], hours["dinner_end"]
                    )
                else:
                    item["opening_hours"].add_range(
                        DAYS_IT[day_name.title()], hours["lunch_start"], hours["dinner_end"]
                    )

            yield item
