from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider

ROCOMAMAS_COUNTRIES = {
    "BW",
    "CD",
    "GH",
    "KE",
    "IN",
    "NA",
    "SA",
    "SZ",
    "ZM",
    "ZA",
    "ZW",
}

ROCOMAMAS_BRANDS = {
    "ROCO": {"brand": "RocoMamas", "brand_wikidata": "Q123034964"},
    "ROCOGO": {"brand": "RocoGo", "brand_wikidata": "Q123034964"},
}

SOCIAL_MEDIA_MAP = {
    "Facebook": SocialMedia.FACEBOOK,
    "TripAdvisor": SocialMedia.TRIPADVISOR,
}


class RocomamasSpider(JSONBlobSpider):
    name = "rocomamas"
    start_urls = ["https://rocomamas.com/api/proxy"]

    def start_requests(self):
        for url in self.start_urls:
            for country in ROCOMAMAS_COUNTRIES:
                body_data = (
                    '{"url":"restaurants?brandKey=ROCO,ROCOGO&countryCode='
                    + country
                    + '&tradingStatus=Open&filterHidden=true&expand=channels","method":"GET"}'
                )
                yield JsonRequest(
                    url=url,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                    body=body_data,
                )

    def extract_json(self, response):
        return response.json()["res"]["data"]

    def pre_process_data(self, feature):
        feature["ref"] = feature.pop("key")
        if (alt_phone := feature.get("alternateTelephoneNumber")) is not None:
            feature["telephoneNumber"] = feature.get("telephoneNumber") + "; " + alt_phone
        if (alt_email := feature.get("alternateEmailAddress")) is not None:
            feature["emailAddress"] = feature.get("emailAddress") + "; " + alt_email

    def post_process_item(self, item, response, location):
        item.pop("name")

        if brand_details := ROCOMAMAS_BRANDS.get(location["brand"].get("key")):
            item.update(brand_details)
        else:
            self.crawler.stats.inc_value(f'atp/{self.name}/unknown_brand/{location["brand"].get("key")}')

        if item.get("state") == "International":
            item.pop("state")
        if item.get("postcode") in ["9000", "9999", "0000", "00000"]:
            item.pop("postcode")

        item["branch"] = location.get("displayName").replace(item.get("brand"), "").strip()
        item[
            "website"
        ] = f"https://rocomamas.com/{location['countryCode']}/restaurants/{location['province']}/{location['displayName']}".lower().replace(
            " ", "-"
        )

        apply_yes_no(Extras.KIDS_AREA, item, location.get("playArea"))
        apply_yes_no(Extras.WIFI, item, location.get("wireless"))
        apply_yes_no(Extras.HALAL, item, location.get("halaal"), False)
        apply_yes_no(Extras.SMOKING_AREA, item, location.get("smokingSection"))

        fulfilment = [i["name"] for i in location["fulfilmentChannels"]]
        apply_yes_no(Extras.TAKEAWAY, item, "Take-away" in fulfilment)
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in fulfilment)

        req_data = '{"url":"/restaurants/' + str(item["ref"]) + '?expand=all","method":"GET"}'
        yield JsonRequest(
            url="https://rocomamas.com/api/proxy",
            headers={"Content-Type": "application/json"},
            method="POST",
            body=req_data,
            meta={"item": item},
            callback=self.parse_store,
        )

    def parse_store(self, response):
        item = response.meta["item"]
        store_data = response.json()["res"]["data"]
        for url in store_data["urls"]:
            if service := SOCIAL_MEDIA_MAP.get(url["urlType"]):
                set_social_media(item, service, url["url"])
        item["opening_hours"] = OpeningHours()
        for day in store_data["tradingTimes"]:
            # They also provide public holidays and Christmas hours
            if day["tradingDay"] not in DAYS_FULL:
                continue
            if day["closed"]:
                item["opening_hours"].set_closed(day["tradingDay"])
            else:
                item["opening_hours"].add_range(
                    day["tradingDay"], day["openingTime"], day["closingTime"], time_format="%H:%M:%S"
                )
        yield item
