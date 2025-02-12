import json
import re
from typing import Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Request, Response

from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import Feature


class BonmarcheGBSpider(Spider):
    name = "bonmarche_gb"
    item_attributes = {"brand": "Bonmarché", "brand_wikidata": "Q4942146"}

    def start_requests(self) -> Iterable[Request]:
        country = "GB"
        language = "en-GB"
        for city in city_locations("GB", 500):
            lat, lon = city["latitude"], city["longitude"]
            yield self.make_request(lat, lon, country, 1, language)

    def make_request(self, lat, lon, country_code: str, start_index: int, language: str) -> Request:
        url = f"https://www.bonmarche.co.uk/on/demandware.store/Sites-BONMARCHE-GB-Site/en_GB/Stores-FindStores?lat={lat}&lng={lon}&dwfrm_storelocator_findbygeocoord=Search&format=ajax&amountStoresToRender=5&checkout=false"
        return Request(
            url,
            meta={
                "lat": lat,
                "lon": lon,
                "country_code": country_code,
                "start_index": start_index,
                "language": language,
            },
            callback=self.parse,
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        if response.xpath('//div[@id = "map"]'):
            geo = json.loads(response.xpath('//div[@id = "map"]//@data-results').get())
            data = response.xpath('//li[@class = "stores-list-item"]')
            for location in data:
                item = Feature()
                addr = location.xpath('div/div/div[@class = "store-address"]').get()
                item["addr_full"] = re.sub("(</?div[^>]*>|<br>|\n)", "", addr)
                if "Bonmarch" in item["addr_full"]:
                    item["addr_full"] = re.sub("Bonmarch[^,]+,", "", item["addr_full"])
                tel = location.xpath('div/div/div/a[contains(@href, "tel:")]/text()').get()
                if tel:
                    item["phone"] = re.sub("(Tel:|\n)", "", tel)
                item["ref"] = location.xpath("a//@data-storeid").get()
                item["branch"] = location.xpath('a[@class = "store-link accordion-toggle"]//text()').get()
                for store in geo["stores"]:
                    if store["id"] == item["ref"]:
                        item["lat"] = store["lat"]
                        item["lon"] = store["lng"]
                slug = location.xpath('div/div/a[@class = "button"]/@href').get()
                item["website"] = urljoin("https://www.bonmarche.co.uk", slug)

                table = location.xpath('div/div/div/div/div[@class = "storehours"]/table//tr')
                opening_hours = OpeningHours()
                for row in table:
                    day = row.xpath('td[@class = "storeday"]//text()').get()
                    start = row.xpath('td[@class = "storehours-from"]//text()').get().replace(".", ":")
                    end = row.xpath('td[@class = "storehours-to"]//text()').get().replace(".", ":")
                    # '--' or closed
                    if bool(re.search(r"\d", start)) == 0:
                        continue
                    # '10:00'
                    if "m" not in start:
                        if int(start.split(":")[0]) > 11:
                            start = start + "pm"
                        else:
                            start = start + "am"
                    # '4:00' - all closing times must be pm?
                    if "m" not in end:
                        end = end + "pm"
                    # '17:30pm'
                    if int(end.split(":")[0]) > 12:
                        newhour = int(end.split(":")[0]) - 12
                        end = str(newhour) + ":" + end.split(":")[1]
                    # '10am'
                    if ":" not in start:
                        start = start.replace("am", ":00am").replace("pm", ":00pm")
                    if ":" not in end:
                        end = end.replace("am", ":00am").replace("pm", ":00pm")
                    # there's also a 'om' which I haven't corrected
                    if "am" not in end and "pm" not in end:
                        continue
                    opening_hours.add_range(day=day, open_time=start, close_time=end, time_format="%I:%M%p")
                item["opening_hours"] = opening_hours
                yield item
