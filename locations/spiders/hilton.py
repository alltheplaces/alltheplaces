import json
import re
import scrapy

from locations.items import GeojsonPointItem


def load_json(data):
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        # fix malformed json
        data = re.sub(r"(:\s*)\'", r'\1"', data)  # use double quotes instead of single
        data = re.sub(r"\'([,\s\}])", r'"\1', data)
        data = re.sub(r",(\s*\})", r"\1", data)  # remove trailing commas
        data = re.sub(r'(description": ")[\s\S]*?(",[\n\r])', r"\1\2", data)
        return json.loads(data)


class HiltonSpider(scrapy.Spider):
    name = "hilton"
    allowed_domains = ["hilton.com", "hiltongrandvacations.com"]

    def start_requests(self):
        sites = [
            (
                "Hilton Hotels & Resorts",
                "https://www3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Waldorf Astoria Hotels & Resorts",
                "https://waldorfastoria3.hilton.com/en/hotels/index.html",
                self.parse_hotel_list,
            ),
            (
                "LXR Hotels & Resorts",
                "https://lxrhotels3.hilton.com/lxr/locations/",
                self.parse_lxr,
            ),
            (
                "Conrad Hotels & Resorts",
                "https://conradhotels3.hilton.com/en/hotels/index.html",
                self.parse_hotel_list,
            ),
            (
                "Canopy by Hilton",
                "https://canopy3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Curio Collection by Hilton",
                "https://curiocollection3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Doubletree by Hilton",
                "https://doubletree3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Tapestry Collection by Hilton",
                "https://tapestrycollection3.hilton.com/tc/locations/",
                self.parse_tapestry,
            ),
            (
                "Embassy Suites",
                "https://embassysuites3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Hilton Garden Inn",
                "https://hiltongardeninn3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Hampton Inn",
                "https://hamptoninn3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Tru by Hilton",
                "https://tru3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Homewood Suites by Hilton",
                "https://homewoodsuites3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Home2 Suites by Hilton",
                "https://home2suites3.hilton.com/en/hotel-locations/index.html",
                self.parse,
            ),
            (
                "Hilton Grand Vacations",
                "https://www.hiltongrandvacations.com/destinations/",
                self.parse_grand_vacation,
            ),
            # # ('Motto', '', None)  # no locations yet but "coming soon"
        ]
        for site in sites:
            yield scrapy.Request(
                url=site[1],
                callback=site[2],
                meta={"properties": {"extras": {"brand": site[0]}}},
            )

    def parse_hotel_list(self, response):
        """Different style hotel list"""
        hotel_urls = response.xpath('//ul[@class="locations"]/li/a/@href').extract()

        for url in hotel_urls:
            yield scrapy.Request(
                response.urljoin(url), callback=self.parse_hotel, meta=response.meta
            )

    def parse_lxr(self, response):
        """Parse LXR hotel list"""
        hotel_urls = response.xpath(
            '//section[contains(@class, "location-hotels-wrap")]/section//a/@href'
        ).extract()

        for url in hotel_urls:
            yield scrapy.Request(
                response.urljoin(url), callback=self.parse_lxr_hotel, meta=response.meta
            )

    def parse_lxr_hotel(self, response):
        """Parse LXR hotel page (address parts are not labeled correctly)"""
        try:
            address = ", ".join(
                [
                    response.xpath(
                        '//span[@itemprop="streetAddress"]/text()'
                    ).extract_first(),
                    response.xpath(
                        '//span[@itemprop="addressRegion"]/text()'
                    ).extract_first(),
                ]
            )
        except:
            address = response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract_first()

        properties = {
            "name": response.xpath('//span[@itemprop="name"]/text()').extract_first(),
            "ref": response.xpath('//link[@rel="canonical"]/@href').re_first(
                ".*/(.*?)/"
            ),
            "phone": response.xpath(
                '//span[@itemprop="telephone"]//span/text()'
            ).extract_first(),
            "addr_full": address,
            "city": response.xpath(
                '//span[@itemprop="addressCountry"]/text()'
            ).extract_first(),
            "country": (
                response.xpath('//span[@itemprop="postalCode"]/text()').extract_first()
                or ""
            ).strip(),
            "website": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            "lat": float(
                response.xpath('//div[@class="marker"]/@data-lat').extract_first()
            ),
            "lon": float(
                response.xpath('//div[@class="marker"]/@data-lng').extract_first()
            ),
        }
        properties.update(response.meta["properties"])
        yield GeojsonPointItem(**properties)

    def parse_tapestry(self, response):
        """Parse Tapestry Collection hotel list"""
        script = "".join(response.xpath("//script/text()").extract())
        hotels = re.split(r'hotels\.[\d]+\.address":', script)

        for hotel in hotels[1:]:
            code = re.search(r'ctyhocn":"(.*?)"', hotel).groups()[0]
            lat = re.search(r'latitude":([\d\-\.]+)', hotel).groups()[0]
            lon = re.search(r'longitude":([\d\-\.]+)', hotel).groups()[0]
            properties = {"ref": code, "lat": float(lat), "lon": float(lon)}
            properties.update(response.meta["properties"])
            payload = {
                "operationName": "hotel",
                "variables": {"ctyhocn": code, "language": "en"},
                "query": "query hotel($ctyhocn: String!, $language: String!) {\n  hotel(ctyhocn: $ctyhocn, language: $language) {\n    address {\n      addressFmt\n    }\n    brandCode\n    galleryImages(numPerCategory: 2, first: 12) {\n      alt\n      hiResSrc(height: 430, width: 950)\n      src\n    }\n    homepageUrl\n    name\n    open\n    openDate\n    phoneNumber\n    resEnabled\n    amenities(filter: {groups_includes: [hotel]}) {\n      id\n      name\n    }\n  }\n}\n",
            }

            yield scrapy.Request(
                url="https://www.hilton.com/graphql/customer?appName=dx-brands-ui&operationName=hotel&pod=brands",
                method="POST",
                body=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                meta={"properties": properties},
                callback=self.parse_tapestry_hotel,
            )

    def parse_tapestry_hotel(self, response):
        """Parse Tapestry hotel page"""
        properties = response.meta["properties"]
        data = response.json()

        if not data["data"].get("hotel"):
            return

        url = data["data"]["hotel"]["homepageUrl"]
        if url.startswith("/"):
            url = "https:" + url

        properties.update(
            {
                "addr_full": data["data"]["hotel"]["address"]["addressFmt"],
                "name": data["data"]["hotel"]["name"],
                "phone": data["data"]["hotel"]["phoneNumber"],
                "website": url,
            }
        )
        yield GeojsonPointItem(**properties)

    def parse_grand_vacation_hotel(self, response):
        """Parse Grand Vacation hotel resort page"""
        properties = response.meta["properties"]
        lat, lon = (
            response.xpath("//script/text()")
            .re_first(r".*google.maps.LatLng\(\s*(.*)\s+\);")
            .split(",")
        )
        properties.update(
            {
                "name": response.xpath(
                    '//div[contains(@class, "resort-title")]//h1/text()'
                ).extract_first(),
                "ref": "_".join(re.search(r".*/(.*)/(.*)/", response.url).groups()),
                "lat": float(lat),
                "lon": float(lon),
                "website": response.url,
            }
        )
        yield GeojsonPointItem(**properties)

    def parse_grand_vacation(self, response):
        """Parse Hilton Grand Vacations resort list"""
        resorts = response.xpath('//div[contains(@class, "resortpanel")]')

        for resort in resorts:
            url = resort.xpath(".//a/@href").extract_first()
            location = (
                resort.xpath('.//p[@class="location"]/text()')
                .extract_first()
                .split(",")
            )
            properties = dict()
            properties["country"] = location.pop().strip()
            properties["state"] = location.pop().strip()
            properties["city"] = ", ".join(location)
            properties.update(response.meta["properties"])

            yield scrapy.Request(
                response.urljoin(url),
                callback=self.parse_grand_vacation_hotel,
                meta={"properties": properties},
            )

    def parse_hotel(self, response):
        """Parse generic hotel page"""
        data = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
        ).extract_first()

        if data:
            data = load_json(data)

            properties = {
                "name": data["name"],
                "ref": re.search(r".*/(.*)/(?:index.html)?", response.url).group(1),
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

        else:
            try:
                lat, lon = (
                    response.xpath('//meta[@name="geo.position"]/@content')
                    .extract_first()
                    .split(";")
                )
            except:
                lat, lon = None, None

            properties = {
                "name": response.xpath(
                    '//meta[@name="og:title"]/@content'
                ).extract_first(),
                "ref": re.search(r".*/(.*)/(?:index.html)?", response.url).group(1),
                "phone": response.xpath(
                    '//span[@class="property-telephone"]/text()'
                ).extract_first(),
                "addr_full": (
                    response.xpath(
                        '//span[@class="property-streetAddress"]/text()'
                    ).extract_first()
                    or ""
                ).strip(),
                "city": response.xpath(
                    '//span[@class="property-addressLocality"]/text()'
                ).extract_first(),
                "state": response.xpath(
                    '//span[@class="property-addressRegion"]/text()'
                ).extract_first(),
                "country": response.xpath(
                    '//span[@class="property-addressCountry"]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//span[@class="property-postalCode"]/text()'
                ).extract_first(),
                "lat": float(lat) if lat else None,
                "lon": float(lon) if lon else None,
                "website": response.url,
            }

        properties.update(response.meta["properties"])
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        """Parse generic hotel listings"""
        hotel_urls = response.xpath(
            '//ul[@class="directory_hotels_list"]/li/a/@href'
        ).extract()
        if hotel_urls:
            for url in hotel_urls:
                yield scrapy.Request(
                    response.urljoin(url), callback=self.parse_hotel, meta=response.meta
                )

        else:
            urls = response.xpath(
                '//ul[@class="directory_locations_list"]/li/a/@href'
            ).extract()
            for url in urls:
                yield scrapy.Request(response.urljoin(url), meta=response.meta)
