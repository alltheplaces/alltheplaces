import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class NaturhouseFRSpider(SitemapSpider):
    name = "naturhouse_fr"
    item_attributes = {"brand": "Natur House", "brand_wikidata": "Q6038807"}
    sitemap_urls = ["https://www.naturhouse.fr/sitemap.xml"]
    sitemap_rules = [(r"/centre/(\d+)-[^/]+$", "parse")]

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = re.search(r"/centre/(\d+)-", response.url).group(1)
        item["website"] = response.url
        item["branch"] = response.xpath('normalize-space(//li[@aria-current="page"])').get()
        item["addr_full"] = response.xpath('normalize-space(//div[@id="cardAddress"]//p)').get()
        if m := re.search(r"\b(\d{5}) (.+)$", item["addr_full"] or ""):
            item["postcode"], item["city"] = m.group(1), m.group(2).title()
            item["country"] = OVERSEAS_COUNTRIES.get(item["postcode"][:3], "FR")
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').get()
        if m := re.search(r"const shop = \{ lat: (-?[\d.]+), lng: (-?[\d.]+) \}", response.text):
            item["lat"], item["lon"] = m.group(1), m.group(2)

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//table[contains(@class, "table-horaires")]//tr'):
            day = sanitise_day(row.xpath("normalize-space(./td[1])").get(), DAYS_FR)
            times = row.xpath("normalize-space(./td[2])").get()
            if not day:
                continue
            if "fermé" in times.lower():
                item["opening_hours"].set_closed(day)
                continue
            for open_time, close_time in re.findall(r"(\d{1,2}h\d{2}) - (\d{1,2}h\d{2})", times):
                item["opening_hours"].add_range(day, open_time, close_time, "%Hh%M")

        apply_category(Categories.SHOP_NUTRITION_SUPPLEMENTS, item)
        yield item
