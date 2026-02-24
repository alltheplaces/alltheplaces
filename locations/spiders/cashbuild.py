from typing import AsyncIterator, Iterable

from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class CashbuildSpider(JSONBlobSpider):
    name = "cashbuild"
    item_attributes = {"brand": "Cashbuild", "brand_wikidata": "Q116474606"}
    allowed_domains = ["www.cashbuild.co.za"]
    start_urls = ["https://www.cashbuild.co.za/module/radiusdelivery/StoreSelectorAjax"]
    locations_key = "stores"
    requires_proxy = True

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

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["active"] or not feature["storeActive"]:
            return

        item["ref"] = str(feature["id_store"])
        item["branch"] = item.pop("name", None)
        item["addr_full"] = merge_address_lines([feature["address1"], feature["address2"]])
        item.pop("street_address", None)

        item["opening_hours"] = OpeningHours()
        hours_text = ""
        for day_index, day_hours in enumerate(feature["hoursArray"]):
            hours_text = "{} {}: {}".format(hours_text, DAYS_FROM_SUNDAY[day_index], day_hours["text"])
        item["opening_hours"].add_ranges_from_string(hours_text)

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
