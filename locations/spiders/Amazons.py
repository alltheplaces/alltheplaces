import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import  requests
from locations.items import  GeojsonPointItem

User_Agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"


days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
days_short =["Mon","Tue","Wed","Thur","Fri","Sat","Sun"]
days_want = ["Mo","Tu","We","Th","Fr","Sa","Su"]
days_dict = {i:n for n,i in enumerate(days_want)}
days_rev_dict = {n:i for n,i in enumerate(days_want)}
class AmazonsSpider(CrawlSpider):
    name = 'Amazons'
    allowed_domains = ['amazon.com']
    # start_urls = ['']
    user_agent = (
        User_Agent
    )

    def start_requests(self):
        yield scrapy.Request(
            url="https://www.amazon.com/find-your-store/b/?node=17608448011",
            headers={"User-Agent":self.user_agent}
        )

    rules = (
        Rule(LinkExtractor(restrict_xpaths="//p/a"),
             callback='parse_item',
             follow=True,
             process_request="set_user_agent"),
    )
    def set_user_agent(self, request):
        request.headers["User-Agent"] = self.user_agent
        return request

    def parse_item(self, response):
        item = {}
        openhours = []
        linker = []
        locations = None
        phela = None
        naam = response.xpath("//h2/text()").get()
        lot_of = response.xpath("//div[@class='bxc-grid__text a-text-left   bxc-grid__text--light']//p")
        if naam:
            item["name"] = naam
        if lot_of:
            for i in lot_of:
                add = i.xpath("//p/a/text()").get()
                linked = i.xpath("//p/a/@href").get()
                done = linked.split('@')
                if len(done) == 2:
                    locations = done[1].split(',')[:2]
                for j in i.xpath("//p/text()").getall():
                    try:
                        days = j.split(':')
                        for x,y in zip(days,days_short):
                            f = []
                            u = []
                            if x in days or y in days:
                                try:
                                    f = list(map(str.strip,days[0].split('-')))
                                    u = list(map(str.strip,days[1].split('-')))
                                except Exception:
                                    continue
                        days = [i[:2] for i in f if 8 > len(i) >= 3 and i[0].isalpha() and i[:2] in days_want]
                        time = [i for i in u if i[0].isdigit()]
                        time.append(time[0][:2]+":00")
                        if 'p' in time[1] or 'p'.upper() in time[1] and time[1][0].isdigit():
                            time.append(str(int(time[1][0])+12)+":00")
                        if days:
                            if len(days) == 2:
                                one, two = days_dict[days[0]], days_dict[days[1]]
                                if two > one:
                                    for i in range(one,two+1):
                                        openhours.append({"Day":days_rev_dict[i],"open":time[2],"close":time[3]})
                                else:
                                    for j in range(two,one+1):
                                        openhours.append({"Day":days_rev_dict[i],"open":time[2],"close":time[3]})
                            else:
                                openhours.append({"Day":days[0],"open":time[2],"close":time[3]})
                    except Exception:
                        continue
                    if not (j in [':',': '] and j in ':\n') and len(j) < 20:
                        ok = j.strip(':').strip('\n')
                        if ok == 'To come':
                            continue
                        if len(ok) > 12:
                            if ok[0] == '(':
                                item["phone"] = ok
                            elif ok not in '\n' and ok not in ' ':
                                item["Timings"] = ok
                if '\n' in add:
                    add = add.replace("\n"," ")
                div = add.split(',')
                some = add.split(' ')
                for i in range(len(some)):
                    if ',' in some[i] and len(some[i-1])<4 and i >1:
                        item["extras"] = some[i-1] + " "+some[i]
                if some[0][0].isdigit():
                    item["housenumber"] = some[0]
                    item["street"] = some[1] + " "+some[2]
                if len(div) == 2:
                    try:
                        item["city"]= div[0].split(' ')[-1]
                        item["state"] = div[1].split(' ')[1]
                        item["postcode"] = div[1].split(' ')[2]
                    except Exception as ex:
                        item["city"] = div[0].split(' ')[-2]+" "+div[0].split(' ')[-1]
                        item["postcode"] = div[1]
                        item["state"] = div[0].split(' ')[-1]
                item["addr_full"] = add
                if locations:
                    item["lat"] = locations[0]
                    item["lon"] = locations[1]
                else:
                    item["lat"] = None
                    item["lon"] = None
                try:
                    item['phone']
                except Exception:
                    item['phone'] = None
                if openhours:
                    item["opening_hours"] = openhours
                item.pop("Timings",None)
                break
        if item and len(item) > 2:
            yield GeojsonPointItem(item)
