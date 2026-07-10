import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class BnlITSpider(Spider):
    name = "bnl_it"
    item_attributes = {"brand": "BNL", "brand_wikidata": "Q2201225"}

    # The locator returns only the 96 points nearest a bounding box's centre, so Italy's extent is searched
    # recursively: any bbox that hits the cap is split into quadrants (DuplicatesPipeline drops overlaps by ref).
    max_results = 96

    def bbox_request(self, lat1: float, lat2: float, lon1: float, lon2: float) -> JsonRequest:
        return JsonRequest(
            url="https://bnl.it/digitaldashboardConfiguration/locator/trovaAgenzie",
            data={
                "header": {
                    "distributorId": "BNL",
                    "callingApplication": "BNL-WEB",
                    "callingApplicationVersion": "6.9.999",
                    "language": "it",
                    "country": "IT",
                },
                "body": {
                    "tipoServ": "0",
                    "progr": 0,
                    "visibInfo": 1,
                    "listaPag": 5000,
                    "coordXMin": str(lon1).replace(".", ","),  # the API expects comma decimals
                    "coordXMax": str(lon2).replace(".", ","),
                    "coordYMin": str(lat1).replace(".", ","),
                    "coordYMax": str(lat2).replace(".", ","),
                    "atmEsterno": True,
                },
            },
            cb_kwargs={"bbox": (lat1, lat2, lon1, lon2)},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.bbox_request(35.0, 47.5, 6.0, 19.0)  # Italy mainland + islands

    def parse(self, response: Response, bbox: tuple[float, float, float, float], **kwargs: Any) -> Any:
        locations = response.json()["body"]["datiServs"]

        if len(locations) >= self.max_results:  # cap hit: subdivide into quadrants; the leaf cells return the points
            lat1, lat2, lon1, lon2 = bbox
            lat_mid, lon_mid = (lat1 + lat2) / 2, (lon1 + lon2) / 2
            yield self.bbox_request(lat1, lat_mid, lon1, lon_mid)
            yield self.bbox_request(lat1, lat_mid, lon_mid, lon2)
            yield self.bbox_request(lat_mid, lat2, lon1, lon_mid)
            yield self.bbox_request(lat_mid, lat2, lon_mid, lon2)
            return

        for poi in locations:
            is_branch = poi.get("iwFFiliale") == "1"
            is_atm = poi.get("iwFBancomat") == "1"
            if not (is_branch or is_atm):
                continue
            # Every field uses a bank-specific "iw..." key that DictParser cannot map, so build directly.
            item = Feature(
                ref=poi["iwCProgr"],
                name=self.clean_label(poi.get("iwDsOnline")),
                street_address=poi.get("iwIndirizzo"),
                city=poi.get("iwCitta"),
                state=poi.get("iwProvincia"),
                postcode=poi.get("iwCap"),
                lat=(poi.get("iwCoordY") or "").replace(",", "."),
                lon=(poi.get("iwCoordX") or "").replace(",", "."),
            )
            if is_branch:
                item["branch"] = item.pop("name")
                apply_yes_no(Extras.ATM, item, int(poi.get("iwNumAtm") or 0) > 0)
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)
            yield item

    @staticmethod
    def clean_label(label: str | None) -> str | None:
        # Labels are prefixed with the unit type (e.g. "AG." Agenzia, "SP." Sportello, "FIL." Filiale) and
        # sometimes the "DI" (of) connector; drop those and collapse padding, keeping the real location label.
        label = re.sub(r"^(?:AG|SP|FIL|AGENZIA)\.?\s*(?:DI\s+)?", "", label or "")
        label = re.sub(r"\s{2,}", " ", label).strip()
        # A few records carry only the bare brand as their label; drop it so NSI supplies the brand name.
        return None if label.upper() == "BNL" else (label or None)
