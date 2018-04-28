import scrapy
import xml.etree.ElementTree as ET

from locations.items import GeojsonPointItem


URL = 'http://hosted.where2getit.com/auntieannes/2014/ajax?&xml_request=%3Crequest%3E%3Cappkey%3E6B95F8A2-0C8A-11DF-A056-A52C2C77206B%3C%2Fappkey%3E%3Cformdata+id%3D%22locatorsearch%22%3E%3Cdataview%3Estore_default%3C%2Fdataview%3E%3Climit%3E250%3C%2Flimit%3E%3Cgeolocs%3E%3Cgeoloc%3E%3Caddressline%3E{}%3C%2Faddressline%3E%3Clongitude%3E%3C%2Flongitude%3E%3Clatitude%3E%3C%2Flatitude%3E%3Ccountry%3E{}%3C%2Fcountry%3E%3C%2Fgeoloc%3E%3C%2Fgeolocs%3E%3Cwhere%3E%3Cor%3E%3Chascatering%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fhascatering%3E%3Chaspretzelfieldtrip%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fhaspretzelfieldtrip%3E%3Cnewstores%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fnewstores%3E%3C%2For%3E%3C%2Fwhere%3E%3Csearchradius%3E10%7C25%7C50%7C100%7C250%7C500%7C750%7C1000%3C%2Fsearchradius%3E%3Cstateonly%3E1%3C%2Fstateonly%3E%3C%2Fformdata%3E%3C%2Frequest%3E'

US_STATES = (
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
)

UK_Cities = (
        'London', 'Birmingham', 'Manchester', 'Glasgow', 'Leeds',
        'Liverpool', 'Bristol', 'Newcastle', 'Sunderland', 'Wolverhampton',
        'Nottingham', 'Sheffield', 'Belfast', 'Leicester', 'Bradford',

)

UAE_Cities = (
        "Abu Dhabi", "Sharjah", "Dubai", "Dayrah","Al Ain",
        "Fujairah", "Ras al-Khaimah", "Ar Ruways", "As Satwah",
        "Al Khan",
)

TT_Cities = (
        "Arima", "San Fernando", "Princes Town", "Piarco", "RioClaro", "Port of Spain",
        "Victoria", "Maraval", "Fyzabad", "Debe", "Couva", "Diego Martin", "Chaguanas",
        "Penal", "Cunupia", "Curepe", "Roxborough", "San Juan", "Arouca", "Saint Joseph",
        "California", "Marabella", "Siparia", "Gasparillo", "Morvant", "Barataria", "Saint Clair",
        "Laventille", "Carenage", "Ward of Tacarigua", "Caroni", "Lopinot", "Tunapuna", "Santa Cruz",
        "Saint Augustine", "Golden Lane", "Scarborough", "Moriah", "Saint James", "Carapichaima",
        "Valsayn", "Freeport", "Claxton Bay", "Sangre Grande", "Cumuto", "Woodbrook", "Petit Valley",
        "El Dorado", "Phoenix Park",
)

Thailand_Cities = (
        "Bangkok", "Chumphon", "Kathu", "Phang Khon", "Sakon Nakhon", "Mueang Nonthaburi",
        "Kalasin", "Chon Buri", "Loei", "Khon Kaen", "Nong Bua Lamphu", "Roi Et", "Udon Thani",
        "Kumphawapi", "Kanchanaburi", "Nong Khai", "Ayutthaya", "Chiang Mai", "Songkhla",
        "Chiang Rai", "Surin", "Thanyaburi", "Wiphawadi", "Phuket", "Sing Buri", "Satun",
        "Prachin Buri", "Ubon Ratchathani", "Pattaya", "Yala", "Bang Na", "Samut Songkhram", "Phetchabun"
        "Ratchaburi", "Lampang", "Narathiwat", "New Sukhothai", "Lopburi", "Uttaradit", "Maha Sarakham",
        "Mae Hong Son", "Suphan Buri", "Chachoengsao", "Samut Sakhon", "Phrae", "Din Daeng",
        "Pathum Wan", "Phayao", "Trang", "Mukdahan", "Phetchaburi", "Uthai Thani", "Krabi", "Phichit",
        "Phitsanulok", "Ban Pat Mon", "Prachuap Khiri Khan", "Ban Khlong Prasong", "Yasothon",
        "Ranong", "Lamphun", "Nong Bua", "Amnat Charoen", "Ban Phichit", "Bang Khae", "Thon Buri",
        "Min Buri", "Ban Tham", "Sam Sen", "Ang Thong", "Mueang Samut Prakan", "Sa Kaeo", "Pathum Thani",
        "Chanthaburi", "Huai Khwang", "Rayong", "Sattahip", "Phan", "Si Racha", "Phatthalung",
        "Rawai", "Buriram", "Dusit", "Khlong Luang", "Trat", "Ban Bueng", "Sung Noen", "Manorom",
        "Ban Bang Plong", "Tak", "Ban Tha Duea", "Amphawa", "Ban Pong Lang", "Phaya Thai", "Si Sa Ket",
        "Nakhon Ratchasima", "Bang Phlat", "Ban Bang Phli Nakhon", "Salaya", "Krathum Baen",
        "Hua Hin", "Ban Talat Rangsit", "Ban Khlong Ngae", "Nong Prue", "Wang Thonglang",
        "Samphanthawong", "Bang Khun Thian", "Chatuchak", "Chaiyaphum",
        "Nakhon Pathom", "Nan", "Bang Kruai", "Sathon", "Suan Luang", "Ban Wang Yai"
        "Khlong San", "Watthana", "Lat Krabang", "Muak Lek", "Kosum Phisai", "Ban Phlam", "Non Thai",
        "Photharam", "Thalang", "Bang Kapi", "Long", "Ka Bang", "Pattani", "Nakhon Si Thammarat",
        "Khlong Toei", "Cha-am", "Amphoe Aranyaprathet", "Phang Nga", "Ban Tha Ruea", "Chiang Muan",
        "Ban Ang Thong", "Ban Khlong Takhian", "Khan Na Yao", "Bang Sue", "Sam Khok", "Don Mueang",
        "Ban Pratunam Tha Khai","Sena", "Prakanong", "Ban Tha Pai", "Bang Lamung", "Nakhon Sawan",
        "San Sai", "Kamphaeng Phet", "Pak Kret", "Hat Yai", "Ban Nam Hak", "Khlung", "Makkasan",
        "Bang Sao Thong", "Ban Hua Thale", "Klaeng", "Chulabhorn", "Ban Don Sak", "Phanna Nikhom",
        "Ban Na", "Ban Ko Pao","Mae Sot"
)
Korea_Cities = (
        "Seoul", "Incheon", "Paju", "Cheonan", "Yongin", "Kwanghui-dong", "Pon-dong",
        "Gwangju", "Gwangmyeong", "Tang-ni", "Busan", "Seongnam-si", "Suwon-si", "Namyang",
        "Namyangju", "Jeju-si", "Ulsan", "Osan", "Hanam", "Pyong-gol", "Anyang-si",
        "Yangsan", "Daejeon", "Nonsan", "Seocho", "Wonju", "Kisa", "Daegu", "Ansan-si", "Gongju",
        "Haeundae", "Sasang", "Bucheon-si", "Chuncheon", "Ilsan-dong", "Naju", "Jinju", "Uiwang",
        "Gangneung", "Yongsan-dong", "Pohang", "Changwon", "Jeonju", "Yeosu",
        "Songnim", "Gimhae", "Songjeong", "Hyoja-dong", "Icheon-si", "Kimso", "Iksan", "Deokjin",
        "Koyang-dong", "Samsung", "Anseong", "Samjung-ni", "Mapo-dong", "Gunnae", "Nae-ri",
        "Suncheon", "Okpo-dong", "Moppo", "Sangdo-dong", "Cheongju-si", "Ch'aeun",
        "Taebuk", "Yeoju", "Seong-dong", "Duchon", "Gyeongju", "Andong", "Seosan City", "Asan",
        "Miryang", "Wonmi-gu", "Janghowon", "Chungnim", "Songam", "Tongan", "Ap'o", "Jecheon",
        "Se-ri", "Ka-ri", "Hansol", "Songang", "Hyangyang", "Gyeongsan-si", "Gumi", "Unpo",
        "Ulchin", "Namhyang-dong", "T'aebaek", "Hadong", "Haesan", "Chungju", "Chilgok",
)

Singapore_Cities = (
        "Singapore", "Yishun New Town", "Bedok New Town", "Ayer Raja New Town",
        "Kalang", "Tampines New Town", "Ang Mo Kio New Town", "Kampong Pasir Ris", "Hougang",
        "Yew Tee", "Choa Chu Kang New Town", "Punggol", "Changi Village", "Bukit Timah Estate",
        "Serangoon", "Jurong Town", "Tanglin Halt", "Woodlands New Town", "Jurong East New Town",
        "Bukit Panjang New Town", "Bukit Batok New Town", "Pasir Panjang", "Holland Village",
        "Tai Seng", "Toa Payoh New Town", "Bukit Timah", "Jurong West New Town", "Kembangan",
        "Queenstown Estate", "Boon Lay", "Simei New Town", "Pandan Valley", "Clementi New Town",
        "Tanjong Pagar"
)

Saudi_Arabia_Cities = (
        "Riyadh", "Dammam", "Safwa", "Al Qatif", "Dhahran", "Al Faruq", "Khobar", "Jubail",
        "Sayhat", "Jeddah", "Ta'if", "Mecca", "Al Hufuf", "Medina", "Rahimah", "Rabigh",
        "Yanbu` al Bahr", "Abqaiq", "Mina", "Ramdah", "Linah", "Abha", "Jizan", "Al Yamamah",
        "Tabuk", "Sambah", "Ras Tanura", "At Tuwal", "Sabya", "Buraidah", "Najran", "Sakaka",
        "Madinat Yanbu` as Sina`iyah", "Hayil", "Khulays", "Khamis Mushait", "Ra's al Khafji",
        "Al Bahah", "Rahman", "Jazirah", "Jazirah"
)

Indonesia_Cities = (
        "Jakarta", "Surabaya", "Medan", "Bandung", "Bekasi", "Palembang", "Tangerang", "Makassar",
        "Semarang", "South Tangerang",
)

Malaysia_Cities = (
        "Kaula Lumpur", "Kota Bharu", "Klang", "Johor Bahru", "Subang Jaya", "Ipoh", "Kuching", "Seremban",
        "Petaling Jaya", "Shah Alam", 'Penang', 'Kelantan', "Pantai", "Petaling Jaya",  "Kajang",
        "Setapak", "Bukit Kayu Hitam", "Bayan Lepas", "Taiping", "Kuala Terengganu", "Kuantan",
        "Alor Gajah",
)
Japan_Cities = (
        'Tokyo', "Hiroshima", "Saitama", "Nihon'odori", "Ibaraki", "Urayasu",
        "Suita", "Funabashi", "Nagareyama", "Ichikawa", "Isesaki", "Koga", "Ichihara",
        "Koshigaya", "Shibukawa", "Aoicho", "Yamakita", "Gotemba", "Nisshin", "Nishinomiya",
        "Den'en-chofu", "Kawasaki", "Toyama-shi", "Moriguchi", "Chita", "Sano", "Nagoya-shi",
        "Kyoto", "Hamamatsu", "Shimotoda", "Yachiyo", "Tsukuba", "Chiba", "Yokohama",
        "Yamanashi", "Ashihara", "Kawaguchi", "Kasukabe", "Shizuoka", "Kawanishi", "Itami",
        "Kobe", "Nara", "Yao", "Osaka", "Handa", "Honjocho", "Kishiwada", "Susono", "Nagasaki",
        "Setagaya-ku", "Zushi", "Sugito", "Yabasehoncho", "Yamaguchi", "Kanazawa", "Maruyama",
        "Tahara", "Obu", "Nishio", "Okinawa", "Urasoe", "Naha", "Chichibu", "Asahi", "Kita-sannomaru",
        "Hirokawa", "Ishigaki", "Higashine", "Tsuruoka", "Asahikawa", "Minatomachi", "Sannohe",
        "Tottori-shi", "Higashiasahimachi", "Iwata", "Koriyama", "Hanno", "Takarazuka", "Kuwana-shi",
        "Kakogawa", "Komaki", "Mitake", "Tondabayashi", "Matsumoto", "Kakamigahara", "Onomichi",
        "Kure", "Maebaru", "Tokai",
)

COUNTRIES = {
        'US': US_STATES,
        'UK': UK_Cities,
        'AE': UAE_Cities,
        'TT': TT_Cities,
        'TH': Thailand_Cities,
        'KR': Korea_Cities,
        'SG': Singapore_Cities,
        'SA': Saudi_Arabia_Cities,
        'ID': Indonesia_Cities,
        'MY': Malaysia_Cities,
        'JP': Japan_Cities
}

TAGS = [
        'city', 'country', 'latitude', 'longitude',
        'phone', 'postalcode', 'state', 'uid'
]

MAPPING = {
        'latitude': 'lat', 'longitude': 'lon', 'uid': 'ref',
        'postalcode': 'postcode',
}


class AuntieAnnesSpider(scrapy.Spider):

    name = "auntie_annes"
    allowed_domains = ["hosted.where2getit.com/auntieannes"]
    download_delay = 0.2

    def process_poi(self, poi):
        props = {}
        add_parts = []

        for child in poi:
            if child.tag in TAGS and child.tag in MAPPING:
                if child.tag in ('latitude', 'longitude'):
                    props[MAPPING[child.tag]] = float(child.text)
                else:
                    props[MAPPING[child.tag]] = child.text

            elif child.tag in TAGS and child.tag not in MAPPING:
                props[child.tag] = child.text

            elif child.tag in ('address1', 'address2', 'address3', ):
                add_parts.append(child.text if child.text else '')

        props.update({'addr_full': ', '.join(filter(None, add_parts))})

        return GeojsonPointItem(**props)

    def start_requests(self):

        for country, locations in COUNTRIES.items():
            for location in locations:
                loc = "+".join(location.split(' '))
                url = URL.format(location, country)
                yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):

        root = ET.fromstring(response.text)
        collection = root.getchildren()[0]
        pois = collection.findall('poi')

        for poi in pois:
            yield self.process_poi(poi)
