import re

import scrapy
from scrapy.linkextractors import LinkExtractor

from locations.categories import Categories, apply_category
from locations.geo import city_locations
from locations.google_url import extract_google_position
from locations.hours import DAYS_DE, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class JetATSpider(scrapy.Spider):
    name = "jet_at"
    item_attributes = {"brand": "Jet", "brand_wikidata": "Q568940"}

    def start_requests(self):
        url = "https://www.jet-tankstellen.at/de/tankstellen/suchergebnisse.php"
        postcodes = [2130, 2540, 3910, 4400, 4780, 4820, 7000, 7400, 8472, 8600, 8753, 9900]
        for postcode in postcodes:
            yield scrapy.FormRequest(
                url=url,
                method="post",
                formdata={"suche": str(postcode)},
            )
        MIN_POPULATION = 45000
        for city in city_locations("AT", min_population=MIN_POPULATION):
            yield scrapy.FormRequest(
                url=url,
                method="post",
                formdata={"suche": city["name"]},
                cb_kwargs=dict(city=city["name"]),
            )

    def parse(self, response, **kwargs):
        links = LinkExtractor(
            allow=(
                r"/de/tankstellen/suchergebnisse\.php\?plz=\d+$",
                r"/de/tankstellen/details\.php\?TSNr=.*&plzsearch=\d+$",
            )
        ).extract_links(response)
        for link in links:
            if "suchergebnisse.php?plz=" in link.url and link.url is not response.url:
                yield response.follow(link.url, callback=self.parse, cb_kwargs=kwargs)
            elif "details.php?TSNr=" in link.url:
                yield response.follow(link.url, callback=self.parse_stations, cb_kwargs=kwargs)

    def parse_stations(self, response, **kwargs):
        item = Feature()
        address_element = response.xpath('//*[@class="detail_top_inhalt1"]//p/text()').getall()
        item["street_address"] = address_element[0]
        item["postcode"] = re.search(r"\d{4}", address_element[1]).group(0)
        item["addr_full"] = ", ".join(address_element[:2]).strip()
        item["phone"] = response.xpath('//*[@title="anrufen"]/text()').get()
        item["city"] = kwargs.get("city")
        item["website"] = response.url
        match = re.search(r"TSNr=(.*)&plzsearch=", response.url)
        item["ref"] = match.group(1) if match else item["website"]
        extract_google_position(item, response)

        timing = response.xpath('//*[@class="detail_top_inhalt2"]').get()
        item["opening_hours"] = OpeningHours()
        for start_day, end_day, open_time, close_time in re.findall(
            r">\s*(\w+)\s*-\s*(\w+)[:<>\w\s/]*(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", timing
        ):
            for day in day_range(sanitise_day(start_day, DAYS_DE), sanitise_day(end_day, DAYS_DE)):
                item["opening_hours"].add_range(day, open_time, close_time)
        for day, open_time, close_time in re.findall(r">\s*(\w+)[:<>\w\s/]*(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", timing):
            if day := sanitise_day(day, DAYS_DE):
                item["opening_hours"].add_range(day, open_time, close_time)
        apply_category(Categories.FUEL_STATION, item)

        yield item
