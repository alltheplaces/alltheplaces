from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class PosIndonesiaIDSpider(Spider):
    name = "pos_indonesia_id"
    item_attributes = {"brand": "Pos Indonesia", "brand_wikidata": "Q4273095"}

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
            item["name"] = location["nama_dirian"]
            item["city"] = location["kabupaten"].removeprefix("KOTA ")
            if item["city"].startswith("KAB."):
                item["state"] = item.pop("city").removeprefix("KAB. ")
            if location_type == "MR":
                apply_category({"amenity": "mailroom"}, item)
            else:
                apply_category(Categories.POST_OFFICE, item)
            yield JsonRequest(
                url="https://postoffice.posindonesia.co.id/backend/externalweb/detailktr",
                data={"id_dirian": location["id_dirian"]},
                callback=self.parse_details,
                cb_kwargs=dict(item=item),
            )

    def parse_details(self, response: Response, item: Feature) -> Any:
        location = response.json()["data"][0]
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        item["street_address"] = location["alamat"]
        item["phone"] = location["telpon_old"]
        item["website"] = "https://postoffice.posindonesia.co.id/"
        yield item
