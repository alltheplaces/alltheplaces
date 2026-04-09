from typing import Iterable

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class LoroITSpider(WpGoMapsSpider):
    name = "loro_it"
    item_attributes = {"brand": "Loro", "brand_wikidata": "Q131832194"}
    allowed_domains = ["www.loro.it"]

    def post_process_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        description = Selector(text=location["description"])
        item["name"] = description.xpath("//text()[1]").get()
        item["addr_full"] = description.xpath("//text()[2]").get()
        if phone := description.xpath("//text()[3]").get():
            item["phone"] = phone.removeprefix("T. ")
        apply_category(Categories.FUEL_STATION, item)
        yield item
