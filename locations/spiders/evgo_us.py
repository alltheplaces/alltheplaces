from typing import Any, Iterable, Iterator

from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class EvgoUSSpider(SitemapSpider, PlaywrightSpider):
    name = "evgo_us"
    item_attributes = {"brand": "EVgo", "brand_wikidata": "Q61803820"}
    sitemap_urls = ["https://evgo.com/find-a-charger/sites-sitemap.xml"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            request.meta["playwright"] = True
            request.meta["playwright_include_page"] = True
            yield request

    def parse(self, response: Response, **kwargs: Any) -> Iterator[Feature]:
        item = Feature()
        item["website"] = response.url
        item["ref"] = response.url.rsplit("-", 1)[1].strip("/")
        item["branch"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath("//ol/li[last()]//span/text()").get()
        item["state"] = response.xpath("//ol/li[2]//a/text()").get().upper()
        item["addr_full"] = (
            response.xpath("//title/text()").get().split(" | ", 1)[0].removeprefix("EVgo EV Charging Station in ")
        )
        item["extras"]["capacity"] = (
            response.xpath('//div[contains(@title, " stalls at this location")]/@title')
            .get()
            .removesuffix(" stalls at this location")
        )

        extract_google_position(item, response)

        apply_category(Categories.CHARGING_STATION, item)

        yield item
