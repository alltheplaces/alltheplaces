import datetime
import json
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class AshleyHomeStoreSpider(scrapy.Spider):

    name = "ashleyhomestore"
    item_attributes = {"brand": "Ashley Home Store"}
    allowed_domains = [
        "ashleyfurniture.com",
        "ashleyhomestore.ca",
        "stores.boldapps.net",
    ]
    download_delay = 0.5

    def start_requests(self):
        return [
            scrapy.Request(
                "https://stores.ashleyfurniture.com/store",
                callback=self.parse_us_stores,
            ),
            scrapy.Request(
                "https://ashleyhomestore.ca/apps/store-locator",
                callback=self.parse_ca_stores,
            ),
        ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            if hour["opens"] == "Closed":
                continue
            elif hour["closes"] == "Closed":
                continue
            else:
                opening_hours.add_range(
                    day=DAY_MAPPING[
                        hour["dayOfWeek"].replace("http://schema.org/", "")
                    ],
                    open_time=hour["opens"],
                    close_time=hour["closes"],
                    time_format="%I:%M%p",
                )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        try:
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
                ).extract_first()
            )
        except:
            jsondata = response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
            jsondata = jsondata[:-8]
            jsondata = jsondata.replace("\r\n", "")
            data = json.loads(jsondata)

        properties = {
            "name": data["name"],
            "ref": data["url"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data.get("telephone"),
            "website": data.get("url") or response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        hours = self.parse_hours(data.get("openingHoursSpecification", []))
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_store_list(self, response):
        urls = response.xpath(
            '//div[contains(@class, "city-details")]/div[@class="storeName"]/a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_us_stores(self, response):
        urls = response.xpath('//div[@class="state-col"]/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store_list)

    def parse_ca_store(self, response):
        properties = response.meta["properties"]

        data = response.json()["data"]
        hours = (
            scrapy.Selector(text=data).xpath('//span[@class="hours"]/text()').extract()
        )
        pattern = re.compile(r"([a-z]+)\s*:\s*(.*)", re.IGNORECASE)

        opening_hours = OpeningHours()
        for hour in hours:
            try:
                hour = hour.strip()
                day, open_close = re.search(pattern, hour).groups()
                if open_close == "Closed":
                    continue
                open_time, close_time = open_close.split("-")
                opening_hours.add_range(
                    day=day[:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )
            except:
                continue
        opening_hours = opening_hours.as_opening_hours()

        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse_ca_stores(self, response):
        store_list = response.xpath('//div[@class="addresses"]/ul/li')

        # coords are found in script element and match to store by a unique id
        scripts = "".join(response.xpath("//script/text()").extract())
        markers = re.findall(r"markersCoords.push\((.+?)\);", scripts)

        coords = {}
        lat_pattern = re.compile(r"lat:\s*([0-9.-]+)")
        lon_pattern = re.compile(r"lng:\s*([0-9.-]+)")
        id_pattern = re.compile(r"id:\s*([0-9]+)")
        for marker in markers:
            try:
                lat = re.search(lat_pattern, marker).group(1)
                lon = re.search(lon_pattern, marker).group(1)
            except AttributeError:
                continue
            id = re.search(id_pattern, marker).group(1)
            coords[id] = {"lat": float(lat), "lon": float(lon)}

        for store in store_list:
            id = store.xpath("./@onmouseover").re_first(r"\((.*)\)")
            name = store.xpath('.//span[@class="name"]/text()').extract_first().strip()
            name = re.sub(r"\(\d+\)", "", name).strip()

            properties = {
                "ref": id,
                "name": name,
                "addr_full": store.xpath('.//span[@class="address"]/text()')
                .extract_first()
                .strip(),
                "city": store.xpath('.//span[@class="city"]/text()')
                .extract_first()
                .strip(),
                "state": store.xpath('.//span[@class="prov_state"]/text()')
                .extract_first()
                .strip(),
                "postcode": store.xpath('.//span[@class="postal_zip"]/text()')
                .extract_first()
                .strip(),
                "country": "CA",
                "phone": store.xpath('.//span[@class="phone"]/text()')
                .extract_first()
                .strip(),
                "lat": float(coords[id]["lat"]),
                "lon": float(coords[id]["lon"]),
            }

            yield scrapy.Request(
                url="https://stores.boldapps.net/front-end/get_store_info.php?shop=ashley-homestores-in-canada.myshopify.com&data=detailed&store_id="
                + str(id),
                callback=self.parse_ca_store,
                meta={"properties": properties},
            )
