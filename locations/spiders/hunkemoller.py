import chompjs
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class HunkemollerSpider(SitemapSpider):
    name = "hunkemoller"
    item_attributes = {"brand": "Hunkemöller", "brand_wikidata": "Q2604175"}
    sitemap_urls = ["https://www.hunkemoller.be/nl/sitemap-stores.xml"]
    sitemap_rules = [
        (
            r"https://www.hunkemoller.be/nl/winkel/.+/.+$",
            "parse",
        ),
    ]

    def parse(self, response, **kwargs):
        script_text = response.xpath('//script[contains(text(), "pageContext")]/text()').get()
        poi = chompjs.parse_js_object(script_text)["analytics"]["store"]
        item = DictParser.parse(poi)
        item["ref"] = item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        if not poi.get("openingHours"):
            return
        for rule in poi.get("openingHours", []):
            if day := sanitise_day(rule["dayOfWeek"], DAYS_NL):
                open_time = rule.get("open")
                close_time = rule.get("close")
                item["opening_hours"].add_range(day, open_time, close_time)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
