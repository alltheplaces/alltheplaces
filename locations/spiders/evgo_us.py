from typing import Any, AsyncIterator, Iterable, Iterator

from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS
from locations.user_agents import BROWSER_DEFAULT


class EvgoUSSpider(SitemapSpider, PlaywrightSpider):
    name = "evgo_us"
    item_attributes = {"brand": "EVgo", "brand_wikidata": "Q61803820"}
    sitemap_urls = ["https://evgo.com/find-a-charger/sites-sitemap.xml"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False} | DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS

    async def start(self) -> AsyncIterator[Request]:
        # Route the sitemap fetch through Playwright to bypass the Vercel security checkpoint
        for url in self.sitemap_urls:
            yield Request(
                url,
                callback=self._parse_sitemap,
                meta={"playwright": True, "playwright_include_page": True},
            )

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            request.meta["playwright"] = True
            request.meta["playwright_include_page"] = True
            yield request

    def parse(self, response: Response, **kwargs: Any) -> Iterator[Feature]:
        # Skip the root overview page if it comes through the sitemap
        if response.url.strip("/").endswith("find-a-charger"):
            return

        item = Feature()
        item["website"] = response.url
        item["ref"] = response.url.rsplit("-", 1)[1].strip("/")
        item["branch"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath("//ol/li[last()]//span/text()").get()
        item["state"] = response.xpath("//ol/li[2]//a/text()").get("").upper()
        item["addr_full"] = (
            response.xpath("//title/text()").get().split(" | ", 1)[0].removeprefix("EVgo EV Charging Station in ")
        )
        item["extras"]["capacity"] = (
            response.xpath('//div[contains(@title, " stalls at this location")]/@title')
            .get("")
            .removesuffix(" stalls at this location")
        )

        extract_google_position(item, response)

        apply_category(Categories.CHARGING_STATION, item)

        yield item
