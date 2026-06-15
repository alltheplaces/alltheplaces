import re
from typing import Any

import reverse_geocoder
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class TgjonesGBSpider(SitemapSpider):
    name = "tgjones_gb"
    item_attributes = {"brand": "TGJones", "brand_wikidata": "Q133575797"}
    allowed_domains = ["tgjonesonline.co.uk"]
    sitemap_urls = ["https://www.tgjonesonline.co.uk/SiteMap/sitemap-pages.xml"]
    sitemap_rules = [(r"/stores/[-\w]+", "parse")]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {"Host": "www.tgjonesonline.co.uk", "Alt-Used": "www.tgjonesonline.co.uk"},
        "USER_AGENT": BROWSER_DEFAULT,
    }
    coordinates_pattern = re.compile(r"google\.maps\.LatLng\(\s*([-\d.]+)[,\s]+([-\d.]+)\s*\)")
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath("//h1/text()").get(default="").split(",")[0]
        if not item["name"]:
            return
        item["addr_full"] = clean_address(response.xpath('//*[@class="shop-styling__address"]/p/text()').getall())
        if coordinates := re.search(self.coordinates_pattern, response.text):
            item["lat"], item["lon"] = coordinates.groups()
        # Some stores have wildly incorrect coordinates for
        # locations as far away as the Indian Ocean. Remove
        # these incorrect coordinates.
        # Some stores are located in countries other than GB. Make
        # the required change to the item's country.
        if result := reverse_geocoder.get((float(item["lat"]), float(item["lon"])), mode=1, verbose=False):
            match result["cc"]:
                case "GB" | "IE" | "JE" | "IM" | "GG":
                    item["country"] = result["cc"]
                case _:
                    item.pop("lat")
                    item.pop("lon")

        apply_category(Categories.SHOP_NEWSAGENT, item)

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//li[@class="whs-hours-item"]'):
            day = rule.xpath('.//*[contains(@class, "day")]/text()').get("")
            hours = rule.xpath('.//*[contains(@class, "time")]/text()').get("").replace("24hr-24hr", "00:00-23:59")
            item["opening_hours"].add_ranges_from_string(f"{day} {hours}")
        yield item
