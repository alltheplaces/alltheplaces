import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# The store locator is a table of company owned stores, each row linking to the
# store's page, where the hours are listed a day at a time.
#
# The table also carries the company's two offices in China and a row labelled
# "(DEALER)", which is an independent stockist rather than a Vista Paint store;
# both are skipped.
#
# No coordinates are published: the store pages embed a map built from the
# address text.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class VistaPaintUSSpider(Spider):
    name = "vista_paint_us"
    item_attributes = {"brand": "Vista Paint"}
    allowed_domains = ["www.vistapaint.com"]
    start_urls = ["https://www.vistapaint.com/stores/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for row in response.xpath("//table//tr"):
            cells = [
                re.sub(r"\s+", " ", " ".join(cell.xpath(".//text()").getall())).strip()
                for cell in row.xpath("./td")
            ]
            if len(cells) < 6:
                continue

            store_number, city, street, state, postcode, phone = cells[:6]
            # The offices in China have no store number and a province in place
            # of a state.
            if not re.fullmatch(r"[A-Z]{2}", state) or not re.fullmatch(r"\d{5}", postcode):
                continue
            # "Rimforest (DEALER)" is an independent stockist.
            if "dealer" in city.lower():
                continue

            item = Feature()
            item["ref"] = store_number
            item["branch"] = city
            item["street_address"] = street
            item["city"] = city
            item["state"] = state
            item["postcode"] = postcode
            item["phone"] = phone
            item["website"] = response.urljoin(row.xpath('.//a[contains(@href, "/stores/")]/@href').get(""))

            apply_category(Categories.SHOP_PAINT, item)

            if item["website"]:
                yield response.follow(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})
            else:
                yield item

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        oh = OpeningHours()

        for day_block in response.xpath('//div[contains(@class, "day ")]'):
            values = [
                value.strip()
                for value in day_block.xpath('.//span[contains(@class, "elementor-icon-list-text")]/text()').getall()
                if value.strip()
            ]
            if len(values) != 2 or not (day := DAYS_EN.get(values[0])):
                continue
            if times := re.fullmatch(r"(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)", values[1], re.I):
                oh.add_range(
                    day, times.group(1).replace(" ", "").upper(), times.group(2).replace(" ", "").upper(), "%I:%M%p"
                )

        if oh:
            item["opening_hours"] = oh

        yield item
