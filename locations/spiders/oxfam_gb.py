from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.geo import city_locations
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class OxfamGBSpider(JSONBlobSpider):
    name = "oxfam_gb"
    item_attributes = {"brand": "Oxfam", "brand_wikidata": "Q267941"}
    locations_key = "results"
    brands = {
        "oxfam-shop-": ({"brand": "Oxfam", "brand_wikidata": "Q267941"}, Categories.SHOP_CHARITY),
        "oxfam-bookshop-": ({"brand": "Oxfam Bookshop", "brand_wikidata": "Q7115196"}, Categories.SHOP_BOOKS),
        "oxfam-books-music-": ({"brand": "Oxfam Books & Music", "brand_wikidata": "Q117838013"}, Categories.SHOP_MUSIC),
        # oxfam-boutique- (4)
        # oxfam-emporium- (1)
        # oxfam-festivals-shop (1)
        # oxfam-furniture-shop- (1)
        # oxfam-homeware- (2)
        # oxfam-music-audio- (1)
        # oxfam-music-shop- (4)
        # oxfam-online-hub- (2)
        # oxfam-original- (2)
        # oxfam-superstore- (1)
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("GB", 15000):
            yield JsonRequest(url=f'https://www.oxfam.org.uk/api/locations/?query={city["name"]}')

    def pre_process_data(self, feature: dict) -> None:
        if feature.get("shop"):
            for key, value in feature["shop"].items():
                feature[key] = value
            if feature.get("phone_number"):
                feature["phone_number"] = feature["phone_number"]["international"]
        elif feature.get("donationpoint"):
            for key, value in feature["donationpoint"].items():
                feature[key] = value

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines(
            [feature.get("address_line_1"), feature.get("address_line_2"), feature.get("address_line_3")]
        )
        if feature.get("shop"):
            item["website"] = feature["detail_url"]
            for url, (brand, category) in self.brands.items():
                if url in item["website"]:
                    item["branch"] = item.pop("name").removeprefix(brand["brand"]).removeprefix(" Shop").strip()
                    item.update(brand)
                    apply_category(category, item)
                    break
            else:
                apply_category(Categories.SHOP_CHARITY, item)
        elif feature.get("donationpoint"):
            if "Book Bank" in feature["name"]:
                apply_category(Categories.RECYCLING, item)
                apply_yes_no("recycling:books", item, True)
            elif "Clothing Bank" in feature["name"]:
                apply_category(Categories.RECYCLING, item)
                apply_yes_no("recycling:clothes", item, True)

        yield item
