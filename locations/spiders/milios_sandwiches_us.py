from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

US_STATE_ABBREVIATIONS = {
    "Iowa": "IA",
    "Minnesota": "MN",
    "Wisconsin": "WI",
}


class MiliosSandwichesUSSpider(Spider):
    name = "milios_sandwiches_us"
    item_attributes = {"brand": "Milio's", "brand_wikidata": "Q6851893"}
    allowed_domains = ["milios.com"]
    # robots.txt disallows all query strings ("Disallow: /*?"), which would
    # otherwise block the paginated wp-json listing request below.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://milios.com/wp-json/wp/v2/location?per_page=100&page={page}",
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.json()

        for store in stores:
            yield Request(store["link"], callback=self.parse_store)

        if len(stores) == 100:
            yield self.make_request(response.meta["page"] + 1)

    def parse_store(self, response: Response) -> Any:
        # Phone number and address are published as plain text lines within
        # the first rich-text block that contains a "tel:" link.
        lines = [
            line.strip()
            for line in response.xpath(
                '(//div[contains(@class, "fl-module-rich-text")][.//a[starts-with(@href, "tel:")]])[1]//p//text()'
            ).getall()
            if line.strip()
        ]
        if len(lines) < 3:
            return

        phone, street_address, city_state_zip = lines[0], lines[1], lines[-1]
        city, state, postcode = [part.strip() for part in city_state_zip.split(",")]

        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = " ".join(response.css("h1.fl-heading ::text").getall()).strip()
        item["phone"] = phone
        item["street_address"] = street_address
        item["city"] = city
        item["state"] = US_STATE_ABBREVIATIONS.get(state, state)
        item["postcode"] = postcode
        item["image"] = response.css(".fl-module-photo img::attr(src)").get()

        # No coordinates are published anywhere on the page; the embedded
        # Google Maps iframe is a "place?q=<address>" query, not a
        # coordinate-based embed, so lat/lon is intentionally left blank.

        item["opening_hours"] = OpeningHours()
        hours_rows = response.xpath(
            '(//span[contains(@class, "fl-heading-text")]'
            '[normalize-space(text()) = "Store Hours"]'
            '/ancestor::div[contains(@class, "fl-module-heading")][1]'
            '/following-sibling::div[contains(@class, "fl-module-rich-text")][1])'
            "//table[contains(@class, 'restaurant-hours-table')]//tr"
        )
        for row in hours_rows:
            cells = row.css("td::text").getall()
            if len(cells) != 2:
                continue
            day, hours_range = cells[0].strip(), cells[1].strip()
            open_time, _, close_time = hours_range.partition(" - ")
            item["opening_hours"].add_range(day, open_time.strip(), close_time.strip(), time_format="%I:%M %p")

        apply_category(Categories.FAST_FOOD, item)

        yield item
