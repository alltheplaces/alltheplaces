from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_email


class JaycarAUSpider(SitemapSpider):
    name = "jaycar_au"
    item_attributes = {"brand": "Jaycar", "brand_wikidata": "Q6167713"}
    sitemap_urls = ["https://www.jaycar.com.au/sitemap.xml"]
    sitemap_follow = ["/Store-en-aud-"]
    sitemap_rules = [("/store/", "parse")]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "_STK" not in entry["loc"]:
                # Filter out resellers
                yield entry

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath('//div[@class="detailSectionHeadline"]/text()').get()
        item["phone"] = response.xpath('normalize-space(//div[@class="detailSection"][contains(., "Telephone")])').get()
        item["lon"] = response.xpath("//@data-longitude").get()
        item["lat"] = response.xpath("//@data-latitude").get()
        item["addr_full"] = merge_address_lines(
            response.xpath('//div[@class="detailSection"][contains(., "Australia")]/ul/li/text()').getall()
        )

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//tr[@class="weekday_openings"]'):
            day = rule.xpath('./td[@class="weekday_openings_day"]/text()').get()
            times = rule.xpath('./td[@class="weekday_openings_times"]/text()').get().strip().split(" - ")
            if len(times) == 2:
                item["opening_hours"].add_range(day, times[0], times[1], "%I:%M %p")

        extract_email(item, response)

        yield item
