import re

from scrapy import Request
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class LegalSeaFoodsUSSpider(SitemapSpider):
    name = "legal_sea_foods_us"
    item_attributes = {"brand": "Legal Sea Foods", "name": "Legal Sea Foods"}
    sitemap_urls = ["https://www.legalseafoods.com/page-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/$", "parse_location")]
    custom_settings = {"USER_AGENT": "Googlebot"}

    def parse_location(self, response):
        item = Feature(
            ref=response.url.rstrip("/").rsplit("/", 1)[-1],
            branch=response.css("h1::text").get(),
            phone=response.xpath('//section[contains(@class, "m__map")]//a[starts-with(@href, "tel:")]/@href').get(),
            website=response.url,
        )
        item["phone"] = item["phone"].removeprefix("tel:") if item["phone"] else None

        widget = response.xpath('//*[@data-marqii and starts-with(@data-marqii, "hours-")]/@data-marqii').get()
        if widget:
            yield Request(
                url=f"https://embed.marqii.com/api/v2/public/widget/{widget.removeprefix('hours-')}?widgetType=hours",
                callback=self.parse_hours,
                cb_kwargs={"item": item},
            )
            return

        address = response.xpath(
            'normalize-space((//div[contains(@class, "m__hero__breadcrumbs")]//a[contains(@href, "google.com/maps")])[1])'
        ).get()
        item["addr_full"] = address
        if match := re.search(r", ([^,]+), ([A-Z]{2}) (\d{5})$", address):
            item["city"], item["state"], item["postcode"] = match.groups()
            item["country"] = "US"

        hours = OpeningHours()
        for line in response.xpath(
            '//section[contains(@class, "m__map")]//div[contains(@class, "m__map__content-row")][.//*[normalize-space()="Opening Hours"]]//div[contains(@class, "m__map__content-row-content")]//text()'
        ).getall():
            if re.match(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun):", line.strip()):
                hours.add_ranges_from_string(line.replace("–", "-").replace("*", "").strip())
        item["opening_hours"] = hours
        apply_category(Categories.RESTAURANT, item)
        yield item

    def parse_hours(self, response, item):
        data = response.json()
        address = data["store"]["address"]
        item["street_address"] = address["streetAddress"]
        item["city"] = address["addressLocality"]
        item["state"] = address["addressRegion"]
        item["postcode"] = address["postalCode"]
        item["country"] = address["country"]

        hours = OpeningHours()
        for hours_type in data["data"]:
            if hours_type["hourTypeName"] != "Base":
                continue
            for day in hours_type["regularHours"]:
                day_code = day["dayOfTheWeek"].title()[:2]
                if not day["isOpen"]:
                    hours.set_closed(day_code)
                    continue
                for period in day["period"]:
                    hours.add_range(day_code, period["startTime"], period["endTime"])
        item["opening_hours"] = hours
        apply_category(Categories.RESTAURANT, item)
        yield item
