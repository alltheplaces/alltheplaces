from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone


class HssHireGBSpider(SitemapSpider):
    name = "hss_hire_gb"
    item_attributes = {"brand": "HSS Hire", "brand_wikidata": "Q5636000"}
    sitemap_urls = ["https://www.hss.com/sitemap-branches.xml"]
    sitemap_rules = [(r"/branches/(?!virtual-test).+$", "parse")]

    def parse(self, response: Response, **kwargs):
        item = Feature()

        label = response.xpath("//h1/text()").get()
        if label.startswith("HSS at "):
            item["located_in"], item["branch"] = label.removeprefix("HSS at ").split(" - ", 1)
        elif label.startswith("HSS "):
            item["branch"] = label.removeprefix("HSS ")

        item["addr_full"] = (
            response.xpath('//*[@class="rounded-2xl bg-gray-100 p-5 lg:p-8"]/p').xpath("normalize-space()").get()
        )
        item["ref"] = item["website"] = response.url

        try:
            item["opening_hours"] = self.parse_opening_hours(response.xpath("//main//ul/li"))
        except:
            self.logger.error("Error parsing opening hours")

        extract_email(item, response)
        extract_phone(item, response)
        extract_google_position(item, response)

        yield item

    def parse_opening_hours(self, rules: Selector) -> OpeningHours:
        oh = OpeningHours()
        for day_time in rules:
            day = day_time.xpath("./span[1]/text()").get()
            time = day_time.xpath("./span[2]/text()").get()
            if day == "Bank holidays":
                continue
            if time == "Closed":
                oh.set_closed(day)
            else:
                oh.add_range(day, *time.split(" - "))
        return oh
