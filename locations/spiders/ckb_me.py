import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature

GMARKER_RE = re.compile(
    r"gmarkers\[\d+\]\s*=\s*new\s+Array\(\s*"
    r"'([^']+)'\s*,\s*"  # lat
    r"'\s*([^']+?)\s*'\s*,\s*"  # lng (strip whitespace inside quotes)
    r"'([PZN])'\s*,\s*"  # type
    r"'(\d+)'"  # id
)


class CkbMESpider(Spider):
    name = "ckb_me"
    item_attributes = {"brand": "Crnogorska Komercijalna Banka", "brand_wikidata": "Q869855"}

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            url="https://www.ckb.me/site/locations/map.aspx",
            formdata={},
            headers={"Origin": "https://www.ckb.me", "Referer": "https://www.ckb.me/site/locations/map.aspx"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for lat, lng, marker_type, marker_id in GMARKER_RE.findall(response.text):
            yield FormRequest(
                url="https://www.ckb.me/site/locations/get_details.aspx",
                formdata={"id": marker_id},
                cb_kwargs={"lat": lat, "lng": lng, "marker_type": marker_type, "marker_id": marker_id},
                callback=self.parse_detail,
            )

    def parse_detail(
        self, response: Response, lat: str, lng: str, marker_type: str, marker_id: str, **kwargs: Any
    ) -> Any:
        # Source is HTML, no DictParser
        item = Feature()
        item["ref"] = marker_id
        item["lat"] = lat
        item["lon"] = lng

        name = response.xpath('normalize-space(//*[contains(@class, "location-name")])').get()
        if " - " in name:
            item["city"], item["street_address"] = name.split(" - ", 1)
        item["branch"] = name

        phones = [p.strip() for p in response.xpath('//*[contains(@class, "location-phone")]/text()').getall()]
        phones = [p for p in phones if p]
        if phones:
            item["phone"] = phones[-1]

        if marker_type == "P":
            apply_category(Categories.ATM, item)
        elif marker_type == "Z":
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, True)
        elif marker_type == "N":
            apply_category(Categories.BANK, item)
        else:
            self.logger.error("Unexpected CKB marker type: %s", marker_type)
            return

        yield item
