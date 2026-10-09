import json
from typing import Any, AsyncIterator

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from scrapy.http import Request, Response
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


async def pass_turnstile(page: Page) -> None:
    # The generic click solver can't find this Turnstile checkbox, but it takes keyboard focus.
    await page.wait_for_url("**ki-cf-botcl=1**", wait_until="commit", timeout=30000)
    await page.wait_for_timeout(8000)
    await page.keyboard.press("Tab")
    await page.keyboard.press("Space")
    try:
        await page.wait_for_selector("[data-shops]", state="attached", timeout=10000)
    except PlaywrightTimeoutError:
        # Focus sometimes lands on the Cloudflare logo link, one Tab past the checkbox.
        await page.keyboard.press("Shift+Tab")
        await page.keyboard.press("Space")
        await page.wait_for_selector("[data-shops]", state="attached", timeout=20000)


class LeonidasSpider(CamoufoxSpider):
    name = "leonidas"
    item_attributes = {"brand": "Leonidas", "brand_wikidata": "Q80335"}
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            "https://www.leonidas.com/en/shops/", meta={"camoufox_page_methods": [PageMethod(pass_turnstile)]}
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in json.loads(response.xpath("//@data-shops").get()):
            item = DictParser.parse(data)
            item["street_address"] = item.pop("street")
            if item.get("email"):
                item["email"] = item["email"][0]
            try:
                oh = OpeningHours()
                for key, value in data.get("schedule").items():
                    if value:
                        for time in value:
                            open_time = time[0]
                            close_time = time[1]
                            oh.add_range(day=key, open_time=open_time, close_time=close_time, time_format="%H:%M:%S")
                item["opening_hours"] = oh
            except:
                pass
            yield item
