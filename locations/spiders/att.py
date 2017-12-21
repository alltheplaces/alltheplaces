import scrapy
from locations.items import GeojsonPointItem
import json


class ATTScraper(scrapy.Spider):
    name = "att"

    start_urls = ['https://www.att.com/sitemapfiles/stores-sitemap.xml']
    api_base = "https://www.att.com/apis/maps/v2/locator/place/cpid/{}.json"

    def process_hours(result):
        ret = []
        for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            open, close = result[day.lower() + "_open"], result[day.lower() + "_close"]
            if "-1" not in (open, close):
                ret.append("{} {}-{}".format(day[:2], open, close))

        return "; ".join(ret)

    def parse(self, response):
        response.selector.remove_namespaces()
        locations = response.xpath('//url/loc/text()')
        for loc in locations:
            url = loc.extract()
            store_id = url.rsplit('/', 1)[-1]
            yield scrapy.Request(
                self.api_base.format(store_id),
                callback=self.parse_location,
                meta={"url": loc.extract()}
            )

    def parse_location(self, response):
        results = json.loads(response.body_as_unicode())["results"]
        if results:
            store_data = results[0]
            yield GeojsonPointItem(
                lat=store_data["lat"],
                lon=store_data["lon"],
                name=store_data["name"],
                addr_full=(store_data["address1"] + " "
                          + (store_data.get("address2") or "")).strip(),
                city=store_data["city"],
                state=store_data["region"],
                postcode=store_data["postal"],
                phone=store_data["phone"].strip(),
                website=response.meta["url"],
                opening_hours=self.process_hours(store_data),
                ref=store_data["id"]
            )
