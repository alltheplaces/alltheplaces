# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class CulversSpider(scrapy.Spider):
    name = "culvers"
    item_attributes = {"brand": "Culver's", "brand_wikidata": "Q1143589"}
    allowed_domains = ["hosted.where2getit.com"]
    start_urls = (
        'https://hosted.where2getit.com/culvers/2015/ajax?&xml_request=<request><appkey>1099682E-D719-11E6-A0C4-347BDEB8F1E5</appkey><formdata id="locatorsearch"><dataview>store_default</dataview><order>rank,_distance</order><limit>5000</limit><stateonly>0</stateonly><geolocs><geoloc><addressline></addressline><longitude>-98.369</longitude><latitude>39.417</latitude><country></country></geoloc></geolocs><searchradius>2500</searchradius></formdata></request>',
    )
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def store_hours(self, store_hours):
        day_groups = []
        days = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
        this_day_group = dict()
        for day, hours in zip(days, store_hours):
            hours = "{}:{}-{}:{}".format(
                hours[0][0:2],
                hours[0][2:4],
                hours[1][0:2],
                hours[1][2:4],
            )

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        data = response.xpath("//poi")

        for store in data:
            properties = {
                "ref": str(store.xpath("number/text()").extract_first()),
                "name": store.xpath("name/text()").extract_first(),
                "opening_hours": self.store_hours(
                    json.loads(store.xpath("bho/text()").extract_first())
                ),
                "website": store.xpath("url/text()").extract_first(),
                "addr_full": store.xpath("address1/text()").extract_first(),
                "city": store.xpath("city/text()").extract_first(),
                "state": store.xpath("state/text()").extract_first(),
                "postcode": store.xpath("postalcode/text()").extract_first(),
                "country": store.xpath("country/text()").extract_first(),
                "lon": float(store.xpath("longitude/text()").extract_first()),
                "lat": float(store.xpath("latitude/text()").extract_first()),
            }

            phone = store.xpath("phone/text()")
            if phone:
                properties["phone"] = phone.extract_first()

            yield GeojsonPointItem(**properties)

        else:
            self.logger.info("No results")
