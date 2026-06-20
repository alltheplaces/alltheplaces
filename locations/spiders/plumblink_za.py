from typing import AsyncIterator, Iterable

from scrapy.http import FormRequest, Request, Response
from scrapy_playwright.page import PageMethod

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS


class PlumblinkZASpider(JSONBlobSpider):
    name = "plumblink_za"
    item_attributes = {"brand": "Plumblink", "brand_wikidata": "Q127596751"}
    start_urls = ["https://api.esolve.co.za/get-locations.php?is_active=true&ws_id=PLNK01"]
    locations_key = "records"
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.plumblink.co.za/store-locator",
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle"),
                ],
            },
            callback=self.parse_cookie,
        )

    async def parse_cookie(self, response) -> AsyncIterator[FormRequest]:
        page = response.meta["playwright_page"]

        try:
            cookies = await page.context.cookies()
        finally:
            await page.close()

        auth_cookie = next((c for c in cookies if c["name"] == "_ng_eslv_token"), None)

        yield FormRequest(url=self.start_urls[0], headers={"authorization": auth_cookie["value"]})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["head_office"] == 1:
            return

        item["branch"] = feature.pop("description", "").removeprefix("Plumblink ")
        item["website"] = "https://www.plumblink.co.za/store/" + feature.pop("identifier", "")

        item["street_address"] = item.pop("street", "")

        item["phone"] = feature.pop("branch_telnumber", "")
        item["email"] = feature.pop("branch_email", "")
        item["extras"]["contact:whatsapp"] = feature.pop("branch_whatsapp_number", "")
        item["extras"]["fax"] = feature.pop("branch_fax", "")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            open_time = feature.get(f"{day.lower()}_open_time")
            close_time = feature.get(f"{day.lower()}_close_time")
            if open_time == close_time:
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day, open_time, close_time)

        apply_category(Categories.SHOP_HARDWARE, item)

        yield item
