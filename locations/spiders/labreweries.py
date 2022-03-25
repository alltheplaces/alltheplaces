# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class LaBreweriesSpider(scrapy.Spider):
    name = "labreweries"
    allowed_domains = ["labeerhop.com"]
    start_urls = ("http://labeerhop.com/breweries-sitemap.xml",)

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for day in store_hours:
            day = day.replace("  :-", " 12:00 -")
            day = day.split("<h5>Hours</h5>")[1].strip("<br>").strip("</aside>")
            match = re.search(r"(closed|(\d{1,2})\S.\s*-\s*(\d{1,2})\S.)", day.lower())
            open("/tmp/test1.txt", "w").write(str(day))
            (dow, f_hr, t_hr) = match.groups()
            day_short = dow[:2]

            f_hr = int(f_hr)
            t_hr = int(t_hr)

            hours = "{:02d}-{:02d}".format(
                f_hr,
                t_hr,
            )

            if not this_day_group:
                this_day_group = {
                    "from_day": day_short,
                    "to_day": day_short,
                    "hours": hours,
                }
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {
                    "from_day": day_short,
                    "to_day": day_short,
                    "hours": hours,
                }
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day_short

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
            "addr_full": address[0].split(",")[0].strip(),
            "city": address[0].split(",")[1].strip(),
            "state": address[0].split(" ")[-2].strip(),
            "postcode": address[0].split(" ")[-1].strip(),
        }

        return addr_tags

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        for path in city_urls:
            if path not in "http://labeerhop.com/breweries/1056/":
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):

        properties = {
            "website": response.xpath(
                '//head/link[@rel="canonical"]/@href'
            ).extract_first(),
            "ref": str(
                response.xpath("/html/body/div[1]/div[1]/header/h1/text()").extract()
            ).strip("['']"),
            "opening_hours": re.sub(
                r"\s+",
                " ",
                response.xpath('//*[@id="content"]/div/div[2]/div[3]')
                .extract()[0]
                .split('<h5 class="mb-2">Hours</h5>')[1]
                .replace("<br>", "")
                .replace("</div>", "")
                .replace("\t", " ")
                .replace("\n", "")
                .replace("\r", " "),
            ).strip(),
            # 'lon': float(data['geo']['longitude']),   # not lon on page
            # 'lat': float(data['geo']['latitude']),    # not lat on page
        }

        address = self.address(
            response.xpath("/html/body/div[1]/div[1]/aside/address/text()").extract()
        )
        if address:
            properties.update(address)

        yield GeojsonPointItem(**properties)
