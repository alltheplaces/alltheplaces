import scrapy

from locations.items import GeojsonPointItem
from locations.linked_data_parser import LinkedDataParser


class EdwardJonesSpider(scrapy.Spider):
    name = "edwardjones"
    item_attributes = {"brand": "Edward Jones", "brand_wikidata": "Q5343830"}
    allowed_domains = ["www.edwardjones.com"]

    def get_page(self, n):
        return scrapy.Request(
            f"https://www.edwardjones.com/api/v2/financial-advisor/results?q=57717&distance=75000&distance_unit=mi&page={n}",
            meta={"page": n},
        )

    def start_requests(self):
        yield self.get_page(1)

    def parse(self, response):
        data = response.json()["results"]
        if data == []:
            return
        for row in data:
            url = "https://www.edwardjones.com" + row["faUrl"]
            meta = {
                "lat": row["lat"],
                "lon": row["lon"],
            }
            yield scrapy.Request(url, callback=self.parse_location, meta=meta)
        yield self.get_page(1 + response.meta["page"])

    def parse_location(self, response):
        ld = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        del ld["openingHoursSpecification"]
        item = LinkedDataParser.parse_ld(ld)
        item["lat"] = response.meta["lat"]
        item["lon"] = response.meta["lon"]
        yield item
