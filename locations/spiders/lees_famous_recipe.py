import re

import scrapy

from locations.items import GeojsonPointItem

daysKey = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class LeesFamousRecipeSpider(scrapy.Spider):
    name = "lees_famous_recipe"
    item_attributes = {
        "brand": "Lee's Famous Recipe Chicken",
        "brand_wikidata": "Q6512810",
    }
    allowed_domains = ["www.leesfamousrecipe.com"]
    start_urls = ("https://www.leesfamousrecipe.com/locations/all",)

    def parse_phone(self, phone):
        phone = phone.replace(".", "")
        phone = phone.replace(")", "")
        phone = phone.replace("(", "")
        phone = phone.replace("_", "")
        phone = phone.replace("-", "")
        phone = phone.replace("+", "")
        phone = phone.replace(" ", "")
        return phone

    def store_hours(self, hours):
        try:
            days = hours.split(": ")[0].strip()
            if "-" in days:
                start_day = daysKey[days.split("-")[0]]
                end_day = daysKey[days.split("-")[1]]
                day_output = start_day + "-" + end_day
            else:
                day_output = daysKey[days]

            both_hours = hours.split(": ")[1].replace(" ", "")
            open_hours = both_hours.split("-")[0]
            close_hours = both_hours.split("-")[1]

            if "am" in open_hours:
                open_hours = open_hours.replace("am", "")
                if ":" in open_hours:
                    open_h = open_hours.split(":")[0]
                    open_m = open_hours.split(":")[1]
                else:
                    open_h = open_hours
                    open_m = "00"
                open_hours = open_h + ":" + open_m

            if "pm" in open_hours:
                open_hours = open_hours.replace("pm", "")
                if ":" in open_hours:
                    open_h = open_hours.split(":")[0]
                    open_m = open_hours.split(":")[1]
                else:
                    open_h = open_hours
                    open_m = "00"
                open_h = str(int(open_h) + 12)
                open_hours = open_h + ":" + open_m

            if "am" in close_hours:
                close_hours = close_hours.replace("am", "")
                if ":" in close_hours:
                    close_h = close_hours.split(":")[0]
                    close_m = close_hours.split(":")[1]
                else:
                    close_h = close_hours
                    close_m = "00"
                close_hours = close_h + ":" + close_m

            if "pm" in close_hours:
                close_hours = close_hours.replace("pm", "")
                if ":" in close_hours:
                    close_h = close_hours.split(":")[0]
                    close_m = close_hours.split(":")[1]
                else:
                    close_h = close_hours
                    close_m = "00"
                close_h = str(int(close_h) + 12)
                close_hours = close_h + ":" + close_m
            return day_output + " " + open_hours.replace(" ", "") + "-" + close_hours + ";"
        except (KeyError, IndexError):
            return ""

    def parse(self, response):
        if "https://www.leesfamousrecipe.com/locations/all" == response.url:
            for match in response.xpath("//div[contains(@class,'field-content')]/a/@href"):
                request = scrapy.Request(match.extract())
                yield request
        else:
            name_string = response.xpath("//h1[@class='node-title']/text()").extract_first().strip()
            short_string = response.xpath("//h1[@class='node-title']/small/text()").extract_first()
            if short_string is None:
                short_string = ""
            name_string = name_string + " " + short_string
            name_string = name_string.strip()

            google_map_src = response.xpath("//*[@id='block-system-main']/div/div/iframe").extract_first()
            [lat_string, lon_string] = re.findall('center=(.*?)"', google_map_src)[0].split(",")

            opening_hours_string = ""
            first_hour_block = response.xpath(
                "//div[contains(@class,'field-name-field-hours-summer')]/div/div/p/br/parent::p/text()"
            )
            for hourLine in first_hour_block:
                opening_hours_string = opening_hours_string + " " + self.store_hours(hourLine.extract())
            opening_hours_string = opening_hours_string.strip(";").strip()

            if "british-columbia" in response.url:
                country_string = "CA"
                state_string = "BC"
            else:
                country_string = "US"
                state_string = response.xpath("//div[contains(@class,'adr')]/div[2]/span[2]/text()").extract_first()

            yield GeojsonPointItem(
                ref=name_string,
                addr_full=response.xpath("//div[@class='street-address']/text()").extract_first().strip(),
                city=response.xpath("//div[@class='city-state-zip']/span[@class='locality']/text()")
                .extract_first()
                .strip(),
                opening_hours=opening_hours_string,
                state=state_string,
                postcode=response.xpath("//div[@class='city-state-zip']/span[@class='postal-code']/text()")
                .extract_first()
                .strip(),
                phone=self.parse_phone(
                    response.xpath("//div[contains(@class,'adr')]/div[3]/text()").extract_first().strip()
                ),
                country=country_string,
                lat=lat_string,
                lon=lon_string,
            )
