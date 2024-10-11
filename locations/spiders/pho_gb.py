from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class PhoGBSpider(SitemapSpider, StructuredDataSpider):
    name = "pho_gb"
    item_attributes = {
        "brand": "Pho",
        "brand_wikidata": "Q108443630",
    }
    sitemap_urls = ["https://www.phocafe.co.uk/locations-sitemap.xml"]
    wanted_types = ["Restaurant"]

    def extract_amenities(self, item, response):
        wheelchair = response.xpath("//i[@class='fa fa-wheelchair']").get()
        wifi = response.xpath("//i[@class='fa fa-wifi']").get()
        # kid_friendly = response.xpath("//i[@class='fa fa-child']").get()

        if wheelchair:
            apply_yes_no(Extras.WHEELCHAIR, item, True)

        if wifi:
            apply_yes_no(Extras.WIFI, item, True)

    def extract_opening_hours(self, item, response):
        hours = response.xpath(
            "//section[@class='location-contact']/div/div/div/div[@class='col-7']/div[@class='contact-details']/p/text()"
        ).get()

        oh = OpeningHours()
        oh.add_ranges_from_string(hours)

        item["opening_hours"] = oh

    def extract_coords(self, item, response):
        url = response.xpath("//a[contains(@href, 'https://citymapper.com/directions?startcoord=')]/@href").get()

        item["lat"], item["lon"] = url.split("https://citymapper.com/directions?startcoord=")[1].split(",")

    def post_process_item(self, item, response, ld_data, **kwargs):
        self.extract_opening_hours(item, response)
        self.extract_coords(item, response)
        self.extract_amenities(item, response)

        yield item
