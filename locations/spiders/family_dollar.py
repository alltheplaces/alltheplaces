# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class FamilyDollarSpider(scrapy.Spider):
    name = "family_dollar"
    item_attributes = {"brand": "Family Dollar", "brand_wikidata": "Q5433101"}
    allowed_domains = ["familydollar.com"]
    start_urls = ("https://locations.familydollar.com",)

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for line in store_hours:
            # Applebees always seems to have a single dow
            # in each opening hours object
            day = line["dayOfWeek"][0][:2]

            match = re.search(r"^(\d{1,2}):(\d{2}) ([AP]M)$", line["opens"])
            (f_hr, f_min, f_ampm) = match.groups()
            match = re.search(r"^(\d{1,2}):(\d{2}) ([AP]M)$", line["closes"])
            (t_hr, t_min, t_ampm) = match.groups()

            f_hr = int(f_hr)
            if f_ampm == "PM":
                f_hr += 12

            t_hr = int(t_hr)
            if t_ampm == "PM":
                t_hr += 12

            hours = "{:02d}:{}-{:02d}:{}".format(
                f_hr,
                f_min,
                t_hr,
                t_min,
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

    def address(self, address):
        if not address:
            return None

        addr_tags = {
            "addr_full": address["streetAddress"],
            "city": address["addressLocality"],
            "state": address["addressRegion"],
            "postcode": address["postalCode"],
            "country": address["addressCountry"],
        }

        return addr_tags

    def parse(self, response):
        urls = response.xpath('//div[@class="itemlist"]/a/@href')
        for path in urls:
            yield scrapy.Request(response.urljoin(path.extract()))

        store_urls = response.xpath('//div[@class="itemlist forcitypage"]/li/a/@href')
        if store_urls:
            for store_url in store_urls:
                yield scrapy.Request(
                    response.urljoin(store_url.extract()), callback=self.parse_store
                )

    def parse_store(self, response):
        json_data = response.xpath('//head/script[@type="application/ld+json"]/text()')[
            1
        ].extract()
        data = json.loads(json_data)

        properties = {
            "phone": data["telephone"],
            "website": data["url"],
            "ref": data["@id"],
            "lon": float(data["geo"]["longitude"]),
            "lat": float(data["geo"]["latitude"]),
        }

        address = self.address(data["address"])
        if address:
            properties.update(address)

        try:
            hours = self.store_hours(data["openingHoursSpecification"])
            if hours:
                properties["opening_hours"] = hours
        except:
            pass

        yield GeojsonPointItem(**properties)
