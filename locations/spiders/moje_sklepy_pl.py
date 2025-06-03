from typing import Iterable

from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MojeSklepyPLSpider(JSONBlobSpider):
    name = "moje_sklepy_pl"
    allowed_domains = ["mojesklepy.pl", "prod-www-api-iph.mojpos.pl"]
    start_urls = ["https://prod-www-api-iph.mojpos.pl/api/v2/shops/map"]
    locations_key = "shops"
    brands = {
        "abc": ("abc", "Q11683985"),
        "eurosklep": ("Euro Sklep", "Q11702591"),
        "groszek": ("Groszek", "Q9280965"),
    }

    def start_requests(self) -> Iterable[Request]:
        yield Request(url="https://mojesklepy.pl/wybierz-sklep/", callback=self.parse_auth_token)

    def parse_auth_token(self, response: Response) -> Iterable[JsonRequest]:
        js_blob = response.xpath('//script[contains(text(), "var mojeSklepySettings = ")]/text()').get()
        auth_token = js_blob.split('{"authToken":"', 1)[1].split('"', 1)[0]
        yield JsonRequest(url=self.start_urls[0], headers={"Authorization": f"Bearer {auth_token}"}, meta={"auth_token": auth_token})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[JsonRequest]:
        item["ref"] = str(feature["shopId"])
        if feature["brand"] in self.brands.keys():
            item["brand"] = self.brands[feature["brand"]][0]
            item["brand_wikidata"] = self.brands[feature["brand"]][1]
        elif feature["brand"] == "niezrzeszony": # "unaffiliated"
            # Ignore unbranded independent stores.
            return
        else:
            self.logger.warning("Unknown brand: {}".format(feature["brand"]))
        match feature["format"]:
            case "ExpressMarket" | "MiniMarket":
                apply_category(Categories.SHOP_SUPERMARKET, item)
            case "Market" | "Supermarket":
                apply_category(Categories.SHOP_CONVENIENCE, item)
            case _:
                self.logger.warning("Unknown feature type: {}".format(feature["format"]))

        shop_id = feature["shopId"]
        auth_token = response.meta["auth_token"]
        yield JsonRequest(url=f"https://prod-www-api-iph.mojpos.pl/api/v2/shops/{shop_id}", headers={"Authorization": f"Bearer {auth_token}"}, meta={"item": item}, callback=self.parse_extra_details)

    def parse_extra_details(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        if not response.json() or not response.json()["shop"]:
            # A bug in the brand's API/website where an icon appears on the
            # map but is unknown to the API as a feature with details such as
            # address, phone number and opening hours available?
            # Such features are probably best to skip.
            return
        feature = response.json()["shop"]

        if address_details := feature.get("address"):
            if isinstance(address_details, dict):
                item["street_address"] = address_details.get("street")
                item["city"] = address_details.get("city")
                item["postcode"] = address_details.get("postalCode")

        item["phone"] = feature.get("contactPhoneNumber")

        if hours_dict := feature.get("openHours"):
            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in hours_dict.items():
                if not day_hours.get("isOpen"):
                    item["opening_hours"].set_closed(day_name)
                elif not day_hours.get("timeFrom") or not day_hours.get("timeTo"):
                    # Many features are just stated to be open or closed on a
                    # given day without specifying opening hours. For many
                    # features, opening hours will just be extracted perhaps as
                    # simply as "Su closed".
                    continue
                else:
                    item["opening_hours"].add_range(day_name, day_hours["timeFrom"].split("T", 1)[1].removesuffix(":00"), day_hours["timeTo"].split("T", 1)[1].removesuffix(":00"))

        yield item
