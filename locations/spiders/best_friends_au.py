from locations.categories import Categories, apply_category
from locations.storefinders.storerocket import StoreRocketSpider

BEST_FRIENDS = {"brand": "Best Friends", "brand_wikidata": "Q106540748"}
OUR_VET = {"brand": "Our Vet", "brand_wikidata": "Q128912575"}


class BestFriendsAUSpider(StoreRocketSpider):
    name = "best_friends_au"
    storerocket_id = "aDJkAN6pOd"

    def parse_item(self, item, location):
        if location["name"].startswith("Best Friends Pets "):
            item["brand"] = BEST_FRIENDS["brand"]
            item["brand_wikidata"] = BEST_FRIENDS["brand_wikidata"]
            apply_category(Categories.SHOP_PET, item)
            item["branch"] = item.pop("name").removeprefix("Best Friends Pets ")
            item["website"] = "https://bestfriendspets.com.au/pages/store-locator/" + item["branch"].lower().replace(
                " ", "-"
            )
            item["email"] = location["city"].lower().replace(" ", "") + "@bfpets.com.au"
        elif location["name"].startswith("Our Vet "):
            item["brand"] = OUR_VET["brand"]
            item["brand_wikidata"] = OUR_VET["brand_wikidata"]
            apply_category(Categories.VETERINARY, item)
            item["branch"] = item.pop("name").removeprefix("Our Vet ")
            item["website"] = "https://www.ourvet.com.au/our-locations?location=" + location["slug"]
        yield item
