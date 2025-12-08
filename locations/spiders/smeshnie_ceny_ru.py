import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours
from locations.items import Feature


class SmeshnieCenyRUSpider(SitemapSpider):
    name = "smeshnie_ceny_ru"
    item_attributes = {"brand": "Смешные цены"}
    # TODO: add brand in wikidata
    allowed_domains = ["smeshnie-ceny.ru"]
    sitemap_urls = ["https://smeshnie-ceny.ru/magazin-sitemap.xml"]
    sitemap_rules = [(r"/magazin/", "parse")]

    def parse(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('//table[@class="table"]/tbody/tr[th/text()="Адрес"]/td/text()').get()
        script_text = response.xpath('//script[contains(., "ymaps.ready(init)")]/text()').get()
        if match := re.search(r"new ymaps.Placemark\(\[([\d.]+),\s*([\d.]+)\]", script_text):
            item["lat"] = match.group(1)
            item["lon"] = match.group(2)
        if hours := response.xpath('//table[@class="table"]/tbody/tr[th/text()="График"]/td/text()').get():
            oh = OpeningHours()
            oh.add_ranges_from_string(hours, DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU)
            item["opening_hours"] = oh.as_opening_hours()
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
