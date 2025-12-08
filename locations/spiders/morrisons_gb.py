import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.central_england_cooperative import set_operator


class MorrisonsGBSpider(Spider):
    name = "morrisons_gb"
    allowed_domains = ["api.morrisons.com"]
    start_urls = ["https://api.morrisons.com/location/v2/stores?apikey=kxBdM2chFwZjNvG2PwnSn3sj6C53dLEY&limit=20000"]

    MCCOLLS = {"brand": "McColl's", "brand_wikidata": "Q16997477"}
    MARTINS = {"brand": "Martin's", "brand_wikidata": "Q116779207"}
    RS_MCCOLL = {"brand": "RS McColl", "brand_wikidata": "Q7277785"}
    MORRISONS = {"brand": "Morrisons", "brand_wikidata": "Q922344"}
    MORRISONS_DAILY = {"brand": "Morrisons Daily", "brand_wikidata": "Q99752411"}
    MORRISONS_SELECT = {"brand": "Morrisons Select", "brand_wikidata": "Q105221633"}

    def create_slug(self, name: str) -> str:
        a = "àáäâãåăæąçćčđďèéěėëêęğǵḧìíïîįłḿǹńňñòóöôœøṕŕřßşśšșťțùúüûǘůűūųẃẍÿýźžż·/_,:;"
        b = "aaaaaaaaacccddeeeeeeegghiiiiilmnnnnooooooprrsssssttuuuuuuuuuwxyyzzz------"

        slug = re.sub(r"\s+", "-", name.lower())

        for old, new in zip(a, b):
            slug = slug.replace(old, new)

        slug = slug.replace("&", "-and-")
        slug = re.sub(r"[^\w\-]+", "", slug)
        slug = re.sub(r"\-\-+", "-", slug)
        slug = slug.strip("-")

        return slug

    def parse(self, response):
        for location in response.json()["stores"]:
            location["id"] = str(location.pop("name"))
            item = DictParser.parse(location)
            item["street_address"] = clean_address(
                [location["address"].get("addressLine1"), location["address"].get("addressLine2")]
            )
            item["website"] = "https://my.morrisons.com/storefinder/{}/{}".format(
                item["ref"], self.create_slug(location["storeName"])
            )

            item["opening_hours"] = OpeningHours()
            for day_abbrev, day_hours in location["openingTimes"].items():
                item["opening_hours"].add_range(day_abbrev, day_hours["open"], day_hours["close"], "%H:%M:%S")

            if location["storeFormat"] == "supermarket" and location["category"] == "Supermarket":
                item.update(self.MORRISONS)
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif location["storeFormat"] == "supermarket" and location["category"] == "McColls":
                if "Morrisons Daily" in location["storeName"]:
                    item.update(self.MORRISONS_DAILY)
                elif "McColl's" in location["storeName"]:
                    item.update(self.MCCOLLS)
                elif "Rs Mccoll" in location["storeName"]:
                    item.update(self.RS_MCCOLL)
                elif "Martin's" in location["storeName"]:
                    item.update(self.MARTINS)
                apply_category(Categories.SHOP_CONVENIENCE, item)
                set_operator(self.MCCOLLS, item)
            elif location["storeFormat"] == "supermarket" and location["category"] == "Gas Station":
                if "Morrisons Daily" in location["storeName"]:
                    item.update(self.MORRISONS_DAILY)
                elif "Morrisons Select" in location["storeName"]:
                    item.update(self.MORRISONS_SELECT)
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif location["storeFormat"] == "pfs" and location["category"] == "Gas Station":
                item.update(self.MORRISONS)
                apply_category(Categories.FUEL_STATION, item)

            if not item.get("brand"):
                continue
            item["branch"] = item.pop("name", None)
            yield item
