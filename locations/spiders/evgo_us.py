from typing import Any

from geonamescache import GeonamesCache
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class EvgoUSSpider(CrawlSpider):
    name = "evgo_us"
    item_attributes = {"brand": "EVgo", "brand_wikidata": "Q61803820"}
    start_urls = [
        "https://evgo.com/find-a-charger/{}/".format(state.lower()) for state in GeonamesCache().get_us_states().keys()
    ]
    rules = [Rule(LinkExtractor(r"/find-a-charger/\w\w/[^/]+/[^/]+\-(\d+)/?$"), "parse")]
    custom_settings = {"REDIRECT_ENABLED": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
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
