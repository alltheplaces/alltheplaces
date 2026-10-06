from itertools import groupby
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class PostLUSpider(Spider):
    name = "post_lu"
    item_attributes = {"operator": "POST Luxembourg", "operator_wikidata": "Q1570910"}
    allowed_domains = ["www.post.lu", "api.post.lu"]
    # The post.lu finders read their API base URL and public client id from this config.
    start_urls = ["https://www.post.lu/ng-conf/sales-points-babel-web.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        config = response.json()
        api = config["salespoints-babel-api"]
        headers = {"X-IBM-Client-Id": config["clientId"]}
        yield JsonRequest(
            f"{api['url']}{api['salespoints']}?type=LETTER_BOX", headers=headers, callback=self.parse_boxes
        )
        groups = f"{api['url']}{api['salespointsgroups']}"
        yield JsonRequest(
            groups, headers=headers, callback=self.parse_groups, cb_kwargs={"url": groups, "headers": headers}
        )

    def parse_boxes(self, response: Response) -> Any:
        for box in response.json()["data"]:
            item = self.base_item(box)
            item["ref"] = box["id"]
            item["extras"]["ref:post_lu"] = box["name"]
            times = {
                DAYS[t["day"] - 1]: f"{t['startHour']:02d}:{t['startMinute']:02d}"
                for t in box.get("openingTime") or []
                if 1 <= t.get("day", 0) <= 7 and t.get("startHour") is not None
            }
            collection_times = []
            for time, days in groupby(DAYS, key=times.get):
                if time:
                    days = list(days)
                    collection_times.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
            if collection_times:
                item["extras"]["collection_times"] = "; ".join(collection_times)
            apply_category(Categories.POST_BOX, item)
            yield item

    def parse_groups(self, response: Response, url: str, headers: dict) -> Any:
        page = response.json()
        for group in page["data"]:
            for point in group.get("salesPoints") or []:
                if point["type"] == "SHOP_COURRIER":
                    item = self.base_item(point)
                    item["ref"] = point["id"]
                    item["branch"] = point["name"].removeprefix("Bureau de poste ").strip()
                    item["opening_hours"] = self.parse_hours(point.get("openingTime") or [])
                    apply_category(Categories.POST_OFFICE, item)
                    yield item
                elif point["type"] == "POST_POINT":
                    item = self.base_item(point)
                    item["ref"] = point["id"]
                    item["name"] = point["name"]
                    item["extras"]["post_office"] = "post_partner"
                    apply_category(Categories.GENERIC_POI, item)
                    yield item
        # The groups list is paged: "count" is the total, "first" the offset of this page.
        fetched = page.get("first", 0) + len(page["data"])
        if page["data"] and fetched < page.get("count", 0):
            yield JsonRequest(
                f"{url}?first={fetched}",
                headers=headers,
                callback=self.parse_groups,
                cb_kwargs={"url": url, "headers": headers},
            )

    @staticmethod
    def base_item(point: dict) -> Feature:
        item = Feature()
        item["lat"], item["lon"] = point.get("latitude"), point.get("longitude")
        item["housenumber"] = point.get("numStreet")
        item["street"] = point.get("street")
        item["postcode"] = point.get("zipCode")
        item["city"] = point.get("city")
        return item

    @staticmethod
    def parse_hours(times: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for t in times:
            if t.get("category") != "Courrier" or t.get("endHour") is None or not 1 <= t.get("day", 0) <= 7:
                continue
            oh.add_range(
                DAYS[t["day"] - 1],
                f"{t['startHour']:02d}:{t['startMinute']:02d}",
                f"{t['endHour']:02d}:{t['endMinute']:02d}",
            )
        return oh
