import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature

ICON_CATEGORY_MAP = {
    "car": Categories.PARKING,
    "bicycle": Categories.BICYCLE_PARKING,
    "motorcycle": Categories.MOTORCYCLE_PARKING,
}

LIST_URL = "https://smilepark.seiburealestate-pm.co.jp/parking/list/service0.html"
RESERVATION_URL = "https://smilepark.seiburealestate-pm.co.jp/parking/list/service6.html"
REFERER = "https://smilepark.seiburealestate-pm.co.jp/parking/"


class SeibuSmileParkJPSpider(scrapy.Spider):
    name = "seibu_smile_park_jp"
    item_attributes = {"brand": "西武スマイルパーク"}
    allowed_domains = ["smilepark.seiburealestate-pm.co.jp"]

    # There is no sitemap covering all lots, only a paginated (5 per page)
    # POST search. Car/motorcycle/bicycle are queried separately via the
    # type[] filter because a single lot can appear under more than one
    # type. Reservation-style lots ("予約式駐車場", operated through a
    # partner booking platform) live in a separate search bucket that isn't
    # returned by the type[] filters at all, so it's queried on its own.
    SEARCHES = [
        (LIST_URL, {"type[]": "1", "h_m[]": ["1", "2"]}),
        (LIST_URL, {"type[]": "2", "h_m[]": ["1", "2"]}),
        (LIST_URL, {"type[]": "4", "h_m[]": ["1", "2"]}),
        (RESERVATION_URL, {}),
    ]

    async def start(self):
        for url, formdata in self.SEARCHES:
            yield scrapy.FormRequest(
                url,
                formdata=formdata,
                headers={"Referer": REFERER},
                callback=self.parse_list,
                meta={"formdata": formdata, "url": url},
            )

    def parse_list(self, response):
        formdata = response.meta["formdata"]
        url = response.meta["url"]

        for href in response.css("p.more a::attr(href)").getall():
            yield scrapy.Request(response.urljoin(href), callback=self.parse_detail)

        if "p" not in formdata:
            total = int(response.css(".result-head-block .number strong::text").get("0"))
            for p in range(2, -(-total // 5) + 1):
                page_formdata = {**formdata, "p": str(p)}
                yield scrapy.FormRequest(
                    url,
                    formdata=page_formdata,
                    headers={"Referer": REFERER},
                    callback=self.parse_list,
                    meta={"formdata": page_formdata, "url": url},
                )

    def parse_detail(self, response):
        name = response.css("h1.title::text").get()
        match = re.search(r"new google\.maps\.LatLng\(([\d.\-]+),\s*([\d.\-]+)\)", response.text)
        if not name or not match:
            return
        lat, lon = match.groups()

        address = response.css("address.address .value::text").get()
        post_id = response.url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html")

        for icon in response.css("ul.assort-list img::attr(src)").getall():
            for key, category in ICON_CATEGORY_MAP.items():
                if f"icon-assort-{key}.svg" not in icon:
                    continue

                item = Feature()
                item["ref"] = f"{post_id}_{key}"
                item["name"] = name.strip()
                item["lat"] = lat
                item["lon"] = lon
                item["addr_full"] = address.strip() if address else None
                item["country"] = "JP"
                item["website"] = response.url

                apply_category(category, item)

                yield item
