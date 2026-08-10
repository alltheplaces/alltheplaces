import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SdiBrokerBGSpider(Spider):
    """Spider for SDI Broker (Bulgaria) insurance offices.
    Closes #5915
    """

    name = "sdi_broker_bg"
    item_attributes = {"brand": "SDI Broker", "brand_wikidata": "Q65224484"}
    start_urls = ["https://www.sdi.bg/sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in response.xpath("//url/loc/text() | //*[local-name()='loc']/text()").getall():
            if re.match(r"https://www\.sdi\.bg/offices/[a-z].*\.html$", url):
                yield response.follow(url, callback=self.parse_city)

    def parse_city(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        m = re.search(r"var offices\s*=\s*(\[[\s\S]*?\]);", response.text)
        if not m:
            return
        for office in json.loads(m.group(1)):
            if office.get("office_status") != "2":
                continue
            item = Feature()
            item["ref"] = office["office_id"]
            item["branch"] = office.get("office_name", "").replace("Офис ", "").strip() or None
            item["street_address"] = office.get("office_address")
            item["lat"] = office.get("office_gps_lat")
            item["lon"] = office.get("office_gps_lon")
            item["phone"] = office.get("office_phones") or None
            item["email"] = office.get("office_email") or None

            # office_working_hours_rich is already in OSM opening_hours format
            if hours_str := office.get("office_working_hours_rich", "").strip().strip('"'):
                oh = OpeningHours()
                oh.add_ranges_from_string(hours_str)
                item["opening_hours"] = oh

            apply_category(Categories.OFFICE_INSURANCE, item)
            yield item
