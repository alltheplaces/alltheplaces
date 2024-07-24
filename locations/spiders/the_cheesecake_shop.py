from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media


class TheCheesecakeShopSpider(Spider):
    name = "the_cheesecake_shop"
    item_attributes = {"brand": "The Cheesecake Shop", "brand_wikidata": "Q117717103"}
    allowed_domains = ["www.cheesecake.com.au", "www.thecheesecakeshop.co.nz"]
    start_urls = [
        "https://www.cheesecake.com.au/sync/ajax/stores",
        "https://www.thecheesecakeshop.co.nz/sync/ajax/stores",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    store_list = {}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_store_list)

    def parse_store_list(self, response):
        if ".com.au" in response.url:
            country = "AU"
        elif ".co.nz" in response.url:
            country = "NZ"
        for location in response.json():
            store = {}
            store["country"] = country
            store["postcode"] = location["value"].split(",")[-1].strip()
            self.store_list[location["store_sys_id"]] = store
        yield from self.search_by_postcode(country, response.json()[0]["value"].split(",")[-1].strip())

    def search_by_postcode(self, country, postcode):
        if country == "AU":
            yield JsonRequest(
                url=f"https://www.cheesecake.com.au/postcodes/ajax/suggest/?term={postcode}&select=1",
                meta={"postcode": postcode},
            )
        elif country == "NZ":
            yield JsonRequest(
                url=f"https://www.thecheesecakeshop.co.nz/postcodes/ajax/suggest/?term={postcode}&select=1",
                meta={"postcode": postcode},
            )

    def parse(self, response):
        if len(response.text) > 0:
            for store in response.json():
                if store["store_sys_id"] not in self.store_list.keys():
                    continue
                self.store_list.pop(store["store_sys_id"])
                item = DictParser.parse(store)
                item["ref"] = store["store_sys_id"]
                item["addr_full"] = store["address"]
                item["state"] = item["state"].strip()
                item["postcode"] = item["postcode"].strip()
                item["phone"] = store.get("store_phone")
                item["email"] = store.get("store_email")
                set_social_media(item, SocialMedia.FACEBOOK, store.get("store_facebook"))
                set_social_media(item, SocialMedia.INSTAGRAM, store.get("store_instagram"))
                if ".com.au" in response.url:
                    item["website"] = "https://www.cheesecake.com.au/find-bakery/" + store["store_identifier"] + "/"
                elif ".co.nz" in response.url:
                    item["website"] = (
                        "https://www.thecheesecakeshop.co.nz/find-bakery/" + store["store_identifier"] + "/"
                    )
                hours_text = ""
                for day_abbrev in ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]:
                    hours_text = f"{hours_text} {day_abbrev}: " + store[f"store_{day_abbrev}_open"]
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_text)
                yield item

        defunct_stores_list = [
            store_sys_id
            for store_sys_id, store in self.store_list.items()
            if store["postcode"] == response.meta["postcode"]
        ]
        for defunct_store in defunct_stores_list:
            self.store_list.pop(defunct_store)

        if len(self.store_list) > 0:
            next_store = list(self.store_list.values())[0]
            yield from self.search_by_postcode(next_store["country"], next_store["postcode"])
