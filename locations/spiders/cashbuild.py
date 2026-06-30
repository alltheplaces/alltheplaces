import json
import re
from typing import Any, AsyncIterator

from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class CashbuildSpider(PlaywrightSpider):
    name = "cashbuild"
    item_attributes = {"brand": "Cashbuild", "brand_wikidata": "Q116474606"}
    allowed_domains = ["www.cashbuild.co.za"]
    start_urls = ["https://www.cashbuild.co.za/module/radiusdelivery/StoreSelectorAjax"]
    requires_proxy = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[FormRequest]:
        for country_code in ["BW", "LS", "MW", "NA", "SZ", "ZA"]:
            formdata = {
                "ajax": "1",
                "action": "GetMarkers",
                "all": "1",
                "country": country_code,
                "latitude": "0",
                "longitude": "0",
                "map": "selectorMap",
            }
            yield FormRequest(url=self.start_urls[0], method="POST", formdata=formdata)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = re.search(r"stores\":(\[.*\]),\"stores_list_html", response.text).group(1)
        for location in json.loads(raw_data):

            if not location["active"] or not location["storeActive"]:
                return
            item = DictParser.parse(location)

            item["ref"] = str(location["id_store"])
            item["branch"] = item.pop("name", "").removesuffix("| Cashbuild")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["addr_full"] = location["full_address"]

            item["opening_hours"] = OpeningHours()
            hours_text = ""
            for day_index, day_hours in enumerate(location["hoursArray"]):
                hours_text = "{} {}: {}".format(hours_text, DAYS_FROM_SUNDAY[day_index], day_hours["text"])
            item["opening_hours"].add_ranges_from_string(hours_text)

            apply_category(Categories.SHOP_DOITYOURSELF, item)
            yield item
