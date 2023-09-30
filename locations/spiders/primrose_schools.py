import json

import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points


class PrimroseSchoolsSpider(scrapy.Spider):
    name = "primrose_schools"
    item_attributes = {"brand": "Primrose Schools", "brand_wikidata": "Q7243677"}
    allowed_domains = ["primroseschools.com"]

    start_urls = ["https://www.primroseschools.com/find-a-school/"]

    def parse(self, response):
        with open_searchable_points("us_centroids_50mile_radius.csv") as points:
            next(points)
            for point in points:
                row = point.replace("\n", "").split(",")
                lati = row[1]
                long = row[2]
                searchurl = "https://www.primroseschools.com/find-a-school/?search_string=USA&latitude={la}&longitude={lo}".format(
                    la=lati, lo=long
                )
                yield scrapy.Request(response.urljoin(searchurl), callback=self.parse_search)

    def parse_search(self, response):
        content = response.xpath('//script[@type="application/json"]/text()').get()
        if content is None:
            return

        schools = json.loads(content)
        for i in schools:
            if i["address_1"]:
                properties = {
                    "name": i["name"],
                    "street_address": ", ".join(filter(None, [i["address_1"], i["address_2"]])),
                    "city": i["city"],
                    "state": i["state"],
                    "postcode": i["zip_code"],
                    "phone": i["phone"],
                    "ref": i["id"],
                    "website": "https://www.primroseschools.com" + i["url"],
                    "lat": float(i["latitude"]),
                    "lon": float(i["longitude"]),
                }
                yield Feature(**properties)
