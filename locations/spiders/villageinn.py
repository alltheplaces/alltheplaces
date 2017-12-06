# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem

class VillageInnSpider(scrapy.Spider):
    name = "villageinn"
    allowed_domains = ["www.villageinn.com"]
    start_urls = (
        "http://www.villageinn.com/locations/bystate.php",
    )
        
    def parse(self, response):
        selector = scrapy.Selector(response)
        links = selector.css("a.animatedlink::attr(href)")
        
        for link in links:
            yield scrapy.Request(
                response.urljoin(link.extract()),
                callback = self.parse_link
            )
    
    def parse_link(self, response):
        selector = scrapy.Selector(response)
        
        website = response.xpath('//head/meta[@property="og:url"]/@content').extract_first()
        ref = website.split("/")[-1]
        lat = selector.css("#h_lat::attr(value)").extract_first()
        lng = selector.css("#h_lng::attr(value)").extract_first()

        blocks = selector.css("#location_subcontainer .block")
        
        properties = {
            "ref" : ref,
            "website": website,
            "lat": lat,
            "lon": lng,
            "opening_hours": self.hours(blocks[1])
        }
        
        address = self.address(blocks[0])
        if address:
            properties.update(address)
        
        yield GeojsonPointItem(**properties)
        
    def address(self, data):
        address = data.css(".block::text").extract()
        street = address[2].strip("\n").strip("\t")
        address1 = address[-3].strip("\n").strip("\t")
        city = address1.split(",")[0]
        address2 = address1.split(" ")
        state = address2[1]
        zipcode = address2[2]
        phone = re.findall(r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})", address[-2].strip("\n").strip("\t"))[0]
        
        ret = {
            "street": street,
            "city": city,
            "state": state,
            "postcode": zipcode,
            "phone": phone
        }

        return ret

    def hours(self, data):
        section_headings = data.css(".sectionHeading")
        store_hours = section_headings[-1].xpath("//span/following-sibling::span[1]/text()").extract()
        
        ret = ""
        for i in range(7):
            ret += store_hours[(i+1)*3][:2] + " "
            ret += store_hours[(i+1)*3 + 1] + " - "
            ret += store_hours[(i+1)*3 + 2] + "; "

        return ret




