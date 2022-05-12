# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class AsdaSpider(scrapy.Spider):
    name = "asda"
    item_attributes = {"brand": "Asda", "brand_wikidata": "Q297410"}
    allowed_domains = ["asda.com", "virtualearth.net", "bing.com"]
    start_urls = (
        "https://spatial.virtualearth.net/REST/v1/data/2c85646809c94468af8723dd2b52fcb1/AsdaStoreLocator/asda_store?$callback=resultCallback&jsonp=resultCallback&key=AtAs6PiQ3e0HE187rJgUEqvoKcKfTklRKTvCN1X1mpumYE-Z4VQFvx62X7ff13t6&spatialFilter=nearby(53.4795913696289,-2.24873995780945,400)&$select=imp_id,url_key,Latitude,Longitude,name,__Distance,store_photo_url,street,town,post_code,store_manager,telephone,asda_store_type,asda_store_type_display,opening_times_withheld_until_timestamp,has_holiday_opening_times,asda_service_bounty_packs,asda_service_24_hour,asda_service_community_champion,asda_service_pharmacy,asda_service_petrol_station,asda_service_opticians,asda_service_george,asda_service_click_collect,asda_service_grocery_click_collect,asda_service_baby_changing,asda_service_travel_money,asda_service_travel_money_click_collect,asda_service_instant_photo_print_centre,asda_service_photo_department_or_instant_print,asda_service_electric_car_charging,asda_service_scan_go,asda_store_type_living&$top=800&$format=json&$skip=",
    )

    def time_str(self, time):
        time = time.replace("Midnight", "12pm")
        match = re.search(r"(\d{1,2})(pm|am|mp)\s*-\s*(\d{1,2})(pm|am|mp)", time)
        if not match:
            return ""

        stri = str(int(match[1]) + (12 if match[2] in ["pm", "mp"] else 0)) + ":00-"
        stri += str(int(match[3]) + (12 if match[4] in ["pm", "mp"] else 0)) + ":00"
        return stri

    def store_hours(self, store_hours):
        if not store_hours:
            return None

        lastday = DAYS[0]
        lasttime = self.time_str(store_hours[0])
        opening_hours = lastday

        for day in range(1, 7):  # loop by days
            if day == len(store_hours):
                break
            str_curr = self.time_str(store_hours[day])

            if str_curr != lasttime:
                if lastday == DAYS[day - 1]:
                    opening_hours += " " + lasttime + ";" + DAYS[day]
                else:
                    opening_hours += (
                        "-" + DAYS[day - 1] + " " + lasttime + ";" + DAYS[day]
                    )
                lasttime = str_curr
                lastday = DAYS[day]
        if lasttime != "":
            if lastday == DAYS[day]:
                opening_hours += " " + str_curr
            else:
                opening_hours += "-" + DAYS[6] + " " + str_curr
        else:
            opening_hours = opening_hours.rstrip(DAYS[6])

        return opening_hours.rstrip(";").strip()

    def parse(self, response):
        try:
            start = response.meta["start"]
        except Exception:
            start = 250

        shops = json.loads(response.text.rstrip(")").lstrip("resultCallback("))["d"][
            "results"
        ]
        for place in shops:
            yield scrapy.Request(
                "https://storelocator.asda.com/store/" + place["url_key"],
                callback=self.parse_shop,
                meta={
                    "lat": float(place["Latitude"]),
                    "lon": float(place["Longitude"]),
                    "phone": place["telephone"],
                    "website": "https://storelocator.asda.com/store/"
                    + place["url_key"],
                    "ref": place["imp_id"] + "-" + place["name"],
                    "addr_full": place["street"],
                    "postcode": place["post_code"],
                    "city": place["town"],
                    "country": "UK",
                },
            )
        if len(shops) == 250:
            yield scrapy.Request(
                self.start_urls[0] + str(start),
                callback=self.parse,
                meta={"start": start + 250},
            )

    def parse_shop(self, response):
        times = self.store_hours(
            response.xpath('//div[@id="opening-times"]//tr/td[2]/text()').extract()
        )

        yield GeojsonPointItem(
            opening_hours=times,
            lat=response.meta["lat"],
            lon=response.meta["lon"],
            phone=response.meta["phone"],
            website=response.meta["website"],
            ref=response.meta["ref"],
            addr_full=response.meta["addr_full"],
            postcode=response.meta["postcode"],
            city=response.meta["city"],
            country=response.meta["country"],
        )
