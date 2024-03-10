import json

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class KpmgSpider(SitemapSpider):
    name = "kpmg"
    item_attributes = {"brand": "KPMG", "brand_wikidata": "Q493751"}
    allowed_domains = ["kpmg.com", ""]
    sitemap_urls = ["https://kpmg.com/sitemap-index.xml"]
    sitemap_rules = [("/offices/", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response):
        data = response.xpath('//script[contains(text(),"var kpmgMetaData")]/text()').get()
        data = json.loads(self.find_between(data, "var kpmgMetaData=", ";var"))

        properties = {
            "ref": response.url,
            "name": data.get("KPMG_Location_Company_Name"),
            "street_address": data.get("KPMG_Location_Address_Line_1"),
            "postcode": data.get("KPMG_Location_Address_Postal_Code"),
            "city": data.get("KPMG_Location_Address_City"),
            "country": data.get("KPMG_Location_Country_ISO"),
            "lat": data.get("KPMG_Location_Latitude"),
            "lon": data.get("KPMG_Location_Longitude"),
            "phone": data.get("KPMG_Location_Telephone_Number"),
            "website": response.url,
        }

        yield Feature(**properties)
