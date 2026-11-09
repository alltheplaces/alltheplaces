import re
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MutuelleDePoitiersFRSpider(SitemapSpider):
    name = "mutuelle_de_poitiers_fr"
    item_attributes = {"brand": "Mutuelle de Poitiers Assurances", "brand_wikidata": "Q57200940"}
    allowed_domains = ["agence.assurance-mutuelle-poitiers.fr"]
    sitemap_urls = ["https://agence.assurance-mutuelle-poitiers.fr/sitemap.xml"]
    sitemap_rules = [(r"/agence-[^/]+/nous-trouver$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        item = Feature()
        item["ref"] = response.xpath('//input[@name="agency"]/@value').get()
        item["website"] = response.url.removesuffix("/nous-trouver")
        item["branch"] = response.xpath('//span[@class="push-agency-city"]/text()').get("").strip()
        item["phone"] = response.xpath('//p[@class="push-agency-phone"]/a/@href').get("")
        item["email"] = response.xpath('//p[@class="push-agency-email"]/a/@href').get("")

        # The address and coordinates are only in the map popup script
        script = response.xpath('//script[contains(text(), "gmap-infobulle")]/text()').get("")
        if m := re.search(r"q=loc:'\s*\+\s*(-?[\d.]+)\s*\+\s*'\+'\s*\+\s*(-?[\d.]+)", script):
            item["lat"], item["lon"] = m.groups()
        if m := re.search(r"'<div class=\"col-sm-9\">'\s*\+(.*?)'Tél", script, re.S):
            lines = "".join(re.findall(r"'([^']*)'", m.group(1))).split("<br>")
            lines = [line.strip() for line in lines if line.strip()]
            if lines and (postcode_city := re.match(r"(\d{5})\s+(.+)", lines[-1])):
                item["postcode"], item["city"] = postcode_city.groups()
                item["street_address"] = merge_address_lines(lines[:-1])

        apply_category(Categories.OFFICE_INSURANCE, item)
        yield response.follow(item["website"] + "/nos-horaires", self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        oh = OpeningHours()
        for day in response.xpath('//ul[@class="push-agency-days"]/li'):
            day_name = sanitise_day(day.xpath('./p[@class="day-name"]/text()').get(""), DAYS_FR)
            if not day_name:
                continue
            periods = day.xpath('./div[p[@class="day-period-value"]]')
            if not periods:
                oh.set_closed(day_name)
            for period in periods:
                # Periods marked "sur RDV" are by appointment only
                if "RDV" in period.xpath('normalize-space(./p[@class="day-hour-info"])').get("").upper():
                    continue
                time_range = period.xpath('normalize-space(./p[@class="day-period-value"])').get("")
                if m := re.fullmatch(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", time_range):
                    oh.add_range(day_name, *m.groups())
        item["opening_hours"] = oh
        yield item
