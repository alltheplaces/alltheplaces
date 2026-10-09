import csv
import io
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_CN, OpeningHours
from locations.items import Feature


class ChunghwaPostTWSpider(Spider):
    name = "chunghwa_post_tw"
    item_attributes = {"operator": "中華郵政", "operator_wikidata": "Q709259"}
    allowed_domains = ["www.post.gov.tw"]
    # 中華郵政全國營業據點 (https://data.gov.tw/dataset/5950), Open Government Data License v1.
    start_urls = [
        "https://www.post.gov.tw/post/internet/Templates/getOpenDataFile.jsp?vkey=B484EB27-B3F0-4D02-8F62-047D20C64078"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for row in csv.DictReader(io.StringIO(response.body.decode("utf-8-sig"))):
            item = Feature()
            item["ref"] = row["電腦局號"]
            item["branch"] = row["局名"]
            item["lat"], item["lon"] = row["緯度"], row["經度"]
            item["postcode"] = row["郵遞區號"]
            item["state"] = row["縣市"]
            item["city"] = row["鄉鎮市區"]
            item["street_address"] = row["地址"]
            item["phone"] = row["郵務電話"]
            oh = OpeningHours()
            # Mail-counter hours are in the "週一 郵務" to "週五 郵務" columns on weekdays ("週一 儲匯" etc. are the
            # savings counters) and in "週六" and "週日" at weekends.
            for column, value in row.items():
                day_name, _, counter = (column or "").partition(" ")
                if (day := DAYS_CN.get(day_name)) and counter in ("郵務", ""):
                    for start, end in re.findall(r"(\d{2}:\d{2})-(\d{2}:\d{2})", value or ""):
                        oh.add_range(day, start, end)
            item["opening_hours"] = oh
            apply_category(Categories.POST_OFFICE, item)
            yield item
