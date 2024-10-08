import json
import re
import time

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BannerHealthSpider(SitemapSpider):
    name = "banner_health"
    item_attributes = {"brand": "Banner Health", "brand_wikidata": "Q4856918"}
    allowed_domains = ["bannerhealth.com"]
    sitemap_urls = ["https://www.bannerhealth.com/sitemap-BH.xml"]
    sitemap_rules = [(r"https://www.bannerhealth.com/locations/[-\w]+", "parse_location")]

    def parse_location(self, response):
        other = response.xpath("/html/body/div[1]/div[2]/div/div[2]/div").get()
        if not (data := response.xpath('//div[@data-js="map_canvas"]/@data-map-config').get()):
            data = response.xpath('//div[@data-js="map_canvas-v2"]/@data-map-config').get()
        if data and not other:
            if not (
                cty_ste_pde := response.xpath(
                    '//div[contains(@class,"text-card-location-image-content")]/p[1]/text()[3]'
                ).get()
            ):
                cty_ste_pde = response.xpath(
                    '//div[contains(@class,"text-card-location-image-content")]/p[1]/text()[2]'
                ).get()
            if not cty_ste_pde:
                cty_ste_pde = response.xpath("//address/text()[3]").get()
            if not cty_ste_pde:
                cty_ste_pde = response.xpath("//address/text()[2]").get()

            days = response.xpath('//div[@class="card-hours-row"]')
            oh = OpeningHours()
            for day in days:
                hours = day.xpath("./div[2]/text()").get().replace("\n", "").strip()
                if not hours == "Closed":
                    for hour in hours.split(","):
                        open_time = re.split(".to|to", hour)[0].replace(".", "").strip()
                        close_time = re.split(".to|to", hour)[1].replace(".", "").strip()
                        oh.add_range(
                            day=day.xpath("./div[1]/text()").get().replace("\n", "").strip(),
                            open_time=time.strftime(
                                "%H:%M", time.strptime(open_time, "%I:%M %p" if ":" in open_time else "%I %p")
                            ),
                            close_time=time.strftime(
                                "%H:%M", time.strptime(close_time, "%I:%M %p" if ":" in close_time else "%I %p")
                            ),
                        )

            data = json.loads(data)
            cty_ste_pde = cty_ste_pde.strip().strip("\n").replace("\xa0", "")
            postcode = re.findall("[0-9]{5}-[0-9]{4}|[0-9]{5}", cty_ste_pde)[0]
            state = (re.findall("[A-Z]{2}", cty_ste_pde)[0:1] or (None,))[0]
            city = cty_ste_pde.replace(str(state), "").replace(postcode, "").replace(",", "").strip()

            properties = {
                "ref": response.url,
                "postcode": postcode,
                "state": state,
                "city": city,
                "lat": data.get("markerList")[0].get("Latitude"),
                "lon": data.get("markerList")[0].get("Longitude"),
                "name": data.get("markerList")[0].get("Locations")[0].get("Name"),
                "street_address": data.get("markerList")[0].get("Locations")[0].get("Address").replace("<br/>", ""),
                "phone": data.get("markerList")[0].get("Locations")[0].get("PhoneNumber"),
                "opening_hours": oh.as_opening_hours(),
            }

            apply_category(Categories.CLINIC, properties)
            yield Feature(**properties)
