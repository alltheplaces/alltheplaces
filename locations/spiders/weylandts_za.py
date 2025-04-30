from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class WeylandtsZASpider(JSONBlobSpider):
    name = "weylandts_za"
    item_attributes = {
        "brand": "Weylandts",
        "brand_wikidata": "Q130459662",
    }
    start_urls = [
        "https://www.weylandts.co.za/graphql?query=query+storeLocations{storeLocations{items{name+status+address+link+region+city+image+show_in_storefront+__typename}__typename}}&operationName=storeLocations&variables={}"
    ]
    locations_key = ["data", "storeLocations", "items"]

    def post_process_item(self, item, response, location):
        item["ref"] = location["link"]
        item["website"] = "https://www.weylandts.co.za/" + item["ref"]
        if image := location.get("image"):
            item["image"] = "https://m2.weylandts.co.za/media/" + image
        item["branch"] = item.pop("name")
        if location["city"] == "Distribution Centers":
            item.pop("city")
            apply_category(Categories.INDUSTRIAL_WAREHOUSE, item)
        else:
            apply_category(Categories.SHOP_FURNITURE, item)
        url = (
            'https://www.weylandts.co.za/graphql?query=query+storeLocations($filter:StoreLocationFilterInput!){storeLocations(filter:$filter){items{name+status+address+latitude+longitude+email+phone+opening_hours{opens_at+closes_at+weekday+info_time+__typename}special_hours{date+label+opens_at+closes_at+__typename}recurring_hours{label+starts_at+ends_at+__typename}meta_title+meta_description+meta_keywords+image+description+__typename}__typename}}&operationName=storeLocations&variables={"filter":{"link":{"eq":"'
            + location["link"]
            + '"}}}'
        )
        yield JsonRequest(url=url, callback=self.parse_store, meta={"item": item})

    def parse_store(self, response):
        item = response.meta["item"]
        location = response.json()["data"]["storeLocations"]["items"][0]
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        item["email"] = location["email"]
        item["phone"] = location["phone"]

        item["opening_hours"] = OpeningHours()
        for day in location["opening_hours"]:
            if "closed" in day["info_time"]:
                item["opening_hours"].set_closed(day["weekday"])
            else:
                item["opening_hours"].add_range(day["weekday"], day["opens_at"], day["closes_at"])

        yield item
