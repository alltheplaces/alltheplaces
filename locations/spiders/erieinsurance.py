# -*- coding: utf-8 -*-
import json
import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

am_pm = lambda s: re.sub(r" ?([ap])\.*m\.*", lambda x: x[1] + "m", s)


class ErieInsuranceSpider(SitemapSpider):
    name = "erieinsurance"
    item_attributes = {"brand": "Erie Insurance", "brand_wikidata": "Q5388314"}
    allowed_domains = ["www.erieinsurance.com"]
    sitemap_urls = ["https://www.erieinsurance.com/robots.txt"]
    sitemap_rules = [(r"^https://www.erieinsurance.com/agencies/.", "parse")]

    def parse(self, response):
        script = response.xpath(
            '//script/text()[contains(.,"agencyInformation")]'
        ).get()
        data = json.decoder.JSONDecoder().raw_decode(
            script, script.index("{", script.index("agencyInformation ="))
        )[0]

        opening_hours = None
        hours_obj = data["agencyInfo"]["businessHoursOperationDescription"]
        if hours_obj.startswith('{"'):
            hours = json.loads(hours_obj)
            opening_hours = OpeningHours()
            for row in hours["HoursOfOperation"]:
                if any(
                    t in ["Closed", None, ""]
                    for t in [row["StartTime"], row["EndTime"]]
                ):
                    continue
                open_time = am_pm(row["StartTime"])
                close_time = am_pm(row["EndTime"])
                day = row["DayName"][:2]
                opening_hours.add_range(day, open_time, close_time, "%I:%M%p")

        agentContact = dict((x["type"], x["value"]) for x in data["agentContact"])
        if ("Fax", "0") in agentContact.items():
            del agentContact["Fax"]

        properties = {
            "ref": response.url,
            "lat": data["address"]["geoCode"]["latitude"],
            "lon": data["address"]["geoCode"]["longitude"],
            "name": data["agencyName"],
            "street_address": data["address"]["line1"],
            "city": data["address"]["city"],
            "state": data["address"]["state"],
            "postcode": data["address"]["zip"],
            "website": agentContact.get("Website"),
            "phone": agentContact.get("Phone"),
            "extras": {"fax": agentContact.get("Fax")},
            "opening_hours": opening_hours and opening_hours.as_opening_hours() or None,
        }
        yield GeojsonPointItem(**properties)
