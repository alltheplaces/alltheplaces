from urllib.parse import quote

import scrapy
from scrapy import FormRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class PutkaPLSpider(scrapy.Spider):
    name = "putka_pl"
    item_attributes = {"brand": "Putka", "brand_wikidata": "Q113093586"}
    host = "https://www.putka.pl"
    start_urls = [f"{host}/ajax/googleMaps.php"]

    def start_requests(self):
        yield FormRequest(
            url=self.start_urls[0],
            method="POST",
            formdata=dict(action="wszystkie"),  # Polish for "all" (stores)
        )

    def parse(self, response):
        data = response.json()
        for ref, coordinates in zip(data["idp"].split(";")[:-1], data["punkty"].split(";")[:-1]):
            lat, lon = coordinates.split(",")[:2]
            url = f"{self.host}/sklepy-firmowe/1/0/{ref}"
            properties = {
                "ref": ref,
                "lat": float(lat),
                "lon": float(lon),
                "website": url,
            }
            yield scrapy.Request(url, callback=self.parse_store, cb_kwargs=properties)

    def parse_store(self, response, **kwargs):
        store_details = response.xpath("//div[contains(@class, 'sklep-details')]")
        street_address, post_code_city, phone = store_details.xpath("//table/tr[2]/td/text()").getall()
        post_code = post_code_city.split(" ")[0].strip()
        city = " ".join(post_code_city.strip().split(" ")[1:])
        phone = phone.strip().removeprefix("tel: ")
        image_path = store_details.xpath("//img[contains(@src, 'upload/sklepy')]/@src").get()
        opening_hours = OpeningHours()
        opening_hours_texts = store_details.xpath("//tr[5]/td/text()").getall()
        half_opening_hours_len = len(opening_hours_texts) // 2
        for i in range(half_opening_hours_len):
            opening_hours_text = (
                opening_hours_texts[i].strip().replace(".", "")
                + ": "
                + opening_hours_texts[half_opening_hours_len + i].strip()
            )
            opening_hours.add_ranges_from_string(ranges_string=opening_hours_text, days=DAYS_PL)
        properties = {
            "street_address": street_address.strip(),
            "city": city,
            "phone": phone,
            "postcode": post_code,
            "image": f"{self.host}/{quote(image_path)}",
            "opening_hours": opening_hours,
        }
        properties.update(kwargs)
        item = Feature(**properties)
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
