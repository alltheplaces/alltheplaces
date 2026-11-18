import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class PocztaPolskaPLSpider(Spider):
    name = "poczta_polska_pl"
    item_attributes = {"brand": "Poczta Polska", "brand_wikidata": "Q168833"}

    async def start(self) -> AsyncIterator[FormRequest]:
        # Each tab returns every location of its kind in one response: post offices and letter boxes.
        for tab in ("tabPostOffice", "tabOutbox"):
            yield FormRequest(
                url="https://www.poczta-polska.pl/wp-content/plugins/pp-poiloader/find-markers.php",
                formdata={
                    "tab": tab,
                    "lng": "19",
                    "lat": "52",
                    "province": "0",
                    "district": "0",
                    "ppmapBox_Days": "dni robocze",
                },
                headers={"Referer": "https://www.poczta-polska.pl/znajdz-punkt/"},
            )

    def parse(self, response, **kwargs):
        for location in response.json():
            item = Feature()
            item["ref"] = location.get("pni")
            item["name"] = location.get("name")
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            if location.get("typ") == "SKRZYNKA_POCZTOWA":
                item["name"] = None
                apply_category(Categories.POST_BOX, item)
            else:
                apply_category(Categories.POST_OFFICE, item)
            yield FormRequest(
                url="https://www.poczta-polska.pl/wp-content/plugins/pp-poiloader/point-info.php",
                formdata={"pointid": str(item["ref"])},
                meta={"item": item},
                callback=self.parse2,
            )

    def parse2(self, response):
        item = response.meta["item"]
        item["phone"] = ";".join(
            response.xpath("//div[contains(@class, 'pp-map-tooltip__phones')]//p/text()").getall()
        ).replace(" ", "")
        addr = response.xpath("//div[contains(@class, 'pp-map-tooltip__adress')]//p/text()").getall()
        item["street"], item["housenumber"] = addr[0].rsplit(" ", 1)
        if isinstance(item["housenumber"], str) and item["housenumber"].lower() == "b/n":
            item["housenumber"] = None
        item["postcode"], item["city"] = addr[1].split(" ", 1)
        if item["extras"].get("amenity") == "post_box":
            # The emptying time is for working days (the search's ppmapBox_Days); boxes without one say
            # to check the plate on the box.
            emptying = " ".join(
                response.xpath("//div[contains(@class, 'pp-map-tooltip__box-emptying-hours')]//p//text()").getall()
            )
            if times := sorted(set(re.findall(r"\b([01]\d|2[0-3]):([0-5]\d)\b", emptying))):
                item["extras"]["collection_times"] = "Mo-Fr " + ",".join(f"{h}:{m}" for h, m in times)
            item.pop("phone", None)
            yield item
            return
        hours_text = " ".join(
            filter(
                None, map(str.strip, response.xpath('//div[@class="pp-map-tooltip__opening-hours"]//text()').getall())
            )
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_PL)

        yield item
