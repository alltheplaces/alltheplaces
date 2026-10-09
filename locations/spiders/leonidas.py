import json
import logging
from typing import Any, AsyncIterator

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from scrapy.http import Request, Response
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE

logger = logging.getLogger(__name__)


async def pass_turnstile(page: Page) -> None:
    try:
        for _ in range(60):
            try:
                if await page.locator("[data-shops]").count():
                    return
            except PlaywrightError:
                pass  # Kinsta interstitial still redirecting
            if any("challenges.cloudflare.com" in frame.url for frame in page.frames):
                break
            await page.wait_for_timeout(500)
        else:
            raise PlaywrightTimeoutError("Neither the shops page nor a Turnstile challenge loaded")
        # The generic click solver can't find this Turnstile checkbox, but it takes keyboard focus.
        await page.wait_for_timeout(6000)
        await page.keyboard.press("Tab")
        await page.keyboard.press("Space")
        try:
            await page.wait_for_selector("[data-shops]", state="attached", timeout=10000)
        except PlaywrightTimeoutError:
            # Focus sometimes lands on the Cloudflare logo link, one Tab past the checkbox.
            await page.keyboard.press("Shift+Tab")
            await page.keyboard.press("Space")
            await page.wait_for_selector("[data-shops]", state="attached", timeout=30000)
    except PlaywrightError:
        logger.error(
            "Turnstile not passed: title=%r url=%s html=%r", await page.title(), page.url, (await page.content())[:1000]
        )
        raise


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
            if website := item.get("website"):
                # Mostly scheme-less; drop placeholders with no domain such as "www."
                if "." in website.removeprefix("www."):
                    item["website"] = website if website.startswith("http") else f"https://{website}"
                else:
                    item["website"] = None
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
