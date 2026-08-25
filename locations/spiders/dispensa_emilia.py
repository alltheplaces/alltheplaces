import re
from typing import Any

import chompjs
import scrapy
from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.items import Feature


class DispensaEmiliaSpider(scrapy.Spider):
    name = "dispensa_emilia"
    item_attributes = {"brand": "Dispensa Emilia", "brand_wikidata": "Q140867853"}
    start_urls = ["https://www.dispensaemilia.it/it/i-ristoranti.html"]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script_content = response.xpath('//script[contains(text(), "stores =")]/text()').get()
        if not script_content:
            return

        js_str = script_content.split("stores =")[-1]
        data = chompjs.parse_js_object(js_str)

        for store in data:
            try:
                lat = float(store.get("lat"))
                lon = float(store.get("lng"))
            except (ValueError, TypeError):
                continue

            if lat == 0 and lon == 0:
                continue

            item = Feature()
            item["ref"] = str(store.get("id") or store.get("idSedi"))
            item["lat"] = lat
            item["lon"] = lon

            title = store.get("titolo", "").strip()
            item["branch"] = title.removeprefix("Dispensa Emilia").strip(" -") or None

            item["street_address"] = store.get("indirizzo")
            item["city"] = store.get("comune")
            item["postcode"] = store.get("cap")
            item["state"] = store.get("provincia")
            item["phone"] = store.get("telefono")
            item["email"] = store.get("email") or None
            item["website"] = "https://www.dispensaemilia.it/it/i-ristoranti.html"

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "italian;regional"

            if orari_raw := store.get("orari"):
                text = " ".join(Selector(text=orari_raw).xpath("//text()").getall()).strip()
                text = re.sub(r"(?i)Orari\s*:?", "", text)
                text = re.sub(r"(?i)Servizi.*", "", text).strip()
                try:
                    oh = OpeningHours()
                    oh.add_ranges_from_string(
                        text,
                        days=DAYS_IT,
                        named_day_ranges=NAMED_DAY_RANGES_IT,
                        named_times=NAMED_TIMES_IT,
                        closed=CLOSED_IT,
                    )
                    item["opening_hours"] = oh
                except Exception:
                    pass

            yield item
