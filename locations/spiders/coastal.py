# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class CoastalFarmSpider(scrapy.Spider):

    name = "coastalfarm"
    item_attributes = {"brand": "Coastal"}
    allowed_domains = ["www.coastalfarm.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "https://www.coastalfarm.com/wp-admin/admin-ajax.php?action=store_search&lat=45.523062&lng=-122.67648199999996&max_results=25&search_radius=50",
    )

    def parse(self, response):
        results = response.json()
        for data in results:
            properties = {
                "city": data["city"],
                "ref": data["id"],
                "lon": data["lng"],
                "lat": data["lat"],
                "addr_full": data["address"],
                "phone": data["phone"],
                "state": data["state"],
                "postcode": data["zip"],
                "website": data["url"],
            }

            yield GeojsonPointItem(**properties)
