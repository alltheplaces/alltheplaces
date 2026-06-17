from json import loads
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.rio_seo import RioSeoSpider


class LevisSpider(RioSeoSpider):
    name = "levis"
    end_point = "https://maps.levi.com"

    def parse(self, response, **kwargs) -> Iterable[Feature]:
        # Overriding this method from RioSeoSpider because the source data contains
        # unescaped control characters that cause a JSONDecodeError in the standard parser.
        map_list = response.json().get("maplist", "")
        if not map_list:
            return

        map_list = map_list.removeprefix('<div class="tlsmap_list">').removesuffix(",</div>").replace("\t", " ")

        # fix for the JSONDecodeError: strict=False ignores literal tabs/newlines
        for location in loads(f"[{map_list}]", strict=False):
            item = DictParser.parse(location)

            item["ref"] = location["fid"]
            item["street_address"] = merge_address_lines([location["address_1"], location["address_2"]])
            item["phone"] = location["local_phone"]
            item["image"] = location.get("location_image")
            item["located_in"] = location.get("shopping_center_name", location.get("location_shopping_center"))
            item["extras"]["start_date"] = location.get("opening_date", location.get("grand_opening_date"))

            if hours := location.get("hours_sets:primary"):
                item["opening_hours"] = self.parse_hours(hours)

            if location.get("location_closure_message"):
                set_closed(item)

            yield from self.post_process_feature(item, location)

    def post_process_feature(self, item, location):
        apply_category(Categories.SHOP_CLOTHES, item)
        if item["name"].startswith("Dockers® "):
            item["brand"] = "Dockers"
            item["brand_wikidata"] = "Q538792"
        else:
            item["brand"] = "Levi's"
            item["brand_wikidata"] = "Q127962"

        item["branch"] = (
            item["name"].removeprefix(item["brand"]).removeprefix("® ").removeprefix("Factory ").removeprefix("Outlet ")
        )

        if location["Store Type_CS"] == "Levi's® Outlet":
            item["name"] = item["brand"] + " Outlet"
        else:
            item["name"] = item["brand"]

        if item.get("image") and "levis-banner.png" in item["image"]:
            # Generic brand image used instead of image of individual store.
            item.pop("image")

        yield item
