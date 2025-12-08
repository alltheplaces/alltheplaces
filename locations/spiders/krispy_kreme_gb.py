from scrapy.spiders import SitemapSpider

from locations.spiders.krispy_kreme_us import KrispyKremeUSSpider
from locations.structured_data_spider import StructuredDataSpider


class KrispyKremeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "krispy_kreme_gb"
    item_attributes = KrispyKremeUSSpider.item_attributes
    sitemap_urls = ["https://shops.krispykreme.co.uk/robots.txt"]

    def sitemap_filter(self, entries):
        for entry in entries:
            ignore = False
            # Filter out as many kiosk sites as we can, these are the big ones.
            for outlet in ["/sainsburys-", "/asda-", "/tesco-", "/morrisons-", "/welcome-break-", "/moto-"]:
                if outlet in entry["loc"]:
                    ignore = True
                    break
            if not ignore:
                yield entry

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["address"] = ld_data["location"]["address"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["opening_hours"]:
            # Only a location with opening hours is considered a non kiosk type venue.
            item["website"] = response.url
            yield item
