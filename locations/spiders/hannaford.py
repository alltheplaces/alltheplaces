import scrapy
from locations.items import GeojsonPointItem
import re

regex = r"(\D+,\s\D+-\d{5}).*"  # city, state, zip
regex_am = r"\s?([Aa][Mm])"
regex_pm = r"\s?([Pp][Mm])"
regex_lat = r"(lat = \d+\.\d+)"
regex_lon = r"(lng = -\d+\.\d+)"
regex_id = r"(t\.id = \"\d+\")"


class HannafordSpider(scrapy.Spider):
    name = "hannaford"
    item_attributes = {"brand": "Hannaford"}
    allowed_domains = ["www.hannaford.com"]
    start_urls = [
        "https://www.hannaford.com/custserv/locate_store.cmd?form_state=locateStoreForm&latitude=&longitude=&formId=locateStoreForm&radius=500&cityStateZip=maine&submitBtn.x=37&submitBtn.y=10"
    ]

    def parse(self, response):
        base_url = "https://www.hannaford.com"
        script = response.xpath('//script[contains(., "t.lat")]/text()')[0].extract()

        lat = re.findall(regex_lat, script)
        lat = [x.strip("lat = ") for x in lat]
        lon = re.findall(regex_lon, script)
        lon = [x.strip("lng = ") for x in lon]
        storeid = re.findall(regex_id, script)
        storeid = [x.strip('t.id = "').strip('"') for x in storeid]
        lat_lon = list(zip(storeid, lat, lon))

        stores = response.xpath(
            '//*[@id="pageContentWrapperInner"]//descendant::*/a[2]/@href'
        ).extract()
        for store in stores:
            store = base_url + store
            yield scrapy.Request(
                store, callback=self.parse_store, meta={"lat_lon": lat_lon}
            )

    def combine_hours(self, hours):
        days = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
        hours = self.convert_hours(hours)
        converted_hours = "".join("{} {} ".format(*t) for t in zip(days, hours))
        return converted_hours

    def convert_hours(self, hours):
        for i in range(len(hours)):
            cleaned_times = ""
            if ":" in hours[i]:
                hours_to = hours[i].split("-")
                for ampm in hours_to:
                    if re.search(regex_pm, ampm):
                        ampm = re.sub(regex_pm, "", ampm)
                        hour_min = ampm.split(":")
                        if int(hour_min[0]) < 12:
                            hour_min[0] = str(12 + int(hour_min[0]))
                            cleaned_times += ":".join(hour_min)
                    if re.search(regex_am, ampm):
                        ampm = re.sub(regex_am, "", ampm)
                        hour_min = ampm.split(":")
                        if len(hour_min[0]) < 2:
                            hour_min[0] = hour_min[0].zfill(2)
                            if ampm[0]:
                                cleaned_times += (":".join(hour_min)) + "-"
                            else:
                                cleaned_times += ":".join(hour_min)
                        else:
                            if ampm[0]:
                                cleaned_times += (":".join(hour_min)) + "-"
                            else:
                                cleaned_times += ":".join(hour_min)
            else:
                cleaned_times += "off"
            hours[i] = cleaned_times
        return hours

    def parse_store(self, response):
        storeid = response.url.split("=")[1]
        for i in response.meta["lat_lon"]:
            if i[0] == storeid:
                lat = i[1]
                lon = i[2]

        addr = response.xpath('//div[@class="storeContact"]/p[1]/text()').extract()
        addr = [x.strip().replace("\xa0", "-") for x in addr]
        street = ""
        cty_st_zip = ""
        for i in addr:
            search = re.search(regex, i)
            if not search:
                street += i + " "
            else:
                cty_st_zip += i

        city = cty_st_zip.split(",")[0]
        state = cty_st_zip.split("-")[0].split(",")[1]
        postcode = cty_st_zip.split("-")[1]
        addr_full = "{}{},{} {}".format(street, city, state, postcode)

        phone = (
            response.xpath('//div[@class="storeContact"]/p[2]/text()')
            .extract_first()
            .split("\xa0")[1]
        )
        name = (
            response.xpath('//h1[@style="display:block;"]/text()')
            .extract_first()
            .split(" to ")[1]
        )
        website = response.xpath(
            '//div[@class="storeContact"]/descendant::*/a/@href'
        ).extract_first()
        if not website:
            website = response.url
        hours = response.xpath(
            '//div[@class="storeHours"]/div/p/descendant::*/text()'
        ).extract()

        opening_hours = self.combine_hours(hours)

        yield GeojsonPointItem(
            ref=response.url,
            name=name,
            lat=lat,
            lon=lon,
            addr_full=addr_full,
            street=street,
            city=city,
            state=state,
            postcode=postcode,
            phone=phone,
            website=website,
            opening_hours=opening_hours,
        )
