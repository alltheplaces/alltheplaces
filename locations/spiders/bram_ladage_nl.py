import re
from typing import Iterable
from urllib.parse import unquote

from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import CLOSED_NL, DAYS_NL, OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.pipelines.address_clean_up import merge_address_lines


class BramLadageNLSpider(Spider):
    name = "bram_ladage_nl"
    item_attributes = {"brand": "Bram Ladage", "brand_wikidata": "Q2216467"}
    start_urls = ["https://bramladage.nl/bestellen/"]

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Feature | Request]:
        for location in response.css(".exp-store-locator__item.card[data-lat]"):
            item = Feature()
            item["branch"] = location.css(".exp-store-locator__item-title::text").get().strip()
            item["ref"] = item["branch"]
            item["lat"] = location.attrib["data-lat"]
            item["lon"] = location.attrib["data-lng"]
            item["street_address"] = merge_address_lines(
                location.css(".exp-store-locator__item-address::text").getall()
            )
            if route := location.css(".exp-store-locator__item-route::attr(href)").get():
                if postcode := re.search(r",\s*(\d{4}\s?[A-Z]{2})$", unquote(route).strip()):
                    item["postcode"] = postcode.group(1)

            for link in location.css(".exp-store-locator__item-buttons a::attr(href)").getall():
                if ".bramladage.nl" in link:
                    item["website"] = link.strip().split("?")[0].split("#")[0]
                    break
            for link in location.css(".exp-store-locator__item-social a::attr(href)").getall():
                if "facebook.com" in link:
                    item["facebook"] = link.split("?")[0]

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                " ".join(location.css(".exp-store-locator__item-hours-list li ::text").getall()),
                days=DAYS_NL,
                closed=CLOSED_NL,
            )

            apply_yes_no(Extras.DELIVERY, item, location.attrib.get("data-delivery") == "1")
            apply_category(Categories.FAST_FOOD, item)

            if item.get("website"):
                # The branch's ordering site has city and phone; its hours are online ordering hours, so not used
                yield Request(
                    item["website"],
                    callback=self.parse_ordering_site,
                    errback=self.ordering_site_failed,
                    cb_kwargs={"item": item},
                )
            else:
                yield item

    def parse_ordering_site(self, response: TextResponse, item: Feature) -> Iterable[Feature]:
        if ld := LinkedDataParser.find_linked_data(response, "Restaurant"):
            item["city"] = ld.get("address", {}).get("addressLocality")
            item["phone"] = ld.get("telephone")
        yield item

    def ordering_site_failed(self, failure) -> Iterable[Feature]:
        yield failure.request.cb_kwargs["item"]
