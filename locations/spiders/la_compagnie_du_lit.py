import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature


class LaCompagnieDuLitSpider(Spider):
    name = "la_compagnie_du_lit"
    item_attributes = {"name": "La Compagnie du Lit", "brand": "La Compagnie du Lit", "brand_wikidata": "Q120749952"}
    start_urls = ["https://www.lacompagniedulit.com/magasins/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//div[@data-id][contains(@class, "store-block ")]'):
            title = store.xpath('.//a[contains(@class, "store-block-title")]')
            info = store.xpath('.//p[@class="txt-mag"]')
            item = Feature()
            item["ref"] = store.xpath("@data-id").get()
            item["lat"] = store.xpath("@data-latitude").get()
            item["lon"] = store.xpath("@data-longitude").get()
            item["branch"] = re.sub(r"^(La )?Compagnie du Lit ", "", title.xpath("normalize-space(text())").get())
            item["website"] = title.xpath("@href").get()
            item["street_address"] = re.sub(
                r"\s+\d{5}\s.*$", "", info.xpath('normalize-space(span[@class="address1"])').get()
            )
            item["postcode"] = info.xpath('normalize-space(span[@class="postcode"])').get()
            item["city"] = info.xpath('normalize-space(span[@class="city"])').get()
            item["phone"] = store.xpath('.//a[@class="tel-mag"]/@href').get()

            item["opening_hours"] = OpeningHours()
            for line in store.xpath('.//div[@class="horaire"]/p[contains(@class, "schedule-line")]'):
                day = sanitise_day(line.xpath('normalize-space(strong[@class="day"])').get(), DAYS_FR)
                hours = line.xpath('normalize-space(span[@class="hours"])').get()
                if not day:
                    continue
                if hours.lower() == "fermé":
                    item["opening_hours"].set_closed(day)
                for start_h, start_m, end_h, end_m in re.findall(r"(\d+)h(\d*)\s*-\s*(\d+)h(\d*)", hours):
                    item["opening_hours"].add_range(
                        day, f"{start_h}:{start_m or '00'}", f"{end_h}:{end_m or '00'}", "%H:%M"
                    )
            apply_category(Categories.SHOP_BED, item)
            yield item
