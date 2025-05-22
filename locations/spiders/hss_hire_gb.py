from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


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
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]//text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//text()').get()
        extract_google_position(item, response)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath("//main//ul/li"):
            day = day_time.xpath("./span[1]/text()").get()
            time = day_time.xpath("./span[2]/text()").get()
            if time in ["Closed"]:
                continue
            open_time, close_time = time.split("-")
            item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        yield item
