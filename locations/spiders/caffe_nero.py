from scrapy import Request, Spider

from locations.categories import apply_yes_no, Extras
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS_EN


class CaffeNeroSpider(Spider):
    name = "caffe_nero"
    item_attributes = {"brand": "Caffe Nero", "brand_wikidata": "Q675808"}
    start_urls = ["https://caffenero.com/us/stores/"]

    def parse(self, response, **kwargs):
        for region in response.xpath("//link[@rel='alternate'][starts-with(@hreflang, 'en-')]/@hreflang").getall():
            country_code = region.split('-')[1].lower()
            yield Request(url=f"https://caffenerowebsite.blob.core.windows.net/production/data/stores/stores-{country_code}.json", callback=self.parse_country)

    def parse_country(self, response):
        geojson = response.json()
        for location in geojson["features"]:
            item = DictParser.parse(location["properties"])

            lon, lat = location["geometry"]["coordinates"]
            item["lat"] = lat
            item["lon"] = lon

            amenities = location["properties"]["amenities"]
            apply_yes_no(Extras.TOILETS, item, amenities["toilet"])
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, amenities["disabled_toilet"])
            apply_yes_no(Extras.AIR_CONDITIONING, item, amenities["air_conditioned"])
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, amenities["baby_change"])
            apply_yes_no(Extras.OUTDOOR_SEATING, item, amenities["outside_seating"])
            apply_yes_no(Extras.SMOKING_AREA, item, amenities["smoking_area"])
            apply_yes_no(Extras.WHEELCHAIR, item, amenities["disabled_access"])
            apply_yes_no(Extras.WIFI, item, amenities["wifi"])

            opening_days = location["properties"]["hoursRegular"]
            item["opening_hours"] = OpeningHours()
            for day, day_details in opening_days.items():
                day = day.capitalize()
                if day not in DAYS_EN:
                    continue
                item["opening_hours"].add_range(DAYS_EN.get(day), day_details["open"], day_details["close"])

            yield item
