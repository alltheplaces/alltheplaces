import html

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_PT, OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.structured_data_spider import StructuredDataSpider


class McdonaldsPTSpider(SitemapSpider, StructuredDataSpider):
    name = "mcdonalds_pt"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.pt"]
    sitemap_urls = ["https://www.mcdonalds.pt/sitemap"]
    sitemap_rules = [("/restaurantes/", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = html.unescape(item.pop("name")).removeprefix("McDonald's ")

        services = response.xpath("//div/@data-content").getall()
        apply_yes_no(Extras.DELIVERY, item, "McDelivery" in services)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "McDrive" in services)
        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in services)
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Fraldário" in services)
        apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in services)

        if "McCafé" in services:
            mccafe = item.deepcopy()
            mccafe["ref"] = "{}-mccafe".format(item["ref"])
            mccafe["brand"] = "McCafé"
            mccafe["brand_wikidata"] = "Q3114287"
            apply_category(Categories.CAFE, mccafe)
            yield mccafe

        item["opening_hours"] = self.parse_opening_hours(
            response.xpath(
                '//div[contains(@class, "swiper-slide restaurantSchedule__service")][contains(., "Restaurante")]//li'
            )
        )
        item["extras"]["opening_hours:drive_through"] = self.parse_opening_hours(
            response.xpath(
                '//div[contains(@class, "swiper-slide restaurantSchedule__service")][contains(., "McDrive")]//li'
            )
        ).as_opening_hours()

        yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if day := sanitise_day(rule.xpath("cite/text()").get(), DAYS_PT):
                start_time, end_time = rule.xpath("span/text()").get().split(" às ")
                if end_time == "0h00":
                    end_time = "23h59"
                oh.add_range(day, start_time, end_time, time_format="%Hh%M")

        return oh
