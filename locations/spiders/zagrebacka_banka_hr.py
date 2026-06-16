from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours


class ZagrebackaBankaHRSpider(Spider):
    name = "zagrebacka_banka_hr"
    item_attributes = {"brand": "Zagrebačka banka", "brand_wikidata": "Q140381"}

    # The endpoint returns the POIs nearest to a query point, distance-limited,
    # so a grid of points covering Croatia (overlapping reach) is queried and the
    # pipeline deduplicates by ref. "vrstaPoi" lists the categories to fully
    # enumerate; it must include BOTH "Poslovnica" (branches) and "Bankomat"
    # (ATMs), otherwise the omitted category is only returned as sparse nearby
    # context rather than exhaustively. Note the payload swaps the usual order:
    # "lb" carries latitude and "mb" longitude. The "vrsta*" arrays select
    # function sub-types within each category:
    #   vrstaPoslovnice: 2=retail branch, 3=branch, 4=business centre
    #   vrstaBankomata:  0=withdrawal ATM, 1=deposit/withdrawal ATM
    async def start(self) -> AsyncIterator[Any]:
        for lat, lon in point_locations("eu_centroids_40km_radius_country.csv", "HR"):
            yield JsonRequest(
                url="https://www.zaba.hr/home/mapa/nbLokacija",
                data={
                    "lb": lat,
                    "mb": lon,
                    "filter": {
                        "broj": 99999,
                        "vrstaPoslovnice": [2, 3, 4],
                        "vrstaBankomata": [0, 1],
                        "vrstaPoi": ["Poslovnica", "Bankomat"],
                    },
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for cluster in response.json()["obj"]:
            for poi in cluster.get("pois", []):
                if not poi["idZupanija"]:
                    continue  # foreign UniCredit-group POIs carry no Croatian county id

                if poi["vrsta"] == "Poslovnica":
                    category = Categories.BANK
                elif poi["vrsta"] == "Bankomat":
                    category = Categories.ATM
                elif poi["vrsta"] in ("DNT", "Uređaj za zaprimanje naloga", "Uređaj za deponiranje kovanica"):
                    continue  # day/night safes, order-intake and coin-deposit devices, not mapped
                else:
                    self.logger.error("Unexpected vrsta: {}".format(poi["vrsta"]))
                    continue

                item = DictParser.parse(poi)
                # Croatian API keys: DictParser only maps ref/lat, rest set manually.
                item["lon"] = poi["geolon"]
                item["street_address"] = poi.get("adresa")
                item["city"] = poi.get("grad")
                item["postcode"] = str(poi["postanskiBroj"]) if poi.get("postanskiBroj") else None
                item["phone"] = poi.get("telefon")

                if poi["vrsta"] == "Poslovnica":
                    self.parse_hours(item, poi.get("radnoVrijeme"))

                apply_category(category, item)
                yield item

    def parse_hours(self, item: dict, rules: list[dict] | None) -> None:
        if not rules:
            return
        oh = OpeningHours()
        try:
            for rule in rules:
                day = DAYS[rule["dan"]]
                if rule["t1h"] or rule["t1m"]:
                    oh.add_range(day, f"{rule['f1h']:02d}:{rule['f1m']:02d}", f"{rule['t1h']:02d}:{rule['t1m']:02d}")
                if rule["t2h"] or rule["t2m"]:
                    oh.add_range(day, f"{rule['f2h']:02d}:{rule['f2m']:02d}", f"{rule['t2h']:02d}:{rule['t2m']:02d}")
            item["opening_hours"] = oh
        except Exception:  # TODO: revisit if hours parsing proves unreliable
            self.logger.warning("Failed to parse hours for {}".format(item.get("ref")))
