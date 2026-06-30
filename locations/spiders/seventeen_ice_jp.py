import json
import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

PREFECTURES = [
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
]


class SeventeenIceJPSpider(Spider):
    name = "seventeen_ice_jp"
    item_attributes = {"brand": "セブンティーンアイス", "brand_wikidata": "Q11314427"}
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "COOKIES_ENABLED": True,
    }

    async def start(self) -> AsyncIterator[Request]:
        # Visit the homepage first to establish a Laravel session cookie, then
        # request one search page per prefecture.
        yield Request(
            url="https://seventeenice-map.glico.com/",
            callback=self.request_prefectures,
        )

    def request_prefectures(self, response: Response, **kwargs: Any) -> Any:
        for pref in PREFECTURES:
            yield Request(
                url=f"https://seventeenice-map.glico.com/search?pn={pref}",
                callback=self.parse,
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        match = re.search(r'pointJson\s*=\s*(".*?");', response.text, re.DOTALL)
        if not match:
            return
        locations = json.loads(json.loads(match.group(1)))

        for loc in locations:
            ref = loc.get("id")
            if not ref:
                continue

            item = Feature()
            item["ref"] = ref
            item["website"] = f"https://seventeenice-map.glico.com/spot/{ref}"
            item["branch"] = loc.get("location_name")
            item["extras"]["branch:ja-Hira"] = loc.get("location_name_read") or None
            item["lat"] = loc.get("latitude")
            item["lon"] = loc.get("longitude")
            item["postcode"] = loc.get("postal_code")
            item["addr_full"] = loc.get("address")
            item["phone"] = loc.get("phone") or None
            item["extras"]["addr:province"] = loc.get("pref")
            item["city"] = loc.get("city")
            # item["street_address"] = loc.get("street_address") # this has bad data, do not use

            apply_category(Categories.VENDING_MACHINE, item)
            item["extras"]["vending"] = "ice_cream"

            yield item
