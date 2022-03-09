# -*- coding: utf-8 -*-
import scrapy
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

DAY_MAPPING = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class RossDressSpider(scrapy.Spider):
    name = "ross_dress"
    item_attributes = {"brand": "Ross Dress for Less"}
    allowed_domains = ["hosted.where2getit.com"]
    start_urls = (
        'https://hosted.where2getit.com/rossdressforless/2014/ajax?&xml_request=<request><appkey>1F663E4E-1B64-11E5-B356-3DAF58203F82</appkey><formdata id="locatorsearch"><dataview>store_default</dataview><limit>99999</limit><geolocs><geoloc><longitude>-98.5795</longitude><latitude>39.8283</latitude></geoloc></geolocs><searchradius>4000|2500</searchradius><where><clientkey><eq></eq></clientkey><opendate><eq></eq></opendate><shopping_spree><eq></eq></shopping_spree></where></formdata></request>',
        'https://hosted.where2getit.com/rossdressforless/2014/ajax?&xml_request=<request><appkey>1F663E4E-1B64-11E5-B356-3DAF58203F82</appkey><formdata id="locatorsearch"><dataview>store_default</dataview><limit>99999</limit><geolocs><geoloc><longitude>-84.5947</longitude><latitude>40.6577</latitude></geoloc></geolocs><searchradius>4000|2500</searchradius><where><clientkey><eq></eq></clientkey><opendate><eq></eq></opendate><shopping_spree><eq></eq></shopping_spree></where></formdata></request>',
    )

    def store_hours(self, store_hours):
        opening_hours = OpeningHours()

        for day, hours in zip(DAY_MAPPING, store_hours):
            open_time, close_time = hours.split("-")
            opening_hours.add_range(
                day=day,
                open_time=open_time.strip(),
                close_time=close_time.strip(),
                time_format="%I:%M %p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.xpath("//poi")

        for store in data:
            properties = {
                "ref": str(store.xpath("clientkey/text()").extract_first()),
                "name": store.xpath("name/text()").extract_first(),
                "website": store.xpath("website/text()").extract_first(),
                "addr_full": store.xpath("address1/text()").extract_first(),
                "city": store.xpath("city/text()").extract_first(),
                "state": store.xpath("state/text()").extract_first(),
                "postcode": store.xpath("postalcode/text()").extract_first(),
                "country": store.xpath("country/text()").extract_first(),
                "lon": float(store.xpath("longitude/text()").extract_first()),
                "lat": float(store.xpath("latitude/text()").extract_first()),
            }

            phone = store.xpath("phone/text()")
            if phone:
                properties["phone"] = phone.extract_first()

            hours = [
                store.xpath("monday/text()").extract_first(),
                store.xpath("tuesday/text()").extract_first(),
                store.xpath("wednesday/text()").extract_first(),
                store.xpath("thursday/text()").extract_first(),
                store.xpath("friday/text()").extract_first(),
                store.xpath("saturday/text()").extract_first(),
                store.xpath("sunday/text()").extract_first(),
            ]
            if hours:
                properties["opening_hours"] = self.store_hours(hours)

            yield GeojsonPointItem(**properties)

        else:
            self.logger.info("No results")
