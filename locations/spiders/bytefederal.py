from typing import Any

from chompjs import parse_js_object
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class BytefederalSpider(SitemapSpider):
    name = "bytefederal"
    item_attributes = {"brand": "ByteFederal", "brand_wikidata": "Q135284888"}
    allowed_domains = ["www.bytefederal.com"]
    sitemap_urls = ["https://www.bytefederal.com/sitemap-0.xml"]
    sitemap_rules = [(r"^https:\/\/www\.bytefederal\.com\/bitcoin-atm-near-me\/[^\/]+\/[^\/]+/[^\/]+$", "parse")]
    custom_settings = {"DOWNLOAD_DELAY": 2}  # robots.txt doesn't specify a crawl delay but
    # after many requests at ~1/s, timeouts start to occur
    # so try a 2s delay instead.

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations_js = response.xpath("//mapbox-map/@data-locations").get()
        if not locations_js:
            # Some ATM pages are blank and should be ignored.
            return
        locations = parse_js_object(locations_js)

        for location in locations:
            item = DictParser.parse(location)
            item["website"] = item["ref"] = response.url

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, location["open_hour"], location["close_hour"], "%H:%M:%S")

            apply_category(Categories.ATM, item)
            item["extras"]["currency:XBT"] = "yes"
            item["extras"]["currency:SATS"] = "yes"
            item["extras"]["currency:ETH"] = "yes"
            item["extras"]["currency:DOGE"] = "yes"
            item["extras"]["currency:LTC"] = "yes"
            item["extras"]["currency:USD"] = "yes"
            item["extras"]["cash_in"] = "yes"
            apply_yes_no("cash_out", item, location["location_type"] != "one way", False)

            yield item
