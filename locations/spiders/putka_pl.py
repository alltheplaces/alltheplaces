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
        storeDetails = response.xpath("//div[contains(@class, 'sklep-details')]")
        streetAddress, postCodeCity, phone = storeDetails.xpath("//table/tr[2]/td/text()").getall()
        postCode = postCodeCity.split(" ")[0].strip()
        city = " ".join(postCodeCity.strip().split(" ")[1:])
        phone = phone.strip().removeprefix("tel: ")
        imagePath = storeDetails.xpath("//img[contains(@src, 'upload/sklepy')]/@src").get()
        openingHours = OpeningHours()
        openingHoursTexts = storeDetails.xpath("//tr[5]/td/text()").getall()
        halfOpeningHoursLen = len(openingHoursTexts) // 2
        for i in range(halfOpeningHoursLen):
            openingHoursText = (
                openingHoursTexts[i].strip().replace(".", "")
                + ": "
                + openingHoursTexts[halfOpeningHoursLen + i].strip()
            )
            openingHours.add_ranges_from_string(ranges_string=openingHoursText, days=DAYS_PL)
        properties = {
            "street_address": streetAddress.strip(),
            "city": city,
            "phone": phone,
            "postcode": postCode,
            "image": f"{self.host}/{quote(imagePath)}",
            "opening_hours": openingHours,
        }
        properties.update(kwargs)
        item = Feature(**properties)
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
