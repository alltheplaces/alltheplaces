from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EuromasterNLSpider(SitemapSpider, StructuredDataSpider):
    name = "euromaster_nl"
    item_attributes = {"brand": "Euromaster", "brand_wikidata": "Q3060668"}
    sitemap_urls = ["https://www.euromaster.nl/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.euromaster\.nl/garages/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["AutoRepair"]
    # CloudFront blocks direct requests with a 202 challenge; route through Zyte proxy.
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Euromaster ")
        item["website"] = response.url
        # JSON-LD dayOfWeek values are garbled ("????day-2????"); parse from HTML table instead.
        oh = OpeningHours()
        days = response.xpath('//*[@class="tableHoraires"]/tr/th/text()').getall()
        hours = response.xpath('//*[@class="tableHoraires"]/tr/td/text()').getall()
        for day, hour in zip(days, hours):
            oh.add_ranges_from_string(ranges_string=day + " " + hour, days=DAYS_NL, delimiters=[" - "])
        item["opening_hours"] = oh
        yield item
