import re

import scrapy

from locations.items import Feature


class FarmBoySpider(scrapy.Spider):
    name = "farmboy"
    item_attributes = {"brand": "Farmboy", "brand_wikidata": "Q5435469"}
    allowed_domains = ["www.farmboy.ca"]
    start_urls = ("https://www.farmboy.ca/about-us/stores/",)

    def parse_hours(self, trs):
        opening_hours = []
        for tr in trs:
            day = tr.xpath("td/text()").extract_first()
            time = tr.xpath("td[2]/text()").extract_first()
            if day is not None and time is not None:
                day = (
                    day.replace("Monday", "Mo")
                    .replace("Tuesday", "Tu")
                    .replace("Wednesday", "We")
                    .replace("Thursday", "Th")
                    .replace("Friday", "Fr")
                    .replace("Saturday", "Sa")
                    .replace("Sunday", "Su")
                )
                time = time.replace("\xa0", " ")
                match = re.search(r"(\d{1,2}) (a|p)[.]m[.] . (\d{1,2}) (a|p)[.]m[.]", time)
                if match:
                    (f_hr, f_ampm, t_hr, t_ampm) = match.groups()
                    f_hr = int(f_hr)
                    if f_ampm == "p":
                        f_hr += 12
                    elif f_ampm == "a" and f_hr == 12:
                        f_hr = 0
                    t_hr = int(t_hr)
                    if t_ampm == "p":
                        t_hr += 12
                    elif t_ampm == "a" and t_hr == 12:
                        t_hr = 0

                    hours = "{:02d}:{}-{:02d}:{}".format(
                        f_hr,
                        "00",
                        t_hr,
                        "00",
                    )
                    opening_hours.append("{} {}".format(day, hours))

        return "; ".join(opening_hours)

    def parse(self, response):
        stores = response.xpath('//div[@id="portfolio"]/article')
        for store in stores:
            if store.xpath("@class").extract_first() != "all portfolio-item toronto":
                properties = {
                    "ref": store.xpath("div/h3/text()").extract_first(),
                    "name": store.xpath("div/h3/text()").extract_first(),
                    "addr_full": store.xpath("div/div/p/text()").extract_first(),
                    "postcode": self.post_code(store.xpath("div/div/p/text()[last()]").extract_first()),
                    "state": self.state(store.xpath("div/div/p/text()[last() - 1]").extract_first()),
                    "phone": self.phone(store.xpath('div/div/div[@id="cinfo"]/p/text()').extract_first()),
                    "opening_hours": self.parse_hours(store.xpath('div/div/div[@id="sinfo"]/table[1]/tbody/tr')),
                }
                yield Feature(**properties)

    def city(self, data):
        str_list = data.split(",")
        return str_list[0].strip()

    def state(self, data):
        if data is None:
            return ""
        m = re.search(r"(,)\s(.*)", data)
        m_space = re.search(r"\s(.*)", data)
        if m:
            return m.group(2)
        elif m_space:
            return m_space.group(1)
        else:
            return data

    def post_code(self, data):
        if data is None:
            return ""
        return data.strip().replace("\xa0", "")

    def phone(self, data):
        if data is None:
            return ""
        if ":" not in data:
            return data.replace("\xa0", " ")
        return data.split(":")[1]
