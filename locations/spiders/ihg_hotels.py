import json
import re
import scrapy

from locations.items import GeojsonPointItem


class IHGHotels(scrapy.Spider):

    name = "ihg_hotels"
    item_attributes = {"brand": "IHG Hotels", "brand_wikidata": "Q1424962"}
    # allowed_domains = ["ihg.com"]  # the Kimpton hotels each have their own domains
    download_delay = 0.5

    start_urls = (
        "https://www.ihg.com/holidayinn/destinations/us/en/explore",
        "https://www.ihg.com/armyhotels/hotels/us/en/installations",
    )

    def parse_hotel(self, response):
        if "hoteldetail" not in response.url:
            # got redirected back to search page
            return

        street_address = " ".join(
            response.xpath('//span[@itemprop="streetAddress"]/p/text()').extract()
        )
        if not street_address:
            street_address = response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract_first()

        city = response.xpath(
            '//span[@itemprop="addressLocality"]/text()'
        ).extract_first()
        state = response.xpath(
            '//span[@itemprop="addressRegion"]/text()'
        ).extract_first()

        properties = {
            "ref": "_".join(
                re.search(r"en/(.*)/(.*)/hoteldetail", response.url).groups()
            ),
            "name": response.xpath(
                '//meta[@property="og:title"]/@content'
            ).extract_first(),
            "addr_full": street_address.replace("\u00a0", " ").strip(", ")
            if street_address
            else None,
            "city": city.replace("\u00a0", " ").strip(", ") if city else None,
            "state": state.replace("\u00a0", " ").strip(", ") if state else None,
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "country": response.xpath(
                '//span[@itemprop="addressCountry"]/text()'
            ).extract_first(),
            "phone": (
                response.xpath('//span[@itemprop="telephone"]/text()').extract_first()
                or ""
            ).strip("| "),
            "lat": float(
                response.xpath(
                    '//meta[@property="place:location:latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//meta[@property="place:location:longitude"]/@content'
                ).extract_first()
            ),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse_kimpton(self, response):
        url = response.xpath(
            '//a[contains(text(), "VISIT HOTEL WEBSITE")]/@href'
        ).extract_first()
        properties = {
            "ref": "_".join(
                re.search(r"en/(.*)/(.*)/hoteldetail", response.url).groups()
            ),
            "lat": float(
                response.xpath(
                    '//meta[@property="place:location:latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//meta[@property="place:location:longitude"]/@content'
                ).extract_first()
            ),
        }
        if not url:  # "opening soon" hotels just have teaser pages
            return
        url = url.split("?")[0]  # remove querystring
        yield scrapy.Request(
            url, callback=self.parse_kimpton_data, meta={"properties": properties}
        )

    def parse_kimpton_data(self, response):
        properties = response.meta["properties"]
        script = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()
        if script:
            data = json.loads(script)
        else:
            data = {}
        if "name" in data:
            properties.update(
                {
                    "name": data["name"],
                    "addr_full": data["address"]["streetAddress"],
                    "city": data["address"]["addressLocality"],
                    "state": data["address"].get("addressRegion"),
                    "postcode": data["address"]["postalCode"],
                    "country": data["address"].get("addressCountry"),
                    "phone": data.get("telephone"),
                    "website": data["url"],
                }
            )

        else:
            street_address = " ".join(
                response.xpath('//span[@itemprop="streetAddress"]/p/text()').extract()
            )
            if not street_address:
                street_address = response.xpath(
                    '//span[@itemprop="streetAddress"]/text()'
                ).extract_first()

            city = response.xpath(
                '//span[@itemprop="addressLocality"]/text()'
            ).extract_first()
            state = response.xpath(
                '//span[@itemprop="addressRegion"]/text()'
            ).extract_first()

            properties.update(
                {
                    "name": response.xpath(
                        '//meta[@property="og:title"]/@content'
                    ).extract_first(),
                    "addr_full": street_address.replace("\u00a0", " ").strip(", ")
                    if street_address
                    else None,
                    "city": city.replace("\u00a0", " ").strip(", ") if city else None,
                    "state": state.replace("\u00a0", " ") if state else None,
                    "postcode": response.xpath(
                        '//span[@itemprop="postalCode"]/text()'
                    ).extract_first(),
                    "country": response.xpath(
                        '//span[@itemprop="addressCountry"]/text()'
                    ).extract_first(),
                    "phone": (
                        response.xpath(
                            '//span[@itemprop="telephone"]/text()'
                        ).extract_first()
                        or ""
                    ).strip("| "),
                    "website": response.url,
                }
            )

        yield GeojsonPointItem(**properties)

    def parse_regent(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()
        )

        properties = {
            "ref": "_".join(
                re.search(r"en/(.*)/(.*)/hoteldetail", response.url).groups()
            ),
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"].get("addressRegion"),
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data["telephone"],
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse_crowne_plaza(self, response):
        address = (
            response.xpath('//a[@class="hotel-home"]/text()').extract_first().strip()
        )

        address_parts = address.split("|")

        if len(address_parts) == 4:  # international addresses
            addr_city, postcode, country, _ = address_parts
            state = ""
        else:  # us addresses
            addr_city, state, postcode, country, _ = address_parts

        street_address = ",".join(addr_city.split(",")[0:-1])
        city = addr_city.split(",")[-1]

        properties = {
            "ref": "_".join(
                re.search(r"en/(.*)/(.*)/hoteldetail", response.url).groups()
            ),
            "name": response.xpath(
                '//meta[@property="og:title"]/@content'
            ).extract_first(),
            "addr_full": street_address.strip(),
            "city": city.strip(),
            "state": state.strip(),
            "postcode": postcode.strip(),
            "country": country.strip(),
            "phone": response.xpath(
                '//div[@class="new-hinfo-address"]/p/a[2]/text()'
            ).extract_first(),
            "lat": float(
                response.xpath(
                    '//meta[@property="place:location:latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//meta[@property="place:location:longitude"]/@content'
                ).extract_first()
            ),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse_candlewood_staybridge(self, response):
        if "hoteldetail" not in response.url:
            # got redirected back to search page
            return

        street_address = " ".join(
            response.xpath('//span[@itemprop="streetAddress"]/p/text()').extract()
        )
        if not street_address:
            street_address = response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract_first()

        region = (
            response.xpath('//span[@itemprop="addressRegion"]/text()')
            .extract_first()
            .replace("\u00a0", " ")
        )

        match = re.search(r"([a-z]+)\s(\d+)\s(.*)", region, re.IGNORECASE)
        if match:
            state, postcode, country = match.groups()
        else:
            state, postcode, country = None, None, region.strip()

        properties = {
            "ref": "_".join(
                re.search(r"en/(.*)/(.*)/hoteldetail", response.url).groups()
            ),
            "name": response.xpath(
                '//meta[@property="og:title"]/@content'
            ).extract_first(),
            "addr_full": street_address.replace("\u00a0", " ").strip(", "),
            "city": response.xpath('//span[@itemprop="addressLocality"]/text()')
            .extract_first()
            .replace("\u00a0", " ")
            .strip(", "),
            "state": state,
            "postcode": postcode,
            "country": country,
            "phone": response.xpath('//div[@class="booking"]/a/text()').extract_first(),
            "lat": float(
                response.xpath(
                    '//meta[@property="place:location:latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//meta[@property="place:location:longitude"]/@content'
                ).extract_first()
            ),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse_army_hotel(self, response):
        properties = {
            "ref": "_".join(
                re.search(r"en/(.*)/(.*)/hoteldetail", response.url).groups()
            ),
            "name": response.xpath(
                '//meta[@property="og:title"]/@content'
            ).extract_first(),
            "addr_full": response.xpath(
                '//meta[@property="business:contact_data:street_address"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@property="business:contact_data:locality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//meta[@property="business:contact_data:region"]/@content'
            ).extract_first(),
            "postcode": response.xpath(
                '//meta[@property="business:contact_data:postal_code"]/@content'
            ).extract_first(),
            "country": response.xpath(
                '//meta[@property="business:contact_data:country_name"]/@content'
            ).extract_first(),
            "phone": (
                response.xpath(
                    '//span[@title="Hotel Front Desk:"]/span/text()'
                ).extract_first()
                or ""
            ).strip(),
            "lat": float(
                response.xpath(
                    '//meta[@property="place:location:latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//meta[@property="place:location:longitude"]/@content'
                ).extract_first()
            ),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):

        hotel_parsers = {
            "holidayinn": self.parse_hotel,
            "crowneplaza": self.parse_crowne_plaza,
            "holidayinnexpress": self.parse_hotel,
            "hotelindigo": self.parse_hotel,
            "candlewood": self.parse_candlewood_staybridge,
            "staybridge": self.parse_candlewood_staybridge,
            "holidayinnresorts": self.parse_hotel,
            "intercontinental": self.parse_hotel,
            "regent": self.parse_regent,
            "hotels": self.parse_hotel,  # vocos
            "kimptonhotels": self.parse_kimpton,
            "holidayinnclubvacations": self.parse_hotel,
            "evenhotels": self.parse_hotel,
            "avidhotels": self.parse_hotel,
            "hualuxe": self.parse_hotel,
            "armyhotels": self.parse_army_hotel,
        }

        hotel_urls = response.xpath(
            '//div[@class="hotelList"]//div[contains(@class, "hotelItem")]//a[contains(@class, "hotel-name")]/@href'
        ).extract()

        if "armyhotels" in response.url:
            hotel_urls = response.xpath('//div[@id="hotelListWrap"]//a/@href').extract()

        if hotel_urls:
            for url in hotel_urls:
                hotel_type = re.search(
                    r"ihg.com/(.*?)/", response.urljoin(url), re.IGNORECASE
                ).group(1)

                yield scrapy.Request(
                    response.urljoin(url), callback=hotel_parsers[hotel_type]
                )

        else:
            urls = response.xpath('//li[@class="listingItem"]/a/@href').extract()
            for url in urls:
                yield scrapy.Request(response.urljoin(url))
