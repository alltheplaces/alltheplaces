from typing import Any, AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import FormRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SupermacsGBIESpider(Spider):
    name = "supermacs_gb_ie"
    item_attributes = {
        "brand_wikidata": "Q7643750",
        "brand": "Supermac's",
    }
    allowed_domains = [
        "supermacs.ie",
    ]

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            "https://supermacs.ie/wp-admin/admin-ajax.php",
            formdata={"action": "get_markers"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["markers"]:
            item = DictParser().parse(location)
            item["website"] = location["store_link"]
            if url := (location["store_front_image"] or {}).get("url"):
                # Filter the generic fallback image that appears on most stores
                if "Image-1.jpeg" not in url:
                    item["image"] = url
            item["phone"] = location["store_telephone"]
            item["addr_full"] = item["addr_full"].replace("<br />", "")
            item["ref"] = item["website"]
            item["opening_hours"] = self.parse_hours(location["store_opening_hours"])

            yield item

    @staticmethod
    def parse_hours(hours_html: str) -> OpeningHours:
        oh = OpeningHours()
        # Further tables with the same id belong to co-located brands or delivery hours
        rows = Selector(text=hours_html).xpath('(//table[@id="store-schedule"])[1]/tbody/tr')
        days = rows[0].xpath("./th/text()").getall()
        for day, opens, closes in zip(days, rows[1].xpath("./td"), rows[-1].xpath("./td")):
            oh.add_ranges_from_string(f'{day} {opens.xpath("string()").get()} - {closes.xpath("string()").get()}')
        return oh
