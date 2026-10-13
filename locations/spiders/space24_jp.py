from datetime import date
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature

# Prefectures in JIS X 0401 order, so the "address1" code is the index plus one.
PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]  # fmt: skip


class Space24JPSpider(Spider):
    name = "space24_jp"
    item_attributes = {"brand": "スペース24", "operator": "株式会社スペース24"}
    allowed_domains = ["space24.co.jp"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The map asks for the car parks in its bounding box, given as
        # (south, west)/(north, east). This box covers all of Japan.
        yield JsonRequest("https://space24.co.jp/api/parkings/map/(0,%200)/(90,%20180)")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for parking in response.json()["Parking"]:
            if parking["close_date"] and date.fromisoformat(parking["close_date"]) <= date.today():
                # Car parks stay in the list after they close.
                continue
            item = Feature()
            item["ref"] = str(parking["id"])
            # e.g. "スペース 葵第４", "チケパ 武里駅前第１" or "スペースECO 名古屋篠原橋通第１".
            item["name"] = parking["park_name"]
            # The map places the markers with these as WGS 84 coordinates.
            item["lat"] = parking["map_y"]
            item["lon"] = parking["map_x"]
            item["state"] = PREFECTURES[parking["address1"] - 1]
            item["addr_full"] = "".join(
                filter(None, [item["state"], parking["address2"], (parking["address3"] or "").strip()])
            )
            item["website"] = f"https://space24.co.jp/parkings/detail/{parking['id']}"
            if parking["max_num"]:
                item["extras"]["capacity"] = str(parking["max_num"])
            if parking["24h_flg"] == 1:
                item["opening_hours"] = "24/7"
            # Every car park lists its prices.
            apply_yes_no(Extras.FEE, item, True)
            apply_category(Categories.PARKING, item)
            yield item
