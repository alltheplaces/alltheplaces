import re
from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PharmasaveCASpider(SitemapSpider):
    name = "pharmasave_ca"
    item_attributes = {"brand": "Pharmasave", "brand_wikidata": "Q17093822"}
    sitemap_urls = ["https://pharmasave.com/sitemap_index.xml"]
    sitemap_follow = [r"https://pharmasave.com/[-\w]+/page-sitemap"]
    sitemap_rules = [(r"https://pharmasave.com/[-\w]+/location/$", "parse_website")]
    coordinates_pattern = re.compile(r"var lat = ([-.\d]+);.+?var lon = ([-.\d]+);", re.DOTALL)

    def sitemap_filter(self, entries):
        for entry in entries:
            if not entry["loc"].endswith(".xml"):
                entry["loc"] = urljoin(entry["loc"], "location/")
            yield entry

    def parse_website(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//meta[@property="og:title"]/@content').get().replace("Pharmasave ", "")
        if match := re.search(self.coordinates_pattern, response.text):
            item["lat"], item["lon"] = match.groups()
        item["addr_full"] = clean_address(response.xpath('//*[contains(@class, "store-info-address")]/text()').get())
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get()
        item["opening_hours"] = OpeningHours()
        for timing in response.xpath('//*[contains(text(),"Store Hours")]/parent::span/following-sibling::ul[1]/li'):
            if day := sanitise_day(timing.xpath("./text()").get()):
                hours = timing.xpath("./span/text()").get("")
                for start_time, start_am_pm, end_time, end_am_pm in re.findall(
                    r"(\d+:\d+)\s*(am|pm)?[-\s]+(\d+:\d+)\s*(am|pm)?", hours.lower()
                ):
                    start_time = f"{start_time} {start_am_pm}"
                    end_time = f"{end_time} {end_am_pm}"
                    item["opening_hours"].add_range(day, start_time, end_time, time_format="%I:%M %p")
        apply_category(Categories.PHARMACY, item)
        yield item
