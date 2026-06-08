import re
from typing import Any, Iterable, Iterator

from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class EvgoUSSpider(SitemapSpider):
    name = "evgo_us"
    item_attributes = {"brand": "EVgo", "brand_wikidata": "Q61803820"}
    sitemap_urls = ["https://evgo.com/find-a-charger/sites-sitemap.xml"]
    sitemap_rules = [(r"/find-a-charger/[^/]+/[^/]+/[^/]+-\d+/?$", "parse")]
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
            "https": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
        },
        "ZYTE_API_TRANSPARENT_MODE": True,
        "ZYTE_API_DEFAULT_PARAMS": {"browserHtml": True},
        "ROBOTSTXT_OBEY": False,
    }

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        for match in re.finditer(r"<loc>([^<]+)</loc>", response.text):
            url = match.group(1).strip()
            for pattern, callback in self._cbs:
                if pattern.search(url):
                    yield Request(url, callback=callback)
                    break

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
