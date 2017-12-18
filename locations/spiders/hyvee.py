# -*- coding: utf-8 -*-
"""
Hy-Vee has 155 locations we need and they inplemented a server-side javascript detector logic
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
"""
import scrapy
import re
from locations.items import GeojsonPointItem


class HyVeeSpider(scrapy.Spider):
    name = "hyvee"
    allowed_domains = ["hy-vee.com"]

    def start_requests(self):
        """
        We need to make the inital request use a PUT method
        They have a serverside javascript detector logic in place
        on GET and POST requests
        :return:
        """
        url = 'https://www.hy-vee.com/stores/store-finder-results.aspx'
        yield scrapy.Request(url, method='PUT', callback=self.parse)

    def parse(self, response):
        cities = response.xpath('//select[@name="ctl00$cph_main_content$spuStoreFinderResults'
                                '$spuStoreFinder$ddlCity"]/option/@value').extract()
        for city in cities:
            params = "?zip=&state=&city=" + city + "&olfloral=False&olcatering=False&olgrocery=True" \
                     "&olpre=False&olbakery=False&diet=False&chef=False"
            yield scrapy.Request(
                                 response.urljoin(params),
                                 method='PUT',
                                 callback=self.parse_links)

    def parse_links(self, response):
        store_url = response.xpath('//a[@id="ctl00_cph_main_content_spuStoreFinderResults'
                                   '_gvStores_ctl02_aStoreDetails"]/@href').extract()
        if store_url:
            latlon_js = [x for x in response.xpath('//script[@type="text/javascript"]/text()')
                         .extract() if x.startswith('var map = new goo')][0]
            latlon_find = re.search(r"google\.maps\.LatLng\((-?\d*\.\d*),\s(-?\d*\.\d*)\),\s*zoom:", latlon_js)
            request = scrapy.Request(
                                     response.urljoin(store_url[0]),
                                     method='PUT',
                                     callback=self.parse_details)
            if latlon_find:
                request.meta['latlon'] = latlon_find.groups()
            yield request

    def parse_details(self, response):
        raw_address = response.xpath('//div[@class="col-sm-6 util-padding-bottom-15"]/text()').extract()
        address = raw_address[1].strip()
        raw_city = raw_address[2].strip()
        match_city = re.search(r"^(.*),\s([A-Z]{2})\s([0-9]{5})$", raw_city).groups()
        city = match_city[0]
        state = match_city[1]
        zipcode = match_city[2]
        phone = response.xpath('//div[@class="row util-padding-top-15"]/div[@class="col-sm-6 util-padding-bottom-15"][2]/a[1]/text()').extract()[0]
        website = response.url
        extra_open_hours = self.process_dept_hours(response.xpath('//table[@class="storeHours table"]/tr').extract())
        opening_hours = self.process_hours(response.xpath('//div[@id="page_content"]/p/text()').extract())
        extras = {"department_hours": extra_open_hours, "special_days": opening_hours[1]}
        link_id = website.split("s=")[-1]
        # initialize latlon incase in a rare case we dont have it
        lat = ''
        lon = ''
        if response.meta['latlon']:
            lat = float(response.meta['latlon'][0])
            lon = float(response.meta['latlon'][1])
        properties = {
            "addr_full": address,
            "city": city,
            "state": state,
            "postcode": zipcode,
            "phone": phone,
            "website": website,
            "ref": link_id,
            "opening_hours": opening_hours[0],
            "lat": lat,
            "lon": lon,
            "extras": extras
        }
        logme(str(GeojsonPointItem(**properties))+"\n", "log.txt")
        yield GeojsonPointItem(**properties)

    def process_dept_hours(self, hours):
        """
        Returns the departmental open hours
        :param hours: list of hours in html
        :return:
        """
        dept = []
        for hour in hours:
            #extract from html first
            hour_search = re.search(r"<strong>(\w*)</strong>:\s*</td>\s*<td>\s*([-0-9a-zA-Z\s.;]*)\s*</td>", hour)
            if hour_search:
                m = hour_search.groups()
                split_hours = m[1].split(";")
                formatted_hours = []
                for hr in split_hours:
                    hour_search = re.search(r"(\d{1,2}).?\s*(a.\s?m.?|p.\s?m.?)\s*(?:to|-)?\s*(\d{1,2}).?\s*(a.\s?m.?|p.\s?m.?)\s*(daily)?(?:(\w{2})\w*-?(\w{2})?\w*?)?", hr)
                    if hour_search:
                        hrr = hour_search.groups()
                        if hrr[4] == "daily" or (hrr[6] is None and hrr[5] is None and hrr[4] is None):
                            format_hours = "Mo-Su "+str(int(hrr[0]) + self.am_pm(hrr[0], hrr[1])).zfill(
                                2) + ":00" + "-" + str(int(hrr[2]) + self.am_pm(hrr[2], hrr[3])).zfill(2) + ":00"
                        elif hrr[6] is None and hrr[5] is None:
                            format_hours = str(int(hrr[0]) + self.am_pm(hrr[0], hrr[1])).zfill(
                                2) + ":00" + "-" + str(int(hrr[2]) + self.am_pm(hrr[2], hrr[3])).zfill(2) + ":00"
                        elif hrr[6] is None:
                            format_hours = hrr[5] + " " + str(int(hrr[0]) + self.am_pm(hrr[0], hrr[1])).zfill(
                                2) + ":00" + "-" + str(int(hrr[2]) + self.am_pm(hrr[2], hrr[3])).zfill(2) + ":00"
                        else:
                            format_hours = hrr[5] + "-" + str(hrr[6]) + " " + str(
                                int(hrr[0]) + self.am_pm(hrr[0], hrr[1])).zfill(2) + ":00" + "-" + \
                                           str(int(hrr[2]) + self.am_pm(hrr[2], hrr[3])).zfill(2) + ":00"
                        # lets append our catch
                        formatted_hours.append(format_hours)
                    else:
                        # no match but there are some funny strings that made it through that we need to fix
                        # e.g 10 a.m. to 4 p .m. Sunday , 5 a.m. to midnight ,  7 a.m.
                        # should be Su 10:00-16:00; 5:00-00:00;
                        # with no corresponding closing hr
                        hour_search = re.search(r"(\d{1,2})\s([amp\.\s]*)\sto\s(?:(\d{1,2})\s([amp\.\s]*)\s(\w{2}))?(\w*)", hr.strip())
                        if hour_search:
                            hrr = hour_search.groups()
                            if hrr[5] == 'midnight' and hrr[2] is None and hrr[3] is None and hrr[4] is None:
                                format_hours = str(int(hrr[0]) + self.am_pm(hrr[0], hrr[1])).zfill(2) + ":00-00:00"
                            elif hrr[2] is not None and hrr[3] is not None and hrr[4] is not None:
                                format_hours = hrr[4] + " " + str(int(hrr[0]) + self.am_pm(hrr[0], hrr[1])).zfill(2) + \
                                               ":00-" + str(int(hrr[2]) + self.am_pm(hrr[2], hrr[3])) + ":00"
                            # append whatever we catch
                            formatted_hours.append(format_hours)
                        else:
                            # lets capture this https://www.hy-vee.com/stores/detail.aspx?s=21
                            # Catering 7 a.m. on that page should be 7:00, should apply to pm too
                            hour_search = re.search(r"(\d{1,2})\s([amp\.\s]*)", hr.strip(), re.IGNORECASE)
                            if hour_search:
                                hrr = hour_search.groups()
                                format_hours = str(int(hrr[0]) + self.am_pm(hrr[0], hrr[1])).zfill(2) + ":00"
                                formatted_hours.append(format_hours)
                            else:
                                formatted_hours.append(hr.strip())
                dept.append(m[0] + ": " + "; ".join(formatted_hours))
            else:
                # if all fails, we capture it
                hour_search = re.search(r"<strong>\s*(.*)\s*</strong>:\s*</td>\s*<td>\s*(.*)\s*</td>\s*", hour.strip(), re.IGNORECASE)
                if hour_search:
                    hrr = hour_search.groups()
                    #lets split this by <br>
                    split_hours = hrr[1].split("<br>")
                    for hr_range in split_hours:                                    #Monday-Sunday 6AM-9PM
                        hr_search = re.search(r"(?:(\w{2})?\w*-?(\w{2})?\w*:?\s?(\d{1,2})\s*([amp.\s]*)\s*(-|to)\s*(\d{1,2})\s*([amp.\s]*))|(24-hour\s*|\s*24\s*hours)", hr_range, re.IGNORECASE)
                        if hr_search:
                            m = hr_search.groups()
                            if m[0] is not None and m[1] is not None:
                                format_hours = m[0] + "-" + m[1] + " " + str(int(m[2]) + self.am_pm(m[2], m[3])).zfill(
                                    2) + ":00-" + str(int(m[5]) + self.am_pm(m[5], m[6])).zfill(2) + ":00"
                            elif m[0] is not None and m[1] is None:
                                format_hours = m[0] + " " + str(int(m[2]) + self.am_pm(m[2], m[3])).zfill(2) + ":00-" + str(
                                    int(m[5]) + self.am_pm(m[5], m[6])).zfill(2) + ":00"
                            elif m[0] is None and m[1] is None and m[7] is None:
                                format_hours = str(int(m[2]) + self.am_pm(m[2], m[3])).zfill(2) + ":00-" + str(
                                    int(m[5]) + self.am_pm(m[5], m[6])).zfill(2) + ":00"
                            elif m[7] is not None:
                                format_hours = '24/7'
                        else:
                            # we append if no match
                            format_hours = hr_range

                    format_hours = hrr[0].replace("&amp;","&") + ": " + format_hours
                    dept.append(format_hours)
                else:
                    dept.append(hour)
        return dept

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
        special_days = {"Thanksgiving:": ['Thanksgiving'],
                        "Dec 24:": ['Christmas Eve', 'Dec. 24'],
                        "Dec 25:": ['Christmas Day', 'Dec. 25'],
                        "Dec 31:": ['New Years Eve', 'Dec. 31'],
                        "Dec 26:": ['Boxing', 'Dec. 26'],
                        "Jan. 1": ['New year day', 'Jan. 1'],
                        "24/7": ["7 days a week, 24 hours a day",
                                 "Open 24 hours a day, 7 days a week",
                                 "Open 24 hours 7 days a week",
                                 "Open 24 hours a day",
                                 "Open 24 hours",
                                 "Open 24/7",
                                 "We are open 24 hours a day, 7 days a week",
                                 "Open 24 Hours Monday-Sunday",
                                 "24 hours"]}
        actions = {
                    "close": [
                              'the store will close at',
                              'the store will be closed at',
                              'closing at ',
                              'closed',
                              'open until'],
                    "open": ['Reopening at ',
                             'Re-Opening',
                             're-open',
                             'reopen at']}

        result = []
        for day, vary_day in special_days.items():
            for vday in vary_day:
                matching_days = [x for x in hours if vday in x]
                if day == '24/7':
                    result.append(day)
                    break
                if matching_days:
                    for k, v in actions.items():
                        all_closed_actions = "|".join(v)
                        reg_str = r"" + vday + ".*(" + all_closed_actions + ")\s?" \
                                  r"(\d{1,2})\s(a\.m\.|p\.m\.)(?:\son\s(\w{3}\s\d{1,2}))?"
                        match = re.search(reg_str, matching_days[0], re.IGNORECASE)
                        if match:
                            m = match.groups()
                            result.append(day + " " + k + ": " + str(int(m[1]) + self.am_pm(m[1], m[2])) + ":00")
                        else:
                            reg_str = r"(" + all_closed_actions + ")\s?(\d{1,2})\s(a\.m\.|p\.m\.)\s?(" + vday + ")"
                            match = re.search(reg_str, matching_days[0], re.IGNORECASE)
                            if match:
                                m = match.groups()
                                result.append(day + " " + k + ": " + str(int(m[1]) + self.am_pm(m[1], m[2])) + ":00")
                            else:
                                reg_str = r"(" + all_closed_actions + ")\s?(\d{1,2})\s(a\.m\.|p\.m\.)\s?(" + vday + ")"
                                match = re.search(reg_str, matching_days[0], re.IGNORECASE)
                                if match:
                                    m = match.groups()
                                    result.append(day + " " + k + ": " + str(int(m[1]) + self.am_pm(m[1], m[2])) + ":00")
                                else:
                                    # more match can come here.
                                    pass
        if '24/7' in result:
            return [result.pop(result.index('24/7')), "; ".join(result)]
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
        if a_p_stripped == 'a.m.' or a_p_stripped == 'a.m':
            if int(hr) < 12:
                diff = 0
            else:
                diff = -12
        else:
            if int(hr) < 12:
                diff = 12
        return diff

def logme(strr, f):
    h=open(f, 'a')
    h.write(str(strr)+"\n")
    h.close()