from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


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
            region = response.url.split("https://", 1)[1].split(".", 1)[0].lower()

            if data["innerCountry"]:
                item["country"] = data["innerCountry"]
            else:
                item["country"] = region.upper()
                item["country"] = None if (item["country"] == "MENA") else item["country"]

            item["ref"] = f"{region}-{data['seoUrl']}"

            item["website"] = "https://{}.sunglasshut.com/{}/store-locator/{}".format(
                region, ("en" if region == "mena" else region), data["seoUrl"]
            )

            item["lat"] = data["geographicCoordinatesLatitude"]
            item["lon"] = data["geographicCoordinatesLongitude"]

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                " ".join(["{}: {}".format(day, data[day.lower()]) for day in DAYS_FULL]), delimiters=[" : "]
            )

            yield item
