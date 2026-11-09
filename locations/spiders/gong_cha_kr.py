from typing import Any

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_KR, DELIMITERS_KR, NAMED_DAY_RANGES_KR, OpeningHours
from locations.items import Feature
from locations.spiders.gong_cha import GongChaSpider

HOURS_KR = {
    "days": DAYS_KR,
    "named_day_ranges": NAMED_DAY_RANGES_KR | {"평일/주말": DAYS, "평일": DAYS[:5], "주말": DAYS[5:]},
    "delimiters": DELIMITERS_KR,
    "closed": ["휴무"],
}


class GongChaKRSpider(Spider):
    name = "gong_cha_kr"
    item_attributes = GongChaSpider.item_attributes
    start_urls = ["https://www.gong-cha.co.kr/brand/store/list?page=1"]

    def parse(self, response: Response, page: int = 1, **kwargs: Any) -> Any:
        seqs = response.xpath('//div[@class="table-wrap"]//a/@data-seq').getall()
        if not seqs:
            return

        csrf_name = response.xpath('//meta[@name="_csrf_header"]/@content').get()
        csrf_token = response.xpath('//meta[@name="_csrf"]/@content').get()
        for seq in seqs:
            yield FormRequest(
                "https://www.gong-cha.co.kr/brand/store/store_detail",
                formdata={"seq": seq, csrf_name: csrf_token},
                callback=self.parse_store,
            )

        yield Request(
            f"https://www.gong-cha.co.kr/brand/store/list?page={page + 1}",
            cb_kwargs={"page": page + 1},
        )

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        store = response.json()["data"]

        item = Feature()
        item["ref"] = store["seq"]
        item["branch"] = store["title"]
        item["addr_full"] = store["addr"]
        item["state"] = store["sido"]
        item["lat"] = store["lat"]
        item["lon"] = store["lng"]
        if store["tel"] != "-":
            item["phone"] = store["tel"]

        conveniences = (store.get("convenience") or "").split(",")
        apply_yes_no(Extras.TOILETS, item, "20" in conveniences)
        apply_yes_no(Extras.WIFI, item, "40" in conveniences)

        if "연중" in (store.get("holiday") or "연중"):
            item["opening_hours"] = OpeningHours()
            times = (store.get("time") or "").replace("<br>", " ")
            item["opening_hours"].add_ranges_from_string(times, **HOURS_KR)
            if not item["opening_hours"].day_hours and times[:1].isdigit():
                item["opening_hours"].add_ranges_from_string(f"평일/주말 {times}", **HOURS_KR)
            if len(item["opening_hours"].day_hours) < 7:
                item["opening_hours"] = None

        apply_category(Categories.CAFE, item)
        yield item
