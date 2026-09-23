import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class DistricenterFRSpider(Spider):
    name = "districenter_fr"
    item_attributes = {"brand": "DistriCenter", "brand_wikidata": "Q121840469"}
    start_urls = ["https://www.districenter.fr/magasins"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.css("article.store-item"):
            item = Feature()
            item["ref"] = store.attrib["data-id-store"]
            item["lat"] = store.attrib["data-lat"]
            item["lon"] = store.attrib["data-lon"]
            item["branch"] = store.css('[itemprop="name"]::text').get("").strip()
            item["street_address"] = merge_address_lines(store.css('[itemprop="streetAddress"]::text').getall())
            # The microdata "addressRegion" actually holds the postcode.
            item["postcode"] = store.css('[itemprop="addressRegion"]::text').get()
            item["city"] = store.css('[itemprop="addressLocality"]::text').get("").strip()
            item["phone"] = store.css('[itemprop="telephone"]::text').get()
            item["website"] = response.urljoin(store.css("a.store-item__link").attrib["href"])

            item["opening_hours"] = OpeningHours()
            for row in store.css('[itemprop="openingHours"] > div'):
                day = DAYS_FR.get(row.xpath("./span[1]/text()").get("").strip())
                hours = " ".join(row.xpath("./span[2]//text() | ./text()").getall()).strip()
                if not day or not hours:
                    continue
                if "ferm" in hours.lower():
                    item["opening_hours"].set_closed(day)
                    continue
                times = re.findall(r"\d{1,2}[:h]\d{2}", hours)
                for open_time, close_time in zip(times[0::2], times[1::2]):
                    item["opening_hours"].add_range(day, open_time.replace("h", ":"), close_time.replace("h", ":"))

            if "fermeture définitive" in " ".join(store.css(".cms-content ::text").getall()).lower():
                set_closed(item)

            yield item
