from typing import Any, AsyncIterator

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class GuyHoquetSpider(Spider):
    name = "guy_hoquet"
    item_attributes = {"brand": "Guy Hoquet", "brand_wikidata": "Q25383970", "name": "Guy Hoquet"}

    async def start(self) -> AsyncIterator[Request]:
        yield FormRequest("https://agence.guy-hoquet.com/markers.php", formdata={})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Only a coordinate search returns opening hours, so search at each marker and keep the agency found there
        for marker in response.json():
            yield FormRequest(
                "https://agence.guy-hoquet.com/agencies.php",
                formdata={"latitude": marker["latitude"], "longitude": marker["longitude"]},
                callback=self.parse_agencies,
                cb_kwargs={"code": marker["code"]},
                dont_filter=True,
            )

    def parse_agencies(self, response: Response, code: str) -> Any:
        for agency in response.json():
            # DATA VERIF is an internal head office record, not an agency
            if agency["code"] != code or agency["nom"] == "DATA VERIF":
                continue
            item = DictParser.parse(agency)
            item["ref"] = code
            item["branch"] = agency["nom"]
            item["addr_full"] = agency["adresse"]

            if agency["horaire"]:
                item["opening_hours"] = OpeningHours()
                for day, times in agency["horaire"].items():
                    day = DAYS[int(day) - 1]
                    item["opening_hours"].add_range(day, times.get("am_open"), times.get("am_close"))
                    item["opening_hours"].add_range(day, times.get("pm_open"), times.get("pm_close"))
                    # The store locator shows am_open to pm_close as one session when the lunch break is absent
                    if not times.get("am_close") and not times.get("pm_open"):
                        item["opening_hours"].add_range(day, times.get("am_open"), times.get("pm_close"))

            apply_category(Categories.OFFICE_ESTATE_AGENT, item)
            yield item
