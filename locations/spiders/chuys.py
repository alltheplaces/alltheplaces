# -*- coding: utf-8 -*-
import scrapy
import re
from urllib.parse import urljoin
from locations.items import GeojsonPointItem


class ChuysSpider(scrapy.Spider):
    name = "chuys"
    allowed_domains = ["www.chuys.com"]
    start_urls = ("https://www.chuys.com/locations",)

    def parse(self, response):
        data = response.xpath(
            '//script[@type="text/javascript"][contains(text(), "new google.maps.LatLng")]/text()'
        ).extract_first()

        re_location_id = r"markers\[(\d+)\]"
        location_ids = re.findall(re_location_id, data)

        for location_id in location_ids:
            re_pattern_store_info = (
                rf"infoWindowContent{location_id}\s\+=(?!.*Coming Soon).+;"
            )
            store_info = re.findall(re_pattern_store_info, data)

            name = re.search(r"<strong>(.*?)</strong>", store_info[0]).group(1)
            addr_full = re.search(r"<br.*>(.*?)'", store_info[1]).group(1).strip()
            locality = re.search(r"<br.*>(.*?)'", store_info[2]).group(1)
            phone = re.search(r"<br.*>(.*?)'", store_info[3]).group(1)
            website = urljoin(
                "https://www.chuys.com",
                re.search(r"href=\"(.*?)\"", store_info[4]).group(1),
            )

            re_coordinates = rf"latLng{location_id}.*LatLng\((.*)\)"
            lat, lon = re.search(re_coordinates, data).group(1).split(", ")

            properties = {
                "ref": location_id,
                "name": name,
                "addr_full": addr_full,
                "city": locality.split(", ")[0],
                "state": locality.split(", ")[1].split()[0],
                "postcode": locality.split(", ")[1].split()[1],
                "phone": phone,
                "website": website,
                "lat": lat,
                "lon": lon,
            }

            yield GeojsonPointItem(**properties)
