import re
from typing import Any, AsyncIterator

from scrapy import Selector
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours, sanitise_day
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class ErikshjalpenSESpider(PlaywrightSpider):
    name = "erikshjalpen_se"
    item_attributes = {
        "brand": "Erikshjälpen Second Hand",
        "brand_wikidata": "Q10487741",
        "country": "SE",
    }
    allowed_domains = ["erikshjalpen.se"]
    start_urls = ["https://erikshjalpen.se/en/our-stores/find-store-and-opening-hours/"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "PLAYWRIGHT_ABORT_REQUEST": lambda request: request.resource_type not in ["document", "script", "fetch"],
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url=self.start_urls[0],
            callback=self.parse,
            meta={"playwright": True, "playwright_include_page": True},
        )

    async def parse(self, response: Response, **kwargs: Any) -> Any:
        page = response.meta["playwright_page"]
        await page.wait_for_load_state("domcontentloaded", timeout=15000)
        for _ in range(10):
            clicked = await page.evaluate(
                """() => {
                    const btn = document.querySelector('button.load-button');
                    if (!btn || !btn.offsetParent) return false;
                    btn.scrollIntoView({block: 'center'});
                    btn.click();
                    return true;
                }"""
            )
            if not clicked:
                break
            await page.wait_for_timeout(2000)
        html_content = await page.content()
        await page.close()

        selector = Selector(text=html_content)
        for store in selector.xpath('//div[contains(@class, "store-wrapper")]'):
            item = Feature()

            name = store.xpath('.//span[contains(@class, "font-size-3")]/text()').get()
            if name:
                item["name"] = name.strip()

            store_url = store.xpath('.//a[contains(@class, "contact--storeurl")][contains(@href, "/stores/")]/@href').get()
            if store_url:
                item["website"] = store_url
                item["ref"] = store_url.rstrip("/").split("/")[-1]

            map_link = store.xpath('.//a[contains(@href, "google.com/maps/place/")]/@href').get()
            if map_link:
                if m := re.search(r"place/([-\d.]+),([-\d.]+)", map_link):
                    item["lat"] = m.group(1)
                    item["lon"] = m.group(2)

            addr = store.xpath('.//div[contains(@class, "contact")]//ul[contains(@class, "infoline")]/li[1]/span[2]/text()').get()
            if addr:
                item["street_address"] = addr.strip()

            phone = store.xpath('.//div[contains(@class, "contact")]//a[starts-with(@href, "tel:")]/text()').get()
            if phone:
                item["phone"] = phone.strip()

            email = store.xpath('.//div[contains(@class, "contact")]//a[starts-with(@href, "mailto:")]/text()').get()
            if email:
                item["email"] = email.strip()

            item["opening_hours"] = self.parse_opening_hours(store)

            apply_category(Categories.SHOP_SECOND_HAND, item)

            yield item

    def parse_opening_hours(self, store) -> OpeningHours:
        oh = OpeningHours()
        for li in store.xpath('.//div[contains(@class, "openhours")]//ul[contains(@class, "infoline")]/li'):
            day_str = li.xpath('.//span[contains(@class, "day")]/text()').get()
            times_str = li.xpath('.//span[contains(@class, "opentimes")]/text()').get()
            if not day_str or not times_str:
                continue
            day = sanitise_day(day_str.strip(), DAYS_EN)
            if not day:
                continue
            times_str = times_str.strip()
            if "closed" in times_str.lower():
                oh.set_closed(day)
                continue
            if m := re.match(r"(\d{4})\s*-\s*(\d{4})", times_str):
                open_t = m.group(1)
                close_t = m.group(2)
                oh.add_range(day, f"{open_t[:2]}:{open_t[2:]}", f"{close_t[:2]}:{close_t[2:]}")
        return oh
