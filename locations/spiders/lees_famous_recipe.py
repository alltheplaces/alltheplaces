# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import re

class LeesFamousRecipeSpider(scrapy.Spider):
    name = "lees_famous_recipe"
    allowed_domains = ["www.leesfamousrecipe.com"]
    start_urls = (
        'https://www.leesfamousrecipe.com/locations/all',
    )

    def parse_phone(self, phone):
        phone = phone.replace('.','')
        phone = phone.replace(')','')
        phone = phone.replace('(','')
        phone = phone.replace('_','')
        phone = phone.replace('-','')
        phone = phone.replace('+','')
        phone = phone.replace(' ','')
        return phone

    def parse(self, response):
        if("https://www.leesfamousrecipe.com/locations/all" == response.url):
            for match in response.xpath("//div[contains(@class,'field-content')]/a/@href"):
                request = scrapy.Request(match.extract())
                yield request
        else:
            nameString = response.xpath("//h1[@class='node-title']/text()").extract_first().strip()
            shortString = response.xpath("//h1[@class='node-title']/small/text()").extract_first()
            if shortString is None:
                shortString = ""
            nameString = nameString + " " + shortString
            nameString = nameString.strip()

            scriptBody = response.xpath("//script[@type='text/javascript' and contains(.,'latitude')]/text()").extract_first()
            latString = re.findall("latitude\":\"(.*?)\"", scriptBody)[0]
            lonString = re.findall("longitude\":\"(.*?)\"", scriptBody)[0]



            if("british-columbia" in response.url):
                countryString = "CA"
                stateString = "BC"
            else:
                countryString = "US"
                mapUrl = response.xpath("//div[contains(@class,'map-link')]/div/a/@href").extract_first()
                stateString = re.findall('(?<=\+)(.*?)(?=\+)', mapUrl)[len(re.findall('(?<=\+)(.*?)(?=\+)', mapUrl)) - 2].strip().replace('%2C','')

            yield GeojsonPointItem(
                ref=nameString,
                addr_full=response.xpath("//div[@class='street-address']/text()").extract_first().strip(),
                city=response.xpath("//div[@class='city-state-zip']/span[@class='locality']/text()").extract_first().strip(),
                state=stateString,
                postcode=response.xpath("//div[@class='city-state-zip']/span[@class='postal-code']/text()").extract_first().strip(),
                phone=self.parse_phone(response.xpath("//div[contains(@class,'field-name-field-phone')]/div/div/text()").extract_first().strip()),
                country = countryString,
                lat=float(latString),
                lon=float(lonString),
            )

