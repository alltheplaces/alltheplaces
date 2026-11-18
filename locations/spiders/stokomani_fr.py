import re
import unicodedata
from typing import Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class StokomaniFRSpider(Spider):
    name = "stokomani_fr"
    item_attributes = {"brand": "Stokomani", "brand_wikidata": "Q22249328"}
    start_urls = ["https://shops.stkmn.tech/get.php"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for store in response.json():
            address = store.pop("address")
            item = DictParser.parse(address)
            item["ref"] = store["id_interne"]
            item["lat"] = address["coor_1"]
            item["lon"] = address["coor_2"]
            item["street_address"] = ", ".join(filter(None, [address["address1"], address["address2"]]))
            item["branch"] = " ".join(store["name"].removeprefix("STOKOMANI").split())
            item["website"] = "https://www.stokomani.fr/pages/boutique-stokomani-{}-{}".format(
                self.slugify(address["city"]), address["zip"]
            )

            item["opening_hours"] = OpeningHours()
            for day_fr, day in DAYS_FR.items():
                key = f"magasin_{day_fr.lower()}"
                if f"{key}_am_start" not in store:
                    continue
                times = [store[f"{key}_{part}"] for part in ("am_start", "am_stop", "pm_start", "pm_stop")]
                if not any(times):
                    item["opening_hours"].set_closed(day)
                elif times[1] and times[2]:
                    item["opening_hours"].add_range(day, times[0], times[1])
                    item["opening_hours"].add_range(day, times[2], times[3])
                else:
                    item["opening_hours"].add_range(day, times[0], times[3])

            yield item

    @staticmethod
    def slugify(city: str) -> str:
        # Matches the store page handles in the sitemap, e.g. "SAINT-OUEN-L'AUMONE" -> "saint-ouen-l-aumone".
        city = unicodedata.normalize("NFD", city.lower())
        city = re.sub(r"[̀-ͯ]", "", city)
        city = re.sub(r"[^a-z0-9]+", "-", city)
        return city.strip("-")
