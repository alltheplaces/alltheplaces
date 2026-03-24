import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class PalmBeachTanUSSpider(SitemapSpider):
    name = "palm_beach_tan_us"
    item_attributes = {"brand": "Palm Beach Tan", "brand_wikidata": "Q64027086"}
    sitemap_urls = ["https://palmbeachtan.com/sitemap-locations.xml"]
    sitemap_rules = [(r"https://palmbeachtan.com/locations/[^/]+/[a-z0-9-]+", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        properties = {
            "ref": response.url,
            "branch": " ".join(response.xpath("//main/section[1]/div[1]/h1/text()[2]").get().split())
            .replace(" - NOW HIRING!", "")
            .replace(" - Now Hiring!", "")
            .replace(" - NOW OPEN!", "")
            .replace(" - Now Open!", ""),
            "addr_full": " ".join(response.xpath("//address[1]/text()").get().split()),
            "phone": response.xpath('//a[contains(@href, "tel:")]/text()').get(),
            "website": response.url,
        }

        coordinates_raw = response.xpath('//script[contains(@src, "flowbite")]/following::script/text()').get()
        if m := re.search(
            r"haversine\(position\.coords\.latitude, position\.coords\.longitude, (\-?\d+\.\d+), (\-?\d+\.\d+),",
            coordinates_raw,
        ):
            properties["lat"] = m.group(1)
            properties["lon"] = m.group(2)

        hours_raw = (
            " ".join(response.xpath("//main/section[1]/div[last()]/div/table/tbody/tr/td/text()").getall())
            .replace(" AM", "AM")
            .replace(" am", "AM")
            .replace(" PM", "PM")
            .replace(" pm", "PM")
            .replace("-", " ")
            .replace("—", "")
            .replace("89:00PM", "9:00PM")
            .split()
        )
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        oh = OpeningHours()
        for day in hours_raw:
            if day[0] not in DAYS_EN:
                continue
            if ":" not in day[1]:
                continue
            oh.add_range(DAYS_EN[day[0]], day[1], day[2], "%I:%M%p")
        properties["opening_hours"] = oh

        yield Feature(**properties)
