# -*- coding: utf-8 -*-
"""
Chipotle currently uses 5 3rd level domains: .com, .ca, .fr, .de and .co.uk
and we are crawling all 5
to exclude any, just comment out like this
#chipotle_urls.extend(build_links("ca", "ca", states_ca))

It appears the only way to get locations is to search by radius (in miles) and address(required) e.g
address=ADDRESS_HERE&distanceMode=1&region=REGION_HERE&pageIndex=1&countPerPage=10&radius=500
it then returns locations relative to the specified address within the specified radius.
Not so cool, but fortunately, the address can by states or city, so we can search by states
since we already know them.

Another issue is with overlapping radius, We skip this by maintaining a python set
to hold the unique link_ids so we dont totally reprocess them.

Some manual tests were ran to get a fair radius that covers all areas and not over do it
at radius = 500 we get 2392 locations
at radius = 450 we get 2392 locations
at radius = 400 we get 2385 locations
at radius = 350 we get 2379 locations
to be safe, we use 500. if some locations don't get covered in future
this is the first point to look.
"""
import scrapy
import re
import json
from locations.items import GeojsonPointItem


def build_links(tld, region_code, states):
    """
    This will build start_urls, It needs to be available before the ChipotleSpider creation

    :param tld: 3rd level domain name to use for building the links e.g .co.uk
    :param region_code: region is an important url param required for the search
    :param states: A list of states or city to search
    :return: A list of well built links which will form part our start_urls
    """
    country_links = []
    for state in states:
        start_url = "https://www.chipotle.%s/locations/search?" % (tld,)
        start_url += "address=%s&distanceMode=1&region=%s&pageIndex=1&countPerPage=10&radius=500" \
                     % (state.strip(), region_code)
        country_links.append(start_url)
    return country_links


class ChipotleSpider(scrapy.Spider):
    name = "chipotle"
    item_attributes = { 'brand': "Chipotle", 'brand_wikidata': "Q465751" }
    crawled_sites = set()

    states_com = [
                "Alabama", "Alaska", "Arizona", "Arkansas", "California",
                "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
                "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas",
                "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts",
                "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
                "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
                "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma",
                "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
                "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
                "Washington", "West Virginia", "Wisconsin", "Wyoming",
                "District of Columbia", "Puerto Rico", "Guam",
                "American Samoa", "U.S. Virgin Islands", "Northern Mariana Islands"]

    states_ca = [
                "Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland",
                "Labrador", "Nova Scotia", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan"]

    states_fr = [
                "Strasbourg", "Bordeaux", "Clermont-Ferrand", "Rennes", "Dijon",
                "Orleans", "ChAlons-en-", "Besancon", "Paris", "Montpellier",
                "Limoges", "Metz", "Caen", "Toulouse", "Lille", "Nantes", "Amiens",
                "Poitiers", "Marseille", "Lyon", "Rouen", "Ajaccio", "Cayenne",
                "Basse-Terre", "Fort-de-France", "Mamoudzou", "Saint-Denis"]
    states_de = [
                "Baden-Wurttemberg", "Bavaria", "Berlin", "Brandenburg", "Bremen",
                "Hamburg", "Hesse", "Lower", "Saxony", "Mecklenburg-Vorpommern",
                "North", "Rhine", "Rhineland-Palatinate", "Saarland", "Saxony",
                "Saxony-Anhalt", "Schleswig-Holstein", "Thuringia"]

    states_uk = [
                "London", "Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Cheshire",
                "Cornwall", "Isles of Scilly", "Cumbria", "Derbyshire", "Devon", "Dorset",
                "Durham", "East,Sussex", "Essex", "Gloucestershire", "Greater,London",
                "Greater,Manchester", "Hampshire", "Hertfordshire", "Kent", "Lancashire",
                "Leicestershire", "Lincolnshire", "Merseyside", "Norfolk", "North,Yorkshire",
                "Northamptonshire", "Northumberland", "Nottinghamshire", "Oxfordshire",
                "Shropshire", "Somerset", "South,Yorkshire", "Staffordshire", "Suffolk",
                "Surrey", "Tyne,and,Wear", "Warwickshire", "West,Midlands", "West,Sussex",
                "West,Yorkshire", "Wiltshire", "Worcestershire", "Flintshire", "Glamorgan",
                "Merionethshire", "Monmouthshire", "Montgomeryshire", "Pembrokeshire", "Radnorshire",
                "Anglesey", "Breconshire", "Caernarvonshire", "Cardiganshire", "Carmarthenshire",
                "Denbighshire", "Kirkcudbrightshire", "Lanarkshire", "Midlothian", "Moray",
                "Nairnshire", "Orkney", "Peebleshire", "Perthshire", "Renfrewshire", "Ross",
                "Cromarty", "Roxburghshire", "Selkirkshire", "Shetland", "Stirlingshire",
                "Sutherland", "West,Lothian", "Wigtownshire", "Aberdeenshire", "Angus", "Argyll",
                "Ayrshire", "Banffshire", "Berwickshire", "Bute", "Caithness", "Clackmannanshire",
                "Dumfriesshire", "Dumbartonshire", "East Lothian", "Fife", "Inverness",
                "Kincardineshire", "Kinross-shire"]

    allowed_domains = ["chipotle.com", "chipotle.ca", "chipotle.fr", "chipotle.de", "chipotle.co.uk"]
    # append all search urls
    chipotle_urls = build_links("com", "us", states_com)
    chipotle_urls.extend(build_links("ca", "ca", states_ca))
    chipotle_urls.extend(build_links("fr", "fr", states_fr))
    chipotle_urls.extend(build_links("de", "de", states_de))
    chipotle_urls.extend(build_links("co.uk", "uk", states_uk))
    start_urls = tuple(chipotle_urls)

    def parse(self, response):
        """
            For some unknown reasons, there are times response.text
            returns the string "<h2>Incomplete response received from application</h2>"
            This throws a JSONDecodeError, at this point we stop parsing and yield nothing
        """
        try:
            json_data = json.loads(response.text)
        except:
            return
        total_address = len(json_data['restaurants'])

        if json_data['restaurants']:
            # if we get results, we queue next page, until we get no result
            match = re.search(r"^(.*)(pageIndex=)(\d+)(.*)$", response.url).groups()
            new_page_index = int(match[2])+1
            new_url = match[0] + match[1] + str(new_page_index) + match[3]
            yield scrapy.Request(new_url)

        if json_data['restaurants']:
            # process only if json_data
            for address in json_data['restaurants']:
                link_id = address['id']
                # if we already processed a link, no point reprocessing
                if link_id not in self.crawled_sites:
                    # add to list of processed
                    self.crawled_sites.add(link_id)
                    address_1 = address['address1']
                    address_2 = address['address2']
                    full_address = address_1 + " " + address_2
                    city = address['city']
                    state = address['state']
                    country = address['country']
                    zip_code = address['zipcode']
                    latitude = address['latitude']
                    longitude = address['longitude']
                    phone = address['phone']
                    fax = address['fax']
                    open_hours = address['open_close_info']
                    website = address['order_url']

                    properties = {"addr_full": full_address,
                                  "city": city,
                                  "state": state,
                                  "postcode": zip_code,
                                  "country": country,
                                  "phone": self.process_phone(phone),
                                  "website": website,
                                  "ref": link_id,
                                  "opening_hours": self.process_hours(open_hours),
                                  "extras": {"fax": self.process_phone(fax)},
                                  "lon": float(longitude),
                                  "lat": float(latitude)}
                    yield GeojsonPointItem(**properties)

    def process_phone(self, phone_number):
        """
        US and CA Phone_numbers look like "804.309.0364", France & UK look like '020 7354 2431'
        Germans do this "(069) 79 58 83 55", and some None
        :param phone_number: Phone number to reformat
        :return: reformatted phone number or None
        """
        if phone_number is not None:
            match = re.search(r"^\(?(\d+)\)?.?(\d+).?(\d+).?(\d+).?(\d+)", phone_number)
            if match:
                join_matches = "".join(match.groups())
                return join_matches[0:3] + "-" + join_matches[3:6] + "-" + join_matches[6:]

    def process_hours(self, hours):
        """
        Converts the hours from ['Mon-Sat: 10:45 AM - 9:00 PM\r', 'Sun: 10:45 AM - 6:00 PM']
        to Mo-Sa 10:45-21:00; Su 10:45-18:00
        possible INPUT formats are
                            #Mon-Fri, Sun: 10:45 AM - 10:00 PM
                            #Mon-Tue, Thu, Sat, Sun: 10:45 AM - 10:00 PM
                            #Mon-Sat: 10:45 AM - 9:00 PM
                            #Sun: 10:45 AM - 6:00 PM
                            #Mon-Tue, Thu-Sun: 10:45 AM - 10:00 PM
                            #Sat-Sun: Closed
        :param hours: A list of opening hours
        :return: A string of formated hours
        """
        working_hours = []
        for hr in hours:
            # lets split day from time
            match = hr.split(":", 1)
            open_days = match[0]
            open_times = match[1].strip()
            # lets split day ranges from day
            day_ranges = open_days.split(",")
            match_times = re.search(r"(\d{1,2}):(\d{1,2})\s(AM|PM)\s-\s(\d{1,2}):(\d{1,2})\s(AM|PM)$", open_times)
            result = []

            if match_times:
                # we have time ranges, not closed
                m = match_times.groups()
                for day_range in day_ranges:
                    # if we have multiple day ranges, we loop through each and convert to e.g
                    # Mon-Fri, Sat-Sun: 10:45 AM - 10:00 PM becomes
                    # Mo-Fr 10:45-22:00; Sa-Su: 10:45-22:00
                    day = self.split_clean(day_range)
                    new_day_range = self.build_day(day)
                    day_result = new_day_range + " " + str(int(m[0]) + self.am_pm(m[0], m[2])) + ":"\
                        + m[1] + "-" + str(int(m[3]) + self.am_pm(m[3], m[5])) + ":" + m[4]
                    result.append(day_result)
            else:
                # the only reason for no match should be closed hours
                for day_range in day_ranges:
                    day = self.split_clean(day_range)
                    new_day_range = self.build_day(day)
                    day_result = new_day_range + " " + open_times
                    result.append(day_result)

            working_hours.extend(result)
        if working_hours:
            return "; ".join(working_hours)
        else:
            # if something fails, we return hours as it came
            return hours

    def am_pm(self, hr, a_p):
        """
            A convenience method to fix noon and midnight issues
        :param hr: the hour has to be passed in to accurately decide 12noon and midnight
        :param a_p: this is either a or p i.e am pm
        :return: the hours that must be added
        """
        diff = 0
        if a_p == 'AM':
            if int(hr) < 12:
                diff = 0
            else:
                diff = -12
        else:
            if int(hr) < 12:
                diff = 12
        return diff

    def split_clean(self, what_to_split):
        """
        Split by - and remove whitespaces
        :param what_to_split:
        :return:
        """
        return list(map(lambda x: x.strip(), what_to_split.split("-")))

    def build_day(self, day):
        """
        day come in these variants Mon-Sat | Mon, lets build it
        :param day:
        :return:
        """
        if len(day) == 1:
            return day[0][0:2]
        else:
            return day[0][0:2] + "-" + day[1][0:2]
