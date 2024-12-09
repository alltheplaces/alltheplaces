from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_ID, OpeningHours
from locations.items import Feature


class PosIndonesiaIDSpider(Spider):
    name = "pos_indonesia_id"
    item_attributes = {"operator": "Pos Indonesia", "operator_wikidata": "Q4273095"}
    handle_httpstatus_list = [400]

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://postoffice.posindonesia.co.id/backend/externalweb/carikantor",
            data={"perPage": 20000, "currentPage": 1, "cari": "", "jnsktr": ""},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("data", []):
            location_type = location["jnskantor"]
            if location_type.startswith("Agen"):  # Agency locations without coordinates
                continue
            item = Feature()
            item["ref"] = location["id_dirian"]
            item["branch"] = location["nama_dirian"]
            item["city"] = location["kabupaten"].removeprefix("KOTA ")
            if item["city"].startswith("KAB."):
                item["state"] = item.pop("city").removeprefix("KAB. ")
            if location_type == "MR":
                apply_category({"amenity": "mailroom"}, item)
            else:
                apply_category(Categories.POST_OFFICE, item)
            yield JsonRequest(
                url="https://postoffice.posindonesia.co.id/backend/externalweb/detailktr",
                data={"id_dirian": item["ref"]},
                callback=self.parse_details,
                cb_kwargs=dict(item=item),
            )

    def parse_details(self, response: Response, item: Feature) -> Iterable[Feature]:
        location = response.json()["data"][0]
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        item["street_address"] = location["alamat"]
        item["phone"] = location["telpon_old"]
        item["website"] = "https://postoffice.posindonesia.co.id/"
        yield JsonRequest(
            url="https://postoffice.posindonesia.co.id/backend/externalweb/detailayanan",
            data={"iddirian": item["ref"]},
            callback=self.parse_hours,
            cb_kwargs=dict(item=item),
        )

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        if response.status == 400:
            yield item
        else:
            days: dict[str, str | None] = response.json()["data"][0]
            try:
                oh = OpeningHours()
                for day_name, hours in days.items():
                    if hours:
                        hours = hours.split("|")[0]
                        oh.add_range(
                            day=DAYS_ID[day_name.title()], open_time=hours.split("-")[0], close_time=hours.split("-")[1]
                        )
                    if not hours:
                        oh.set_closed(DAYS_ID[day_name.title()])
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours: {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/fail")
            yield item
