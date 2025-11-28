from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class OportoAUSpider(Spider):
    name = "oporto_au"
    item_attributes = {"brand": "Oporto", "brand_wikidata": "Q4412342"}
    start_urls = ["https://d3c377j0gjsips.cloudfront.net/opo_all_store_sync.json?t=202508131411"]

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location["attributes"])
            item["ref"] = location["id"]
            item["branch"] = item.pop("name")
            if location["relationships"].get("storeAddress"):
                address = location["relationships"]["storeAddress"]["data"]["attributes"]["addressComponents"]
                if address["floor"]["value"]:
                    item["extras"].update({"addr:floor": address["floor"]["value"]})
                item["housenumber"] = " / ".join(
                    filter(None, [address["unit"]["value"], address["streetNumber"]["value"]])
                )
                item["street_address"] = address["streetName"]["value"]
                item["city"] = address["suburb"]["value"]
                item["state"] = address["state"]["value"]
                item["country"] = address["country"]["longValue"]
                item["postcode"] = address["postcode"]["value"]
                item["lat"] = address["latitude"]["value"]
                item["lon"] = address["longitude"]["value"]
            item["phone"] = location["attributes"]["storePhone"]
            item["website"] = "https://www.oporto.com.au/locations/" + item["branch"].lower().replace(" ", "-")

            extra_features = [
                k for k, v in location["relationships"]["amenities"]["data"]["attributes"].items() if v is True
            ]
            apply_yes_no(Extras.TOILETS, item, "haveToilet" in extra_features, False)
            apply_yes_no(Extras.WIFI, item, "haveWifi" in extra_features, False)
            if location["relationships"].get("collection"):
                item["opening_hours"] = OpeningHours()
                opening_hours = location["relationships"]["collection"]["data"]["attributes"]["collectionTimes"]
                for day_hours in opening_hours:
                    day_name = day_hours["dayOfWeek"]
                    for day_hours_period in day_hours["collectionTimePeriods"]:
                        open_time = day_hours_period["openTime"]
                        close_time = day_hours_period["closeTime"]
                        item["opening_hours"].add_range(day_name, open_time, close_time, "%H:%M:%S")
            yield item
