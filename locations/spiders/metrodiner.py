import json

from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class MetroDinerSpider(SitemapSpider, StructuredDataSpider):
    name = "metrodiner"
    item_attributes = {"brand": "Metro Diner", "brand_wikidata": "Q104870732"}
    allowed_domains = ["metrodiner.com"]
    sitemap_urls = [
        "https://metrodiner.com/locations-sitemap.xml",
    ]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data):
        ldjson = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()[contains(.,\'"Restaurant"\')]').get()
        )
        oh = OpeningHours()
        for day in ldjson.get("openingHoursSpecification"):
            oh.add_range(
                day=day.get("dayOfWeek").replace("https://schema.org/", ""),
                open_time=day.get("opens")[:5],
                close_time=day.get("closes")[:5],
            )

        item["opening_hours"] = oh.as_opening_hours()
        extract_google_position(item, response)

        yield item
