from typing import Any, AsyncIterator
from uuid import uuid4

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class ScotiabankSpider(Spider):
    name = "scotiabank"
    item_attributes = {"brand": "Scotiabank", "brand_wikidata": "Q451476"}
    allowed_domains = ["api.scotiabank.com"]
    base_url = "https://api.scotiabank.com/assets-locator/v1/search/asset/near?asset_types=branch&lat=56.13&lon=-106.34&radius=8000&page={page}&count=50&country=CA&locale=en-CA&rolling_days=true&show_holidays=true&include_abm_info=true"

    def request_page(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=self.base_url.format(page=page),
            headers={
                "x-b3-traceid": str(uuid4()),
                "x-b3-spanid": str(uuid4()),
                "x-channel-id": "Online",
                "x-originating-appl-code": "BGMN",
                "x-country-code": "CA",
            },
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.request_page(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        branches = response.json()["data"] or []
        for branch in branches:
            if branch["status"]["code"] != "OPE":
                continue
            branch.update((branch.pop("addresses", None) or [{}])[0])
            item = DictParser.parse(branch)
            item["branch"] = item.pop("name").strip()
            item["street_address"] = merge_address_lines([branch.get("line_1_addr"), branch.get("line_2_addr")])
            item["state"] = branch.get("state")
            item["postcode"] = branch.get("postal_cd")

            for contact in branch.get("contact_numbers") or []:
                if contact["contact_type_cd"]["code"] == "P":
                    item["phone"] = "+{} {} {}".format(
                        contact["phone_country_cd"], contact["phone_area_cd"], contact["phone_no"]
                    )

            item["opening_hours"] = OpeningHours()
            for rule in branch.get("open_hours") or []:
                if rule["open_time"] and rule["close_time"]:
                    item["opening_hours"].add_range(rule["day_of_week"], rule["open_time"], rule["close_time"])
                else:
                    item["opening_hours"].set_closed(rule["day_of_week"])

            apply_category(Categories.BANK, item)
            yield item

        if branches:
            yield self.request_page(response.meta["page"] + 1)
