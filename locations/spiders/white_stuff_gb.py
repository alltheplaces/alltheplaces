from typing import Iterable

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class WhiteStuffGBSpider(StoremapperSpider):
    name = "white_stuff_gb"
    item_attributes = {
        "brand": "White Stuff",
        "brand_wikidata": "Q7995442",
    }
    company_id = "20836-m3FhjqnTuGYyahve"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        # Other ones are just stockists
        if location.get("custom_field_1") != "White Stuff shop":
            return

        item["branch"] = item.pop("name").removeprefix("White Stuff ")

        item["opening_hours"] = OpeningHours()
        hours_text = (
            Selector(text=location.get("description", ""))
            .xpath('//div[@class="storemapper-description-workinghours"]//text()')
            .getall()
        )
        item["opening_hours"].add_ranges_from_string(" ".join(hours_text))

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
