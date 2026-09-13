import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES

FORMATS = {
    "EUROSPAR": ("Eurospar", Categories.SHOP_SUPERMARKET),
    "SPAR EXPRESS": ("Spar Express", Categories.SHOP_CONVENIENCE),
    "SPAR mini": ("Spar Mini", Categories.SHOP_CONVENIENCE),
    "SPAR": ("Spar", Categories.SHOP_CONVENIENCE),
}

DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class SparPLSpider(Spider):
    name = "spar_pl"
    item_attributes = SPAR_SHARED_ATTRIBUTES

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://spar.pl/nasze-sklepy/", callback=self.parse_nonce)

    def parse_nonce(self, response: Response, **kwargs: Any) -> Any:
        nonce = re.search(r'"nonce":"([0-9a-f]+)"', response.text).group(1)
        self.seen_ids = set()
        for lat, lon in country_iseadgg_centroids("PL", 48):
            yield FormRequest(
                url="https://spar.pl/wp-admin/admin-ajax.php",
                formdata={
                    "action": "storemap_search",
                    "nonce": nonce,
                    "lat": str(lat),
                    "lng": str(lon),
                    "radius": "50",
                },
                callback=self.parse,
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for shop in response.json()["data"]["stores"]:
            if shop["id"] in self.seen_ids:
                continue
            self.seen_ids.add(shop["id"])

            item = DictParser.parse(shop)
            item["country"] = "PL"
            item["website"] = f'https://spar.pl/sklep/{shop["post_name"]}/'

            item["opening_hours"] = OpeningHours()
            for day, key in zip(DAYS, DAY_KEYS):
                hours = shop.get(key, "").strip()
                if not hours:
                    continue
                if hours.lower() == "nieczynne":
                    item["opening_hours"].set_closed(day)
                    continue
                if hours.upper() == "24H":
                    item["opening_hours"].add_range(day, "00:00", "23:59")
                    continue
                open_time, close_time = hours.replace("–", "-").replace("—", "-").split("-")
                item["opening_hours"].add_range(day, open_time.strip(), close_time.strip())

            if fmt := FORMATS.get(shop["format"]):
                name, category = fmt
                item["name"] = name
                apply_category(category, item)
            else:
                self.crawler.stats.inc_value(f'atp/{self.name}/unknown_format/{shop["format"]}')

            yield item
