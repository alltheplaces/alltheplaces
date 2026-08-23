import re
from typing import Any, AsyncIterator

import scrapy
from scrapy import Request
from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class HowardHannaSpider(CamoufoxSpider):
    name = "howard_hanna"
    item_attributes = {"brand": "Howard Hanna", "brand_wikidata": "Q119573413"}
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]
    requires_proxy = "US"

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
        for office in response.json().get("Properties", []):
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
