import chompjs
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DillardsSpider(SitemapSpider, StructuredDataSpider):
    name = "dillards"
    item_attributes = {"brand": "Dillard's", "brand_wikidata": "Q844805"}
    allowed_domains = ["www.dillards.com"]
    sitemap_urls = ["https://www.dillards.com/robots.txt"]
    sitemap_follow = ["sitemap_storeLocator_"]
    sitemap_rules = [(r"/stores/[^/]+/[^/]+/(\d+)$", "parse")]
    time_format = "%I:%M %p"
    wanted_types = ["DepartmentStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        script_data = chompjs.parse_js_object(response.xpath('//script/text()[contains(.,"__INITIAL_STATE__")]').get())
        item["lat"] = script_data["contentData"]["store"]["latitude"]
        item["lon"] = script_data["contentData"]["store"]["longitude"]

        # TODO: Why isn't this automatically done by StructuredDataSpider?
        hours = OpeningHours()
        for row in ld_data["openingHoursSpecification"]:
            day = row["dayOfWeek"]["name"][:2]
            hours.add_range(day, row["opens"], row["closes"], self.time_format)
        item["opening_hours"] = hours
        item["website"] = response.url

        yield item

    def parse(self, response):
        if "Access Denied" in response.text:
            return get_retry_request(response.request, spider=self, reason="throttle")
        else:
            return super().parse(response)
