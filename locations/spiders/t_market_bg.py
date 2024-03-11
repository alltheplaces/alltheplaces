import re

from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import DAYS_BG, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class T_Market_BGSpider(SitemapSpider):
    name = "t_market_bg"
    item_attributes = {"brand": "T-Market", "brand_wikidata": "Q64033983"}
    allowed_domains = ["tmarket.bg"]
    sitemap_urls = ["https://tmarket.bg/sitemap/page/1.xml"]
    sitemap_rules = [(r"https://tmarket\.bg/page/magazin[\w-]+", "parse")]
    no_refs = True

    def parse(self, response):
        item = Feature()
        extract_google_position(item, response)
        item["addr_full"] = (
            response.xpath('//p[contains(text(), "Адрес:")]/following-sibling::p[1]/text()').get(default="").strip()
            if response.xpath('//p[contains(text(), "Адрес:")]')
            else None
        )

        item["opening_hours"] = OpeningHours()
        # Some pages have split the opening days in multiple elements like <strong>Понеделник - <b>Неделя</b></strong>
        oh_days = response.xpath(
            '//*[contains(text(), "Понеделник") or contains(text(), "Вторник") or contains(text(), "Сряда") or contains(text(), "Четвъртък") or contains(text(), "Петък") or contains(text(), "Събота") or contains(text(), "Неделя")]//text()'
        ).getall()
        self.log(oh_days)
        # Others lack days entirely, so it's Mo-Su
        if len(oh_days) == 1 and oh_days[0] is None:
            oh_days[0] = "Понеделник - Неделя"
        oh_days = [re.sub(r"[^а-я-]", "", days.lower()) for days in oh_days]

        # Merge the split day ranges
        for index, day in enumerate(oh_days):
            if day.endswith("-"):
                oh_days[index] = "".join([oh_days[index], oh_days.pop(index + 1)])
        oh_days = [[sanitise_day(day, DAYS_BG) for day in days.split("-")] for days in oh_days]

        oh_hours = response.xpath('(//*[contains(text(), ":00")])/text()').getall()
        oh_hours = [re.sub(r"[^0-9:-]", "", hours).split("-") for hours in oh_hours]

        item["opening_hours"] = OpeningHours()
        for index, days in enumerate(oh_days):
            if len(days) == 2:
                item["opening_hours"].add_days_range(
                    day_range(days[0], days[1]), oh_hours[index][0], oh_hours[index][1]
                )
            else:
                item["opening_hours"].add_range(days[0], oh_hours[index][0], oh_hours[index][1])

        yield item
