import re

import scrapy

from locations.items import Feature


class VillageInnSpider(scrapy.Spider):
    name = "village_inn"
    item_attributes = {"brand": "Village Inn", "brand_wikidata": "Q7930659"}
    allowed_domains = ["www.villageinn.com"]
    start_urls = ("http://www.villageinn.com/locations/bystate.php",)

    def parse(self, response):
        selector = scrapy.Selector(response)
        links = selector.css("a.animatedlink::attr(href)")

        for link in links:
            yield scrapy.Request(response.urljoin(link.extract().strip()), callback=self.parse_link)

    def parse_link(self, response):
        website = response.xpath('//head/meta[@property="og:url"]/@content').extract_first()
        ref = website.split("/")[-1]
        lat = response.css("#h_lat::attr(value)").extract_first()
        lng = response.css("#h_lng::attr(value)").extract_first()

        blocks = response.css("#location_subcontainer .block")

        hours_text = response.xpath(
            '//span[@class="block hours"]/span[@class="hoursTime" or @class="hoursDay"]/text()'
        ).extract()

        properties = {
            "ref": ref,
            "website": website,
            "lat": float(lat),
            "lon": float(lng),
            "opening_hours": self.hours(hours_text),
        }

        address = self.address(blocks[0])
        if address:
            properties.update(address)

        yield Feature(**properties)

    def address(self, data):
        address = data.css(".block::text").extract()

        address = list(filter(lambda a: not a.startswith("Fax"), address))

        street = address[2].strip()
        city_state_zip = address[-3].strip()
        city, state_zip = city_state_zip.split(",", 1)
        state, zipcode = state_zip.strip().split()
        phone = address[-2].strip().replace("Phone: ", "")

        ret = {
            "addr_full": street,
            "city": city,
            "state": state,
            "postcode": zipcode,
            "phone": phone,
        }

        return ret

    def hours(self, data):
        this_day_group = dict()
        day_groups = []
        for i in range(7):
            day = data[i * 3][:2]
            match = re.search(r"(\d{1,2}):(\d{2}) (AM|PM)", data[i * 3 + 1])
            f_hr, f_min, f_ampm = match.groups()

            match = re.search(r"(\d{1,2}):(\d{2}) (AM|PM)", data[i * 3 + 2])
            t_hr, t_min, t_ampm = match.groups()

            f_hr = int(f_hr)
            if f_ampm == "PM":
                f_hr += 12
            if f_ampm == "AM" and f_hr == 12:
                f_hr -= 12

            t_hr = int(t_hr)
            if t_ampm == "PM":
                t_hr += 12
            if t_ampm == "AM" and t_hr == 12:
                t_hr -= 12

            hours = "%02d:%s-%02d:%s" % (
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
