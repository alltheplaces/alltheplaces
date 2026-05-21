import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class HammerDESpider(SitemapSpider):
    name = "hammer_de"
    item_attributes = {"brand": "Hammer", "brand_wikidata": "Q52159668"}
    sitemap_urls = ["https://www.hammer-raumstylisten.de/markt-sitemap.xml"]
    sitemap_rules = [("fachmaerkte", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = (
            response.xpath('//h2[starts-with(normalize-space(text()), "Hammer Fachmarkt")]/text()')
            .get()
            .removeprefix("Hammer Fachmarkt ")
        )
        item["addr_full"] = merge_address_lines(response.xpath('//*[@id="brxe-vqslzw"]//li[1]//span/text()').getall())
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//span//text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto")]//span//text()').get()
        item["ref"] = item["website"] = response.url
        map_data = json.loads(response.xpath("//@data-map-options").get())
        item["lat"] = map_data["map"]["center"]["lat"]
        item["lon"] = map_data["map"]["center"]["lng"]
        oh = OpeningHours()
        for day_time in response.xpath('//*[@id="brxe-bjulpk"]//div'):
            day = sanitise_day(
                day_time.xpath('.//*[@class="openinghours-weekday"]//text()').get().replace(":", ""), DAYS_DE
            )
            time = day_time.xpath('.//*[@class="openinghours-hours"]//text()').get().replace(" Uhr", "")
            if time == "Geschlossen":
                oh.set_closed(day)
            else:
                open_time, close_time = time.split(" - ")
                oh.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
