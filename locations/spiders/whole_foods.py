# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import re
import string

class WholeFoodsSpider(scrapy.Spider):
    name = "whole_foods"
    allowed_domains = ["www.wholefoodsmarket.com"]
    start_urls = (
        'https://www.wholefoodsmarket.com/stores/list?page=0',
        'https://www.wholefoodsmarket.com/stores/list/canada',
        'https://www.wholefoodsmarket.com/stores/list/uk',
        'https://www.wholefoodsmarket.com/stores/list/365',
    )

    def parse(self, response):
      if("?page=" in response.url):
        for match in response.xpath("//div[contains(@class,'views-field-title')]/parent::div/parent::div"):
          yield GeojsonPointItem(
            ref=string.capwords(match.xpath(".//h4[contains(@class,'field-content')]/a/text()").extract_first()),
            addr_full=match.xpath(".//div[contains(@class,'thoroughfare')]/text()").extract_first(),
            city=match.xpath(".//span[contains(@class,'locality')]/text()").extract_first(),
            state=match.xpath(".//span[contains(@class,'state')]/text()").extract_first(),
            postcode=match.xpath(".//span[contains(@class,'postal-code')]/text()").extract_first(),
            phone=re.sub('[^0-9]','', match.xpath(".//div[contains(@class,'storefront-phone')]/span[contains(@class,'strong')]/following-sibling::text()").extract_first()),
            website= "https://www.wholefoodsmarket.com" + match.xpath(".//h4[contains(@class,'field-content')]/a/@href").extract_first(),
            country=match.xpath(".//span[contains(@class,'country')]/text()").extract_first(),
          )
        yield scrapy.Request("https://www.wholefoodsmarket.com" + response.xpath("//li[contains(@class,'pager-next')]/a/@href").extract_first(),callback=self.parse)
      else:
        for match in response.xpath("//div[contains(@class,'views-field-title')]/parent::div"):
          yield GeojsonPointItem(
            ref=string.capwords(match.xpath(".//h4[contains(@class,'field-content')]/a/text()").extract_first()),
            addr_full=match.xpath(".//div[contains(@class,'thoroughfare')]/text()").extract_first(),
            city=match.xpath(".//span[contains(@class,'locality')]/text()").extract_first(),
            state=match.xpath(".//div[contains(@class,'state')]/text()").extract_first(),
            postcode=match.xpath(".//div[contains(@class,'postal-code')]/text()").extract_first(),
            phone=re.sub('[^0-9]','', match.xpath(".//div[contains(@class,'phone-number')]/div/text()").extract_first()),
            website= "https://www.wholefoodsmarket.com" + match.xpath(".//h4[contains(@class,'field-content')]/a/@href").extract_first(),
            country=match.xpath(".//span[contains(@class,'country')]/text()").extract_first(),
          )

