import json
import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

POSTCODE_CITY_RE = re.compile(r"^(\d{5})\s+(.+)$")


class DerDeutschesReisebueroDESpider(Spider):
    name = "der_deutsches_reisebuero_de"
    item_attributes = {"name": "Dertour Reisebüro", "brand": "Dertour Reisebüro", "brand_wikidata": "Q56729186"}
    allowed_domains = ["www.dertour-reisebuero.de"]
    # robots.txt disallows /wp-admin/ (except admin-ajax.php) and
    # /*blackhole, neither of which affects the wp-json listing below.

    # This site is shared by two distinct franchise networks under the same
    # WordPress "Reisebüros" post type: "DERTOUR Reisebüro" (this brand,
    # Q56729186) and "DERPART Reisebüro" (a separate cooperative brand,
    # Q1200317). Only pages headlined "DERTOUR Reisebüro" are kept.
    brand_prefix = "DERTOUR Reisebüro"

    def make_listing_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.dertour-reisebuero.de/wp-json/wp/v2/reisebuero?per_page=100&page={page}&_fields=id,link",
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_listing_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        agencies = response.json()

        for agency in agencies:
            yield Request(agency["link"], callback=self.parse_agency, meta={"ref": agency["id"]})

        if len(agencies) == 100:
            yield self.make_listing_request(response.meta["page"] + 1)

    def parse_agency(self, response: Response) -> Any:
        headline = response.xpath('//div[@class="agency-info"]//h1[@class="headline"]/text()').get("").strip()
        if not headline.startswith(self.brand_prefix):
            # Skip DERPART Reisebüro (and any other) locations sharing this site.
            return

        # The 3 sub-divs (street, an optional address2 note, postcode+city)
        # are always present, but an empty address2 renders as an empty
        # <div></div> with no text node, so select on the divs themselves
        # rather than their text() to keep a stable 3-element result.
        address_divs = response.xpath('//div[@class="address"]/div/div')
        if len(address_divs) != 3:
            return
        street, address2, postcode_city = [div.xpath("string()").get("").strip() for div in address_divs]

        item = Feature()
        item["ref"] = response.meta["ref"]
        item["website"] = response.url
        item["branch"] = headline.removeprefix(self.brand_prefix).strip()
        item["street_address"] = merge_address_lines([street, address2])
        if m := POSTCODE_CITY_RE.match(postcode_city):
            item["postcode"], item["city"] = m.group(1), m.group(2)
        item["phone"] = response.xpath('//div[@class="phone"]//text()').getall()[-1].strip()
        if email := response.xpath('//div[@class="email"]//text()').getall():
            item["email"] = email[-1].strip()

        extract_google_position(item, response)

        if container := response.xpath("//opening-hour-container"):
            # Rendered as a Vue.js v-bind attribute, so its name is literally
            # ":opening-hours-parsed" (with the leading colon) in the HTML.
            if hours_raw := container[0].attrib.get(":opening-hours-parsed"):
                item["opening_hours"] = self.parse_opening_hours(hours_raw)

        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)

        yield item

    def parse_opening_hours(self, hours_raw: str) -> OpeningHours:
        oh = OpeningHours()
        for day, ranges in json.loads(hours_raw).items():
            for time_range in ranges:
                oh.add_range(day, time_range["from"], time_range["to"])
        return oh
