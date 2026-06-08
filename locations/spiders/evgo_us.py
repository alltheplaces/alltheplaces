from typing import Any, AsyncIterator, Iterable, Iterator

from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class EvgoUSSpider(SitemapSpider, CamoufoxSpider):
    name = "evgo_us"
    item_attributes = {"brand": "EVgo", "brand_wikidata": "Q61803820"}
    sitemap_urls = ["https://evgo.com/find-a-charger/sites-sitemap.xml"]
    sitemap_rules = [(r"/find-a-charger/[^/]+/[^/]+/[^/]+-\d+/?$", "parse")]
    custom_settings = {
        **DEFAULT_CAMOUFOX_SETTINGS,
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type not in ("document", "script", "xhr", "fetch"),
    }

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            "https://evgo.com/find-a-charger",
            callback=self._after_warmup,
            meta={
                "camoufox_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle"),
                ],
            },
            dont_filter=True,
        )

    def _after_warmup(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap, dont_filter=True)

    def parse(self, response: Response, **kwargs: Any) -> Iterator[Feature]:
        item = Feature()
        item["website"] = response.url
        item["ref"] = response.url.rsplit("-", 1)[1].strip("/")
        item["branch"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath("//ol/li[last()]//span/text()").get()
        state = response.xpath("//ol/li[2]//a/text()").get()
        item["state"] = state.upper() if state else None
        title = response.xpath("//title/text()").get() or ""
        item["addr_full"] = title.split(" | ", 1)[0].removeprefix("EVgo EV Charging Station in ") or None
        capacity = response.xpath('//div[contains(@title, " stalls at this location")]/@title').get()
        if capacity:
            item["extras"]["capacity"] = capacity.removesuffix(" stalls at this location")

        extract_google_position(item, response)

        apply_category(Categories.CHARGING_STATION, item)

        yield item
