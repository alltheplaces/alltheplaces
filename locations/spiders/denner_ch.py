import re
from datetime import date

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DennerCHSpider(SitemapSpider, StructuredDataSpider):
    name = "denner_ch"
    item_attributes = {"brand": "Denner", "brand_wikidata": "Q379911"}
    allowed_domains = ["www.denner.ch"]
    sitemap_urls = ["https://www.denner.ch/sitemap.xml"]
    sitemap_follow = ["denner_stores"]
    sitemap_rules = [(r"/de/filialen/", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = "Denner"
        item["lat"], item["lon"] = self.parse_lat_lon(response)
        item["country"] = "LI" if 9485 <= int(item.get("postcode", 0)) <= 9499 else "CH"
        item["phone"] = self.parse_phone(response)
        item.setdefault("extras", {}).update(self.parse_opening_date(response))
        item["extras"]["website:de"] = response.xpath('//link[@rel="alternate"][@hreflang="de"]/@href').get()
        item["extras"]["website:fr"] = response.xpath('//link[@rel="alternate"][@hreflang="fr"]/@href').get()
        item["extras"]["website:it"] = response.xpath('//link[@rel="alternate"][@hreflang="it"]/@href').get()

        yield item

    @staticmethod
    def parse_lat_lon(response):
        return (
            float(response.xpath('//input[@id="storeLatitude"]/@value').get()),
            float(response.xpath('//input[@id="storeLongitude"]/@value').get()),
        )

    @staticmethod
    def parse_opening_date(response):
        if opening := response.xpath('//div[normalize-space(text())="Neueröffnung"]/..').get():
            if match := re.search(r"Ab (\d+)\.(\d+)\.(2\d{3})", opening):
                day, month, year = [int(x) for x in match.groups()]
                if date(year, month, day) > date.today():
                    tag = "opening_date"
                else:
                    tag = "start_date"
                return {tag: "%04d-%02d-%02d" % (year, month, day)}
        return {}

    @staticmethod
    def parse_phone(response):
        if match := re.search(r"Tel\. ([\d\s]+)", response.text):
            return match.group(1).strip()
        return None
