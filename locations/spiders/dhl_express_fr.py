from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.dhl_express_de import DHL_EXPRESS_SHARED_ATTRIBUTES


class DhlExpressFRSpider(Spider):
    name = "dhl_express_fr"
    item_attributes = DHL_EXPRESS_SHARED_ATTRIBUTES
    allowed_domains = ["wsbexpress.dhl.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[JsonRequest]:
        # Fifty closest shops are returned no matter their distance from the
        # supplied centroid. Small search radius (24km) required to find the
        # maximum number of features.
        for lat, lon in country_iseadgg_centroids(["FR"], 24):
            url = f"https://wsbexpress.dhl.com/ServicePointLocator/restV3/servicepoints?servicePointResults=1000000&address={lat},{lon}&countryCode=FR&weightUom=lb&dimensionsUom=in&languageScriptCode=Latn&language=eng&resultUom=mi&b64=true&key=963d867f-48b8-4f36-823d-88f311d9f6ef"
            yield JsonRequest(url=url)

    def parse(self, response: Response) -> Iterable[Feature]:
        features = response.json().get("servicePoints")
        if not features:
            return

        if len(features) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(features))

        for feature in features:
            if feature.get("servicePointType") == "STATION":
                item = DictParser.parse(feature.get("address"))

                item["ref"] = feature.get("facilityId")
                item["name"] = feature.get("localName")
                item["lat"] = feature.get("geoLocation", {}).get("latitude")
                item["lon"] = feature.get("geoLocation", {}).get("longitude")
                item["phone"] = feature.get("contactDetails", {}).get("phoneNumber")
                item["website"] = feature.get("contactDetails", {}).get("linkUri")

                item["opening_hours"] = OpeningHours()
                for day in feature.get("openingHours", {}).get("openingHours"):
                    item["opening_hours"].add_range(
                        day=day.get("dayOfWeek"), open_time=day.get("openingTime"), close_time=day.get("closingTime")
                    )

                apply_category(Categories.POST_OFFICE, item)

                yield item
