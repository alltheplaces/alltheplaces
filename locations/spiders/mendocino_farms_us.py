import json
import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class MendocinoFarmsUSSpider(SitemapSpider, PlaywrightSpider):
    name = "mendocino_farms_us"
    item_attributes = {"brand": "Mendocino Farms", "brand_wikidata": "Q110671982"}
    sitemap_urls = ["https://www.mendocinofarms.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.mendocinofarms.com/location-directory/[^/]+/[^/]+$", "parse")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('//*[@class="DirectoryLocations_store_address__asST8"]/@aria-label').get()
        item["phone"] = response.xpath('//*[contains(text(),"tel:")]/text()').get()
        item["email"] = response.xpath('//*[contains(text(),"mailto:")]/text()').get()
        item["lat"] = re.search(r"\\\"latitude\\\":\\\"(\d+\.\d+)\\\",", response.text).group(1)
        item["lon"] = re.search(r"\\\"longitude\\\":\\\"(-?\d+\.\d+)\\\",", response.text).group(1)
        try:

            hours_data = json.loads(
                re.search(
                    r"business\":({.+}),\"dispatch",
                    response.xpath('//*[contains(text(),"latitude")]/text()').get().replace("\\", ""),
                ).group(1)
            )

            item["opening_hours"] = OpeningHours()
            for day, slot in hours_data.items():
                if (day_code := sanitise_day(day)) and slot.get("start") and slot.get("end"):
                    item["opening_hours"].add_range(
                        day_code, slot["start"].split(" ", 1)[1][:5], slot["end"].split(" ", 1)[1][:5]
                    )
        except:
            pass
        yield item
