from collections import Counter
from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CookGBGGSpider(SitemapSpider):
    name = "cook_gb_gg"
    item_attributes = {"brand": "Cook", "brand_wikidata": "Q113457474"}
    allowed_domains = ["www.cookfood.net"]
    sitemap_urls = ["https://www.cookfood.net/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.cookfood\.net\/shops\/[\w\-]+$", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url.removeprefix("https://www.cookfood.net/shops/"),
            "branch": response.xpath('//div[@class="shop-title"]/h1/text()').get(),
            "lat": response.xpath('//div[@id="googleMapsWidget"]/@data-lat').get(),
            "lon": response.xpath('//div[@id="googleMapsWidget"]/@data-lng').get(),
            "addr_full": merge_address_lines(
                response.xpath('//div[@class="shop-address-info"]/p[position()<=2]/text()').getall()
            ),
            "phone": response.xpath('//div[@class="shop-address-info"]/p/a[contains(@href, "tel:")]/@href')
            .get()
            .removeprefix("tel:"),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }

        # Five weeks worth of opening hours is returned, and each week could
        # have slightly different hours depending on public holidays. We
        # therefore need to find the most common opening hours for each day
        # across this five week period, allowing temporary changes for public
        # holidays in a given week to be ignored.
        hours_js = response.xpath('//script[contains(text(), "openingHoursByWeek")]/text()').get()
        hours_js = "[" + hours_js.split('"openingHoursByWeek":[', 1)[1].split("}),", 1)[0] + "]"
        hours_json = parse_js_object(hours_js)
        hours_by_day = {day_name: [] for day_name in DAYS_FROM_SUNDAY}
        for week in hours_json:
            for day_index, day_hours in enumerate(week["openingDays"]):
                if not day_hours["openTime"] or not day_hours["closeTime"]:
                    hours_by_day[DAYS_FROM_SUNDAY[day_index]].append("CLOSED")
                    continue
                hours_by_day[DAYS_FROM_SUNDAY[day_index]].append(
                    (day_hours["openTime"].split("T", 1)[1], day_hours["closeTime"].split("T", 1)[1])
                )
        for day_name, day_hours_list in hours_by_day.items():
            most_common_day_hours = Counter(day_hours_list).most_common(1)[0][0]
            properties["opening_hours"].add_range(
                day_name, most_common_day_hours[0], most_common_day_hours[1], "%H:%M:%S"
            )

        apply_category(Categories.SHOP_FROZEN_FOOD, properties)

        yield Feature(**properties)
