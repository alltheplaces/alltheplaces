import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points


class RaisingCanesSpider(scrapy.Spider):
    name = "raising_canes"
    item_attributes = {"brand": "Raising Cane's Chicken Fingers"}
    allowed_domains = ["www.raisingcanes.com"]
    start_urls = ("https://www.raisingcanes.com/locations",)

    def start_requests(self):
        base_url = "https://www.raisingcanes.com/sites/all/themes/raising_cane_s/locator/include/locationsNew.php?&lat={lat}&lng={lng}"

        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = response.json()
        store_data = data["response"]

        for store in store_data:
            name = store["properties"]["field_alt_title"].strip("&quot;")
            if "Now Open" in name or "Coming Soon" in name:
                continue
            else:
                properties = {
                    "ref": store["properties"]["name"].replace("&#039;s ", " "),
                    "name": name,
                    "addr_full": store["address"],
                    "country": "US",
                    "lat": float(store["geometry"]["coordinates"][1]),
                    "lon": float(store["geometry"]["coordinates"][0]),
                    "phone": store["properties"]["field_phone"],
                    "website": store["properties"]["path"].strip('<a href="').strip('">Restaurant Details</a>'),
                }
                yield Feature(**properties)
