import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, DELIMITERS_FR, OpeningHours, sanitise_day
from locations.items import Feature


class LaFeeMarabouteeSpider(Spider):
    name = "la_fee_maraboutee"
    item_attributes = {"brand": "La Fée Maraboutée", "brand_wikidata": "Q105429377", "name": "La Fée Maraboutée"}

    async def start(self) -> AsyncIterator[Request]:
        # Shopify redirects "Accept-Language: en" to a machine translated en-us store
        yield Request("https://lafeemaraboutee.fr/pages/boutiques", headers={"Accept-Language": "fr"})

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.xpath("//template[starts-with(@name, 'store_')]"):
            key = store.xpath("@name").get()
            item = Feature()
            item["ref"] = key.removeprefix("store_")
            item["lat"] = store.xpath("@latitude").get()
            item["lon"] = store.xpath("@longitude").get()
            item["branch"] = re.sub(
                r"^La f[ée]e marabout[ée]e\s*",
                "",
                store.xpath('normalize-space(.//*[contains(@class, "modal-store-name")])').get(),
                flags=re.IGNORECASE,
            )
            address = store.xpath('.//*[@class="map-place-list__modal-address"]')
            item["street_address"] = address.xpath("normalize-space(./text())").get()
            if m := re.match(
                r"([\w ]+?)\s+(\D.*)$",
                address.xpath('normalize-space(.//*[@class="map-place-list__modal-city"])').get().replace("\xa0", " "),
            ):
                item["postcode"], item["city"] = m.groups()
                if not re.search(r"[A-Z]", item["postcode"]):
                    item["postcode"] = item["postcode"].replace(" ", "")
            item["country"] = address.xpath('normalize-space(.//*[@class="map-place-list__modal-country"])').get()
            item["phone"] = store.xpath('.//a[starts-with(@href, "callto:")]/text()').get()
            item["website"] = response.xpath(
                f'//*[@map-target="{key}"]//a[contains(@href, "/pages/store/")]/@href'
            ).get()

            item["opening_hours"] = OpeningHours()
            hours = store.xpath('.//*[@class="map-place-list__modal-store-opening-hours"]/text()').getall()
            for line in "|".join(hours).split("|"):
                if "chaque" in line:  # "Le 1er dimanche de chaque mois"
                    continue
                if re.search(r"\d{4} :", line):  # "jeudi 29 octobre 2026 : de 10:30 à 13:00 et de 14:00 à 19:00"
                    day = sanitise_day(line.split()[0], DAYS_FR)
                    for open_time, close_time in re.findall(r"(\d{1,2}:\d{2}) à (\d{1,2}:\d{2})", line):
                        item["opening_hours"].add_range(day, open_time, close_time)
                else:  # "Du lundi au vendredi 10:00–19:30" or "Du lundi au samedi : 10h-20h30"
                    line = re.sub(r"(\d{1,2})h(\d{2})?", lambda m: f"{m[1]}:{m[2] or '00'}", line)
                    item["opening_hours"].add_ranges_from_string(line, days=DAYS_FR, delimiters=DELIMITERS_FR)

            if item["country"] == "BE" and len(item.get("postcode") or "") == 5:
                item["postcode"] = item["postcode"].removeprefix("0")  # "02 000" for 2000

            apply_category(Categories.SHOP_CLOTHES, item)
            item["extras"]["clothes"] = "women"
            yield item
