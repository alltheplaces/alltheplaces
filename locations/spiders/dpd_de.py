import csv

import scrapy
from scrapy import FormRequest

from locations.items import Feature
from locations.searchable_points import open_searchable_points


class DPDDESpider(scrapy.Spider):
    name = "dpd_de"
    item_attributes = {"brand": "DPD", "brand_wikidata": "Q541030"}
    start_urls = ["https://my.dpd.de/shopfinder.aspx"]

    def parse(self, response):
        searchable_point_files = [
            "eu_centroids_20km_radius_country.csv",
        ]

        for point_file in searchable_point_files:
            with open_searchable_points(point_file) as openFile:
                results = csv.DictReader(openFile)
                for result in results:
                    if result["country"] == "DE":
                        headers = {"Content-Type": "application/x-www-form-urlencoded"}

                        formdata = {
                            "ctl00$hidMarkerHouse": "https://my.dpd.de/themes/Icons/summer2020/house.svg",
                            "ctl00$hidMarkerShop": "https://my.dpd.de/themes/Icons/summer2020/parcelshop.svg",
                            "ctl00$hidMarkerShop_Active": "https://my.dpd.de/themes/Icons/summer2020/parcelshop_active.svg",
                            "ctl00$hidMarkerCar_Left": "https://my.dpd.de/themes/Icons/summer2020/car_left.svg",
                            "ctl00$hidMarkerCar_Right": "https://my.dpd.de/themes/Icons/summer2020/car_right.svg",
                            "ctl00$hidMarkerNeighbour": "https://my.dpd.de/themes/Icons/summer2020/neighbour.svg",
                            "ctl00$hidAudio_Car": "https://my.dpd.de/themes/Sounds/summer2020/car.mp3",
                            "ctl00$hidAudio_House": "https://my.dpd.de/themes/Sounds/summer2020/house.mp3",
                            "ctl00$hidScaleFactorHouse": "100",
                            "ctl00$hidScaleFactorShop": "100",
                            "ctl00$hidScaleFactorCar": "100",
                            "ctl00$hidScaleFactorNeighbour": "100",
                            "ctl00$ContentPlaceHolder1$modShopFinder$hidPermissionError": "Bitte+aktivieren+Sie+die+Standortermittlung+in+den+Systemeinstellungen.",
                            "ctl00$ContentPlaceHolder1$modShopFinder$txtShopSearch": result["latitude"]
                            + ","
                            + result["longitude"],
                            "ctl00$ContentPlaceHolder1$modShopFinder$hidShopFindMoreShopsBTN": "weitere+Paketshops",
                            "ctl00$ContentPlaceHolder1$modShopFinder$hidDistanceUnit": "Entfernung+!VALUE!+km",
                            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$modShopFinder$btnShopSearch",
                        }

                        rq = FormRequest.from_response(
                            response,
                            formdata=formdata,
                            headers=headers,
                            callback=self.shopsResults,
                            meta=result,
                        )
                        yield rq

    def shopsResults(self, response):
        result = response.meta
        body = response.css("body")
        shopList = body.css("div.ShopList")
        shop = shopList.css("a")
        lengthOfShops = len(shop) - 1
        for nr in range(lengthOfShops):
            item = Feature()
            name = shop.css(
                "span#ContentPlaceHolder1_modShopFinder_repShopList_labShopName_" + str(nr) + "::text"
            ).extract()[0]
            streetElement = shop.css(
                "span#ContentPlaceHolder1_modShopFinder_repShopList_labShopStreet_" + str(nr) + "::text"
            ).extract()[0]
            streets = streetElement.split("\xa0")
            street = streets[0]
            housenumber = streets[1]

            postalAndCity = (
                shop.css("span#ContentPlaceHolder1_modShopFinder_repShopList_labShopCity_" + str(nr) + "::text")
                .extract()[0]
                .split()
            )
            lat = shop.css(
                "input#ContentPlaceHolder1_modShopFinder_repShopList_latitude_" + str(nr) + "::attr(value)"
            ).extract()[0]
            lng = shop.css(
                "input#ContentPlaceHolder1_modShopFinder_repShopList_longitude_" + str(nr) + "::attr(value)"
            ).extract()[0]
            plz = postalAndCity[0]
            city = postalAndCity[1]
            item["lat"] = lat
            item["lon"] = lng
            item["name"] = name
            item["street"] = street
            item["city"] = city
            item["postcode"] = plz
            item["ref"] = lat + lng
            item["housenumber"] = housenumber

            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            formdata = {
                "ctl00$ctl16": "ctl00$ContentPlaceHolder1$modShopFinder$ctl01|ctl00$ContentPlaceHolder1$modShopFinder$repShopList$ctl0"
                + str(nr)
                + "$btnSelectShop",
                "ctl00$modHeader$txtDPDSearch": "",
                "ctl00$hidMarkerHouse": "https://my.dpd.de/themes/Icons/summer2020/house.svg",
                "ctl00$hidMarkerShop": "https://my.dpd.de/themes/Icons/summer2020/parcelshop.svg",
                "ctl00$hidMarkerShop_Active": "https://my.dpd.de/themes/Icons/summer2020/parcelshop_active.svg",
                "ctl00$hidMarkerCar_Left": "https://my.dpd.de/themes/Icons/summer2020/car_left.svg",
                "ctl00$hidMarkerCar_Right": "https://my.dpd.de/themes/Icons/summer2020/car_right.svg",
                "ctl00$hidMarkerNeighbour": "https://my.dpd.de/themes/Icons/summer2020/neighbour.svg",
                "ctl00$hidAudio_Car": "https://my.dpd.de/themes/Sounds/summer2020/car.mp3",
                "ctl00$hidAudio_House": "https://my.dpd.de/themes/Sounds/summer2020/house.mp3",
                "ctl00$hidScaleFactorHouse": "100",
                "ctl00$hidScaleFactorShop": "100",
                "ctl00$hidScaleFactorCar": "100",
                "ctl00$hidScaleFactorNeighbour": "100",
                "ctl00$ContentPlaceHolder1$modShopFinder$hidPermissionError": "Bitte+aktivieren+Sie+die+Standortermittlung+in+den+Systemeinstellungen.",
                "ctl00$ContentPlaceHolder1$modShopFinder$hidShopFindMoreShopsBTN": "weitere+Paketshops",
                "ctl00$ContentPlaceHolder1$modShopFinder$hidDistanceUnit": "Entfernung+!VALUE!+km",
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$modShopFinder$repShopList$ctl0"
                + str(nr)
                + "$btnSelectShop",
                "ctl00$ContentPlaceHolder1$modShopFinder$txtShopSearch": result["latitude"] + "," + result["longitude"],
            }

            rq = FormRequest.from_response(
                response,
                formdata=formdata,
                headers=headers,
                callback=self.openingHoursParse,
                meta=item,
            )

            yield rq

    def openingHoursParse(self, response):
        body = response.css("body")
        shopDetails = body.css("div.panShopDetails")
        shops = shopDetails.css("div.panBusinessHour")
        item = response.meta
        openingShop = dict()
        if len(shops) > 0:
            for nr in range(7):
                day = shops.css(
                    "span#ContentPlaceHolder1_modShopFinder_repBusinessHours_labBusinessDay_" + str(nr) + "::text"
                ).extract()[0]
                openningHours = (
                    shops.css(
                        "span#ContentPlaceHolder1_modShopFinder_repBusinessHours_labBusinessHour_" + str(nr) + "::text"
                    )
                    .extract()[0]
                    .split(" ")
                )

                for element in openningHours:
                    if element == "-":
                        del openningHours[1]

                openingShop[day] = openningHours

            item["opening_hours"] = openingShop

        yield item
