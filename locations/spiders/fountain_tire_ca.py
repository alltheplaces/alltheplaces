from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class FountainTireCASpider(SitemapSpider):
    name = "fountain_tire_ca"
    item_attributes = {"brand": "Fountain Tire", "brand_wikidata": "Q5474771"}
    sitemap_urls = ["https://www.fountaintire.com/sitemap.xml"]
    sitemap_rules = [(r"\/stores\/(?![a-z]{2}$|[a-z]+$|british-columbia$)([a-z0-9-]+)\/?$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@property="storeinfo:name"]/@content').get()
        item["street_address"] = response.xpath('//*[@property="storeinfo:address"]/@content').get()
        item["city"] = response.xpath('//*[@property="storeinfo:city"]/@content').get()
        item["state"] = response.xpath('//*[@property="storeinfo:region"]/@content').get()
        item["postcode"] = response.xpath('//*[@property="storeinfo:postalcode"]/@content').get()
        item["phone"] = response.xpath('//*[@property="storeinfo:phone"]/@content').get()
        item["email"] = response.xpath('//*[@property="storeinfo:email"]/@content').get()
        item["ref"] = item["website"] = response.url
        item["lat"], item["lon"] = response.xpath('//*[@property="storeinfo:latlon"]/@content').get().split(",")
        if hours_data := response.xpath('//*[@property="storeinfo:hours"]/@content').get():
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_data)
            item["opening_hours"] = oh
        yield item
