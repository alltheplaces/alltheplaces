import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class GoodYearSpider(SitemapSpider, StructuredDataSpider):
    name = "goodyear_us"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    sitemap_urls = [
        "https://www.goodyear.com/sitemap-retail-detail.xml",
        "https://www.goodyearautoservice.com/sitemap-retail-detail.xml",
    ]
    sitemap_rules = [("/tire-shop/", "parse_sd"), ("/shop/", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["lat"] = ld_data.get("areaServed", {}).get("geoMidpoint", {}).get("latitude")
        item["lon"] = ld_data.get("areaServed", {}).get("geoMidpoint", {}).get("longitude")

        if not item["lat"]:
            coords = json.loads(response.xpath("//@data-location").get())
            item["lat"] = coords.get("latitude")
            item["lon"] = coords.get("longitude")

        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()

        yield item
