import pycountry
from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class TotalWineAndMoreUSSpider(Spider):
    name = "total_wine_and_more_us"
    item_attributes = {"brand": "Total Wine & More", "brand_wikidata": "Q7828084"}
    allowed_domains = ["www.totalwine.com"]
    start_urls = ["https://www.totalwine.com/registry/"]

    def start_requests(self):
        for url in self.start_urls:
            for state in pycountry.subdivisions.get(country_code="US"):
                formdata = {
                    "components[0][name]": "location-slideout-component",
                    "components[0][version]": "2.0.7",
                    "components[0][parameters][type]": "GET_STORES",
                    "components[0][parameters][query]": state.name,
                }
                yield FormRequest(
                    url=url, method="POST", headers={"Accept": "application/vnd.oc.unrendered+json"}, formdata=formdata
                )

    def parse(self, response):
        pagination = response.json()[0]["response"]["data"]["reactComponent"]["props"]["data"]["pagination"]
        if pagination["totalResults"] == 0:
            return

        for location in response.json()[0]["response"]["data"]["reactComponent"]["props"]["data"]["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["storeNumber"]
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            item["website"] = "https://www.totalwine.com/store-info/" + item["ref"]

            for social_account in location.get("socialMedia", []):
                if social_account["socialMediaType"] == "facebook":
                    item["facebook"] = social_account["url"]
                elif social_account["socialMediaType"] == "instagram":
                    item["extras"]["contact:instagram"] = social_account["url"]

            apply_yes_no(Extras.WIFI, item, location["wifiAvailable"], False)

            if location["storeHours"]["hasHours"]:
                item["opening_hours"] = OpeningHours()
                for day_hours in location["storeHours"]["days"]:
                    if day_hours["closedStatus"]:
                        continue
                    item["opening_hours"].add_range(
                        day_hours["dayOfWeek"].title(), day_hours["openingTime"], day_hours["closingTime"], "%I:%M %p"
                    )

            yield item
