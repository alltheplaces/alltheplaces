import json
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.hours import OpeningHours


class GoodYearSpider(SitemapSpider, StructuredDataSpider):
    name = "goodyear_us"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    sitemap_urls = [
        "https://www.goodyear.com/sitemap-retail-detail.xml",
        "https://www.goodyearautoservice.com/sitemap-retail-detail.xml",
    ]
    sitemap_rules = [("/tire-shop/", "parse_sd"), ("/shop/", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        ldjson = response.xpath('//script[@type="application/ld+json"]/text()[contains(.,"LocalBusiness")]').get()
        data = json.loads(ldjson)
        item["lat"] = data.get("areaServed", {}).get("geoMidpoint", {}).get("latitude")
        item["lon"] = data.get("areaServed", {}).get("geoMidpoint", {}).get("longitude")

        oh = OpeningHours()
        if days := data.get("openingHoursSpecification"):
            for day in days:
                oh.add_range(
                    day=day.get("dayOfWeek"),
                    open_time=day.get("opens"),
                    close_time=day.get("closes"),
                    time_format="%I:%M %p",
                )
            item["opening_hours"] = oh.as_opening_hours()

        yield item
