from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class HongkongPostHKSpider(Spider):
    name = "hongkong_post_hk"
    item_attributes = {"operator": "香港郵政 Hongkong Post", "operator_wikidata": "Q196631"}
    allowed_domains = ["www.hongkongpost.hk"]
    # DATA.GOV.HK "Post Office" dataset, updated monthly.
    start_urls = ["https://www.hongkongpost.hk/opendata/post-office.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for office in response.json()["data"]:
            item = Feature()
            item["ref"] = office["officeCode"]
            item["branch"] = office["nameEN"].removesuffix(" Post Office")
            item["extras"]["branch:zh-Hant"] = office["nameTC"].removesuffix("郵政局")
            item["lat"], item["lon"] = office["latitude"], office["longitude"]
            item["addr_full"] = office["addressEN"]
            item["extras"]["addr:full:zh-Hant"] = office["addressTC"]
            item["city"] = office["districtEN"]
            oh = OpeningHours()
            for rule in office.get("openHour") or []:
                day = int(rule["dayOfWeekCode"])  # 1 = Monday … 7 = Sunday
                if 1 <= day <= 7:
                    oh.add_range(DAYS[day - 1], rule["timeFm"], rule["timeTo"])
            item["opening_hours"] = oh
            apply_category(Categories.POST_OFFICE, item)
            yield item
