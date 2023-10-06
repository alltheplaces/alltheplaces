from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

DAYS_LOWER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class SunglassHut2Spider(Spider):
    name = "sunglass_hut_2"
    allowed_domains = [
        "mena.sunglasshut.com",
        "nl.sunglasshut.com",
        "pt.sunglasshut.com",
        "tr.sunglasshut.com",
        "hk.sunglasshut.com",
    ]

    item_attributes = {"brand": "Sunglass Hut", "brand_wikidata": "Q136311"}

    start_urls = [
        "https://mena.sunglasshut.com/api/content/render/false/limit/9999/type/json/query/+contentType:SghStoreLocator%20+languageId:11%20+deleted:false%20+working:true/orderby/modDate%20desc",
        "https://nl.sunglasshut.com/api/content/render/false/limit/9999/type/json/query/+contentType:SghStoreLocator%20+languageId:3%20+deleted:false%20+working:true/orderby/modDate%20desc",
        "https://pt.sunglasshut.com/api/content/render/false/limit/9999/type/json/query/+contentType:SghStoreLocator%20+languageId:4%20+deleted:false%20+working:true/orderby/modDate%20desc",
        "https://tr.sunglasshut.com/api/content/render/false/limit/9999/type/json/query/+contentType:SghStoreLocator%20+languageId:4%20+deleted:false%20+working:true/orderby/modDate%20desc",
        "https://hk.sunglasshut.com/api/content/render/false/limit/9999/type/json/query/+contentType:SghStoreLocator%20+languageId:8%20+deleted:false%20+working:true/orderby/modDate%20desc",
    ]

    def parse(self, response):
        for data in response.json()["contentlets"]:
            item = DictParser.parse(data)

            item["country"] = data["innerCountry"] if data["innerCountry"] else None

            item["lat"] = data["geographicCoordinatesLatitude"]
            item["lon"] = data["geographicCoordinatesLongitude"]
            item["geometry"] = {"coordinates": [item["lat"], item["lon"]], "type": "Point"}

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                "\n".join([f"{day} {data[day]}" for day in DAYS_LOWER]), delimiters=[" : "]
            )
            item["opening_hours"] = item["opening_hours"].as_opening_hours()

            yield item
