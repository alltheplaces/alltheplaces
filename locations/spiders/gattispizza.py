# -*- coding: utf-8 -*-
import scrapy
import json
import traceback
import re
from locations.items import GeojsonPointItem

URL = "http://gattispizza.com/wp-admin/admin-ajax.php"
HEADERS = {
    "Accept-Language": "en-US,en;q=0.8,ru;q=0.6",
    "Origin": "http://gattispizza.com",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "application/json, text/plain, */*",
    "Referer": "http://gattispizza.com/locationmain/",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}


class GattispizzaSpider(scrapy.Spider):
    name = "gattispizza"
    item_attributes = {"brand": "Gatti's Pizza", "brand_wikidata": "Q5527509"}
    allowed_domains = ["gattispizza.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        form_data = {"action": "udfd_update_locations", "data": "3211"}

        yield scrapy.http.FormRequest(
            url=URL,
            method="POST",
            formdata=form_data,
            headers=HEADERS,
            callback=self.parse,
        )

    def parse(self, response):
        stores = response.json()

        for store in stores:
            props = {
                "lat": store["lat"],
                "lon": store["long"],
                "ref": str(store["ID"]),
                "name": store["post_title"],
                "addr_full": store["formatted_address"],
                "street": store["street"],
                "country": store["country"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zipcode"],
                "website": store["post_url"],
            }

            yield scrapy.Request(
                store["post_url"],
                meta={"product": props},
                callback=self.parse_detail_product,
            )

    def parse_detail_product(self, response):
        product = response.meta.get("product")
        time = response.xpath(
            '//div[@class="medium-4 columns location-hours"]//p/text()'
        ).extract()
        opening_hours = time[0] if time else None

        try:
            phone_list = json.loads(
                re.search("var phonelist = (.*?)}}", response.body).group(1) + "}}"
            )
            product["phone"] = phone_list.get(product.get("ref")).get("phone")
        except:
            product["phone"] = ""
            self.log("Error while parsing the json data".format(traceback.format_exc()))

        yield GeojsonPointItem(
            lat=product.get("lat"),
            lon=product.get("lon"),
            ref=str(product.get("ref")),
            name=product.get("name"),
            addr_full=product.get("addr_full"),
            street=product.get("street"),
            country=product.get("country"),
            city=product.get("city"),
            state=product.get("state"),
            postcode=product.get("postcode"),
            website=product.get("website"),
            phone=product.get("phone"),
            opening_hours=opening_hours,
        )
        form_data = {"action": "udfd_update_locations", "data": product.get("postcode")}

        yield scrapy.http.FormRequest(
            url=URL,
            method="POST",
            formdata=form_data,
            headers=HEADERS,
            callback=self.parse,
        )
