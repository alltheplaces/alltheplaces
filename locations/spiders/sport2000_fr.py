from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.algolia import AlgoliaSpider


class Sport2000FRSpider(AlgoliaSpider):
    name = "sport2000_fr"
    item_attributes = {"brand": "Sport 2000", "brand_wikidata": "Q262394", "extras": Categories.SHOP_SPORTS.value}
    api_key = "f173a66037574432c7fedd51e22e7715"
    app_id = "604535R4DX"
    index_name = "stores"

    channels = {
        "SPORT 2000": {
            "category": Categories.SHOP_SPORTS,
            "brand": "Sport 2000",
            "brand_wikidata": "Q262394",
        },
        "DEGRIF'SPORT": {
            "category": Categories.SHOP_SPORTS,
            "brand": "Degrif Sport",
            "brand_wikidata": "Q130288375",
        },
        "ESPACE MONTAGNE": {
            "category": Categories.SHOP_OUTDOOR,
            "brand": "Espace Montagne",
            "brand_wikidata": "Q130221137",
        },
        "MONDOVELO": {
            "category": Categories.SHOP_BICYCLE,
            "brand": "Mondovélo",
            "brand_wikidata": "Q130216213",
        },
        "PROSPORT": {
            "category": Categories.SHOP_SPORTS,
            "brand": "ProSport",
            "brand_wikidata": "Q130288466",
        },
        "S2 SNEAKERS SPECIALIST": {
            "category": Categories.SHOP_SHOES,
            "brand": "S2 Sneakers Specialist",
            "brand_wikidata": "Q130288490",
        },
        "WAS WE ARE SELECT": {
            "category": Categories.SHOP_CLOTHES,
            "brand": "We Are Select",
            "brand_wikidata": "Q130293185",
        },
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        channel = feature["channels"][0]
        if channel in self.channels:
            channel_def = self.channels[channel]
            apply_category(channel_def["category"], item)
            item["brand"] = channel_def["brand"]
            item["brand_wikidata"] = channel_def["brand_wikidata"]
        else:
            raise KeyError(f'Unknown channel "{channel}". Please extend the scraper')
        item["street_address"] = feature.pop("address").title()
        item["city"] = feature["city"].title()
        item["addr_full"] = f"{item['street_address']}, {item['postcode']} {item['city']}"
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["website"] = f"https://www.sport2000.fr{feature['link']}"
        item["opening_hours"] = self.extract_opening_hours(feature)
        yield item

    @staticmethod
    def extract_opening_hours(feature: dict) -> OpeningHours:
        if hours := feature.get("opening_periods"):
            oh = OpeningHours()
            for index, day in enumerate(DAYS):
                for period in hours.get(str(index + 1), []):
                    oh.add_range(day, period["opening_time"], period["closing_time"])
            return oh
