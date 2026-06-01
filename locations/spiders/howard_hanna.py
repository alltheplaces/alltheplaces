import json
import re
from typing import Any, AsyncIterator

import scrapy
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class HowardHannaSpider(PlaywrightSpider):
    name = "howard_hanna"
    item_attributes = {"brand": "Howard Hanna", "brand_wikidata": "Q119573413"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "DOWNLOAD_DELAY": 5,
        "CONCURRENT_REQUESTS": 1,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.howardhanna.com",
            "Referer": "https://www.howardhanna.com/Office/Map",
            "User-Agent": BROWSER_DEFAULT,
        },
    }

    async def start(self) -> AsyncIterator[Request]:
        url = "https://www.howardhanna.com/Office/MapOffices"
        formdata = {
            "SouthLat": "10.236576558188718",
            "WestLng": "-115.57812500000001",
            "NorthLat": "59.53851123957454",
            "EastLng": "-80.42187500000001",
            "RadiusCenterPointLatitude": "NaN",
            "RadiusCenterPointLongitude": "NaN",
            "Location": "My Current Location",
            "Radius": "10",
            "OrderBy": "Closest",
            "Polygon": "",
        }

        yield scrapy.FormRequest(url=url, method="POST", formdata=formdata, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # This fixes the JSONDecodeError by stripping the <pre> tag
        for office in json.loads(response.xpath("//pre/text()").get()).get("Properties", []):
            branch = office.get("OfficeName")
            mls_number = office.get("MlsNumber")

            item = DictParser.parse(office)
            item["ref"] = mls_number
            item["branch"] = branch
            item["street_address"] = item.pop("addr_full")
            item["website"] = f"https://www.howardhanna.com/Office/Detail/{self.slugify(branch)}/{mls_number}"

            apply_category(Categories.OFFICE_ESTATE_AGENT, item)

            yield item

    def slugify(self, text: str) -> str:
        slug = re.sub(r"[^a-z0-9\s-]", "", re.split(r"\s-\s|/|\\|\s&\s", text)[0].lower())
        return re.sub(r"\s+", "-", slug.strip())
