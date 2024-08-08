import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingMXSpider(Spider):
    name = "burger_king_mx"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://api-lac.menu.app/api/venues?per_page=1000&include=brand_id,address,city,code,latitude,longitude,name,phone,state,zip,available_payment_methods,country,serving_times|type_id;reference_type;date;date_to;days;time_from;time_to;working",
            headers={"Application": "4160ef94dff50c0ea5067b489653eae0"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        venues = response.json()["data"]["venues"]
        for location in venues:
            if (
                "(DUPLICATED)" in location["name"]
                or "(DELETE)" in location["name"]
                or "(Delete)" in location["name"]
                or "(Disabled)" in location["name"]
                or "*PERM. CLOSED*" in location["name"]
            ):
                continue

            item = DictParser.parse(location)
            item["state"] = None
            item["branch"] = item.pop("name")

            item["website"] = "https://www.burgerking.com.mx/restaurantes/{}/?id={}".format(
                self.slugify(location["address"]), location["id"]
            )

            item["opening_hours"] = OpeningHours()
            for rule in location["serving_times"]:
                if rule["type_id"] != 2:
                    continue
                for day in rule["days"]:
                    item["opening_hours"].add_range(DAYS[day - 1], rule["time_from"], rule["time_to"])

            yield item

    def slugify(self, s: str) -> str:
        s = re.sub(r"\s+", "-", s.lower())
        for a, b in zip(
            "àáâäæãåāăąçćčđďèéêëēėęěğǵḧîïíīįìłḿñńǹňôöòóœøōõőṕŕřßśšşșťțûüùúūǘůűųẃẍÿýžźż·/_,:;",
            "aaaaaaaaaacccddeeeeeeeegghiiiiiilmnnnnoooooooooprrsssssttuuuuuuuuuwxyyzzz------",
        ):
            s = s.replace(a, b)
        return re.sub(r"\-\-+", "-", re.sub(r"[^\w\-]+", "", s.replace("&", "-and-"))).strip("-")
