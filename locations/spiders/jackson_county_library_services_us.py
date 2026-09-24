from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from scrapy.http import Request, Response, TextResponse
from twisted.python.failure import Failure

from locations.items import Feature
from locations.storefinders.lib_cal import LibCalSpider


class JacksonCountyLibraryServicesUSSpider(LibCalSpider):
    name = "jackson_county_library_services_us"
    item_attributes = {"operator": "Jackson County Library Services", "operator_wikidata": "Q69488445"}
    libcal_host = "jcls.libcal.com"
    libcal_iid = 3288

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs: Any
    ) -> Iterable[Request | Feature]:
        # The administration office shares the Medford library's address, and
        # a test entry has no URL.
        if item["name"] == "Office" or not item["website"]:
            return
        item["branch"] = item.pop("name")
        item["name"] = "{} Library".format(item["branch"])
        # LibCal's addresses have typos (e.g. "18484 North Applegate Road" for
        # 18485) and its map embeds are centred up to 3 km from the library,
        # so the branch page supplies the address and coordinates.
        yield Request(
            item["website"].replace("http://", "https://", 1),
            callback=self.parse_branch_page,
            errback=self.parse_branch_page_error,
            cb_kwargs={"item": item},
        )

    def parse_branch_page(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["website"] = response.url
        marker = response.css(".marker.libby-marker")
        item["lat"] = marker.xpath("@data-lat").get()
        item["lon"] = marker.xpath("@data-lng").get()
        item["phone"] = marker.css(".location-card__phone a::text").get()
        # The directions link holds the full address, e.g. "Phoenix Library,
        # 510 West 1st Street, Phoenix, OR 97535, USA", where the text on the
        # page leaves out the state and ZIP code for some branches.
        if directions := marker.xpath('.//a[contains(@href, "daddr=")]/@href').get():
            parts = parse_qs(urlparse(directions).query)["daddr"][0].removesuffix(", USA").split(", ")
            item["street_address"], item["city"] = parts[-3:-1]
            item["state"], _, postcode = parts[-1].partition(" ")
            item["postcode"] = postcode or None
        yield item

    def parse_branch_page_error(self, failure: Failure) -> Iterable[Feature]:
        request = failure.request  # ty: ignore[unresolved-attribute]
        self.logger.warning("Failed to fetch branch page %s: %r", request.url, failure.value)
        self.crawler.stats.inc_value(f"atp/{self.name}/branch_page_failed")
        yield request.cb_kwargs["item"]
