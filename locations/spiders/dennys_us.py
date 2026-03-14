from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DennysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dennys_us"
    item_attributes = {"brand": "Denny's", "brand_wikidata": "Q1189695"}
    sitemap_urls = ["https://locations.dennys.com/robots.txt"]
    sitemap_rules = [(r"https://locations.dennys.com/[^/]+/[^/]+/(\d+)$", "parse_sd")]
    time_format = "%I:%M %p"

    def pre_process_data(self, ld_data: dict, **kwargs):
        for rule in ld_data["openingHoursSpecification"]:
            if rule["opens"] == "Closed":
                continue
            if rule["opens"] == "Open 24 Hours":
                rule["opens"] = "12:00 AM  to  11:59 PM"
            rule["opens"], rule["closes"] = rule["opens"].split("  to  ", 1)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = None

        item["extras"]["website:menu"] = response.xpath('//a[@data-event-name="loc_view_menu"]/@href').get()
        item["extras"]["website:orders"] = response.xpath('//a[@data-event-name="loc_order_online"]/@href').get()

        yield item
