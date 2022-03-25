# -*- coding: utf-8 -*-
"""
Hy-Vee has 155 locations we need to scrape, they implemented a server-side javascript detector logic
that returns just the HTML head with an empty body asking that we enable javascript to browse the site.
Unfortunately, The server returns no content for us to process except we use the PUT method.

This is the reason for reimplementing the start_requests so we can pass the PUT method to our request object.
We loop through the cities on https://www.hy-vee.com/stores/store-finder-results.aspx
to build the a url that looks like this
https://www.hy-vee.com/stores/store-finder-results.aspx?zip=&state=&city=CITY,STATECODE&olfloral=...

This usually return 1 result and in some cases 0.
and provides us with a link to a details page where we get more detailed store info.
The detailed store info page has no map so we just get the latlon from the store-finder-results page
and pass it over via the request object's meta.

The opening hours are very inconsistent and contains lots of words.
I tried to solve this by creating a dict of possible words, and mapping them appropriately.

Update Nov-2019: PUT requests stopped working, GET requests now work
"""
import scrapy
import re
from locations.items import GeojsonPointItem


class HyVeeSpider(scrapy.Spider):
    name = "hyvee"
    item_attributes = {"brand": "Hyvee"}
    allowed_domains = ["hy-vee.com"]

    start_urls = ("https://www.hy-vee.com/stores/store-finder-results.aspx",)

    def parse(self, response):
        cities = response.xpath(
            '//select[@name="ctl00$cph_main_content$spuStoreFinderResults'
            '$spuStoreFinder$ddlCity"]/option/@value'
        ).extract()
        for city in cities:
            params = "?zip=&state=&city=" + city
            yield scrapy.Request(
                response.urljoin(params), method="GET", callback=self.parse_links
            )

    def parse_links(self, response):

        latlon_js = [
            x
            for x in response.xpath(
                '//script[@type="text/javascript"]/text()'
            ).extract()
            if x.startswith("var map = new goo")
        ][0]

        store_urls = response.xpath(
            '//*[@storecode]/../a[contains(text(), "store details")]/@href'
        ).extract()
        latlons = re.findall(
            r"position: new google.maps.LatLng\(([\d.-]+),\s?([\d.-]+)\)", latlon_js
        )

        for url, latlon in zip(store_urls, latlons):
            yield scrapy.Request(
                response.urljoin(url),
                callback=self.parse_details,
                meta={"latlon": latlon},
            )

    def parse_details(self, response):
        raw_address = response.xpath(
            '//div[@class="col-sm-6 util-padding-bottom-15"]/text()'
        ).extract()
        raw_address = list(filter(None, [l.strip() for l in raw_address]))
        raw_city = raw_address.pop(-1)
        address = " ".join(raw_address)
        match_city = re.search(r"^(.*),\s([A-Z]{2})\s([0-9]{5})$", raw_city).groups()
        city = match_city[0]
        state = match_city[1]
        zipcode = match_city[2]
        phone = response.xpath(
            '//div[@class="row util-padding-top-15"]/div[@class="col-sm-6 util-padding-bottom-15"][2]/a[1]/text()'
        ).extract()[0]
        website = response.url
        opening_hours = self.process_hours(
            response.xpath('//div[@id="page_content"]/p/text()').extract()
        )
        link_id = website.split("s=")[-1]
        names = response.xpath(
            '//div[@id="page_content"]/h1/descendant-or-self::*/text()'
        ).extract()
        name = " ".join(filter(None, [n.strip() for n in names]))
        # initialize latlon incase in a rare case we dont have it
        lat = ""
        lon = ""
        if response.meta["latlon"]:
            lat = float(response.meta["latlon"][0])
            lon = float(response.meta["latlon"][1])
        properties = {
            "name": name,
            "addr_full": address,
            "city": city,
            "state": state,
            "postcode": zipcode,
            "phone": phone,
            "website": website,
            "ref": link_id,
            "opening_hours": opening_hours,
            "lat": lat,
            "lon": lon,
        }
        yield GeojsonPointItem(**properties)

    def process_hours(self, hours):
        """
        Here is the sample of the times we need to parse

        ['Open 24 hours a day, 7 days a week.\r',
        'Thanksgiving Day, Nov. 23, the store will close at 2 p.m. Reopening at 6 a.m. on Nov 24. \r',
        'The store will close at 5 p.m. Christmas Eve and remain closed Christmas Day. We will reopen at 6 a.m. on Dec 26.']

        ['24/7', {'other_hours': ['Thanksgiving Day, Nov. 23, the store will close at 2 p.m. Reopening at 6 a.m. on Nov 24. \r',
        'The store will close at 5 p.m. Christmas Eve and remain closed Christmas Day. We will reopen at 6 a.m. on Dec 26.']}]

        ['Open 24 hours a day, 7 days a week. Closing Thanksgiving at 2 p.m.
        Reopening Fri. at 6 a.m. Closing Dec. 24 at 5 p.m. Closed Dec.25 Reopening
        Dec 26 at 6 a.m. Closing Dec. 31 at 10 p.m. Reopening Jan. 1 at 6 a.m.']

        :param hours: list of opening hours
        :return:  list | string - in this format Mo-Th 11:00-12:00; Fr-Sa 11:00-01:00;
                                    or a list with the first item as 24/7 and the leftover hours
                                    which are special days like Thanksgiving, Xmas etc.
        """
        special_days = {
            "Thanksgiving:": ["Thanksgiving"],
            "Dec 24:": ["Christmas Eve", "Dec. 24"],
            "Dec 25:": ["Christmas Day", "Dec. 25"],
            "Dec 31:": ["New Years Eve", "Dec. 31"],
            "Dec 26:": ["Boxing", "Dec. 26"],
            "Jan. 1": ["New year day", "Jan. 1"],
            "24/7": [
                "7 days a week, 24 hours a day",
                "Open 24 hours a day, 7 days a week",
                "Open 24 hours 7 days a week",
                "Open 24 hours a day",
                "Open 24 hours",
                "Open 24/7",
                "We are open 24 hours a day, 7 days a week",
                "Open 24 Hours Monday-Sunday",
                "24 hours",
            ],
        }
        actions = {
            "close": [
                "the store will close at",
                "the store will be closed at",
                "closing at ",
                "closed",
                "open until",
            ],
            "open": ["Reopening at ", "Re-Opening", "re-open", "reopen at"],
        }

        result = []
        for day, vary_day in special_days.items():
            for vday in vary_day:
                matching_days = [x for x in hours if vday in x]
                if day == "24/7":
                    result.append(day)
                    break
                if matching_days:
                    for k, v in actions.items():
                        all_closed_actions = "|".join(v)
                        reg_str = (
                            r"" + vday + ".*(" + all_closed_actions + r")\s?"
                            r"(\d{1,2})\s(a\.m\.|p\.m\.)(?:\son\s(\w{3}\s\d{1,2}))?"
                        )
                        match = re.search(reg_str, matching_days[0], re.IGNORECASE)
                        if match:
                            m = match.groups()
                            result.append(
                                day
                                + " "
                                + k
                                + ": "
                                + str(int(m[1]) + self.am_pm(m[1], m[2]))
                                + ":00"
                            )
                        else:
                            reg_str = (
                                r"("
                                + all_closed_actions
                                + r")\s?(\d{1,2})\s(a\.m\.|p\.m\.)\s?("
                                + vday
                                + ")"
                            )
                            match = re.search(reg_str, matching_days[0], re.IGNORECASE)
                            if match:
                                m = match.groups()
                                result.append(
                                    day
                                    + " "
                                    + k
                                    + ": "
                                    + str(int(m[1]) + self.am_pm(m[1], m[2]))
                                    + ":00"
                                )
                            else:
                                reg_str = (
                                    r"("
                                    + all_closed_actions
                                    + r")\s?(\d{1,2})\s(a\.m\.|p\.m\.)\s?("
                                    + vday
                                    + ")"
                                )
                                match = re.search(
                                    reg_str, matching_days[0], re.IGNORECASE
                                )
                                if match:
                                    m = match.groups()
                                    result.append(
                                        day
                                        + " "
                                        + k
                                        + ": "
                                        + str(int(m[1]) + self.am_pm(m[1], m[2]))
                                        + ":00"
                                    )
                                else:
                                    # more match can come here.
                                    pass
        if "24/7" in result:
            return result.pop(result.index("24/7"))
        elif result:
            return "; ".join(result)

    def am_pm(self, hr, a_p):
        """
            A convenience method to fix noon and midnight issues
        :param hr: the hour has to be passed it to accurately decide 12noon and midnight
        :param a_p: this is either a or p i.e am pm
        :return: the hours that must be added

        """
        diff = 0
        # get rid of the whitespaces to reduce possible variation
        a_p_stripped = a_p.replace(" ", "")
        if a_p_stripped == "a.m." or a_p_stripped == "a.m":
            if int(hr) < 12:
                diff = 0
            else:
                diff = -12
        else:
            if int(hr) < 12:
                diff = 12
        return diff
