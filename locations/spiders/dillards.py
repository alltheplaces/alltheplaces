import json

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class DillardsSpider(SitemapSpider, StructuredDataSpider):
    name = "dillards"
    item_attributes = {"brand": "Dillard's", "brand_wikidata": "Q844805"}
    allowed_domains = ["www.dillards.com"]
    sitemap_urls = ("https://www.dillards.com/sitemap/sitemap_storeLocator_1.xml",)
    download_delay = 0.5
    wanted_types = ["DepartmentStore"]
    time_format = "%I:%M %p"

    sitemap_rules = [(r"https://www.dillards.com/stores/.*/.*", "parse")]

    def post_process_item(self, item, response, ld_data):
        script = response.xpath('//script/text()[contains(.,"__INITIAL_STATE__")]').get()
        script_data = json.decoder.JSONDecoder().raw_decode(script, script.index("{"))[0]
        lat = script_data["contentData"]["store"]["latitude"]
        lon = script_data["contentData"]["store"]["longitude"]

        # TODO: Why isn't this automatically done by StructuredDataSpider?
        hours = OpeningHours()
        for row in ld_data["openingHoursSpecification"]:
            day = row["dayOfWeek"]["name"][:2]
            hours.add_range(day, row["opens"], row["closes"], self.time_format)

        item["opening_hours"] = hours
        item["ref"] = response.css(".storeNumber::text").get()
        item["lat"] = lat
        item["lon"] = lon
        item["website"] = response.url
        yield item

    def parse(self, response):
        if "Access Denied" in response.text:
            return get_retry_request(response.request, spider=self, reason="throttle")
        else:
            return super().parse(response)
