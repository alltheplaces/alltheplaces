from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class TruworthsSpider(Spider):
    name = "truworths"
    start_urls = ["https://www.identity.co.za/ccstore/v1/assembler/pages/Default/storeSearch?Nr=AND(product.active:1)"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    BRANDS = {
        "Truworths": {"brand": "Truworths", "brand_wikidata": "Q24233998"},
        "Identity": {"brand": "Identity", "brand_wikidata": "Q116378109"},
        "Loads of Living": {"brand": "Loads of Living", "brand_wikidata": "Q116418933"},
        "Office London": {"brand": "Office London", "brand_wikidata": "Q116418894"},
    }

    def parse(self, response, **kwargs):
        for location in response.json()["resultsList"]["records"]:
            clean_location = {}
            for key, value in location["attributes"].items():
                clean_location[key.replace("store.", "")] = value[0]
            clean_location["street_address"] = clean_address(
                [clean_location.pop("address1", ""), clean_location.pop("address2", "")]
            )
            clean_location["lat"], clean_location["lon"] = clean_location.pop("geocode", ",").split(",")

            item = DictParser.parse(clean_location)

            if brand := self.BRANDS.get(clean_location["companyName"]):
                item.update(brand)

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item

        if offset := response.json()["resultsList"].get("lastRecNum"):
            yield response.follow(
                response.json()["resultsList"]["pagingActionTemplate"]["link"]
                .replace("%7Boffset%7D", str(offset))
                .replace("%7BrecordsPerPage%7D", str(response.json()["resultsList"]["recsPerPage"]))
            )
