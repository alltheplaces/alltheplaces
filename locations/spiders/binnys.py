import chompjs
import scrapy
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class BinnysSpider(SitemapSpider):
    name = "binnys"
    item_attributes = {"brand": "Binny's Beverage Depot", "brand_wikidata": "Q30687714"}
    allowed_domains = ["binnys.com"]
    sitemap_urls = ["https://www.binnys.com/robots.txt"]
    sitemap_rules = [(r"/store-locator/", "parse")]

    def parse(self, response):
        script = response.xpath(
            '//script/text()[contains(.,"var serverSideViewModel")]'
        ).get()
        data = chompjs.parse_js_object(script)
        oh = OpeningHours()
        hours = scrapy.selector.Selector(text=data["storeHours"])
        for row in hours.css("tr"):
            [day, interval] = row.css("td::text").extract()
            open_time, close_time = interval.split(" - ")
            oh.add_range(day[:2], open_time, close_time, "%I:%M %p")
        properties = {
            "ref": data["storeId"],
            "lat": data["latitude"],
            "lon": data["longitude"],
            "name": data["storeName"],
            "street_address": data["addressLine1"],
            "city": data["city"],
            "state": data["state"],
            "postcode": data["zipCode"],
            "phone": data["phoneNumber"],
            "email": data["emailAddress"],
            "opening_hours": oh.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
