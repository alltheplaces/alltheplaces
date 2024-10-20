from locations.hours import DAYS, OpeningHours
from locations.storefinders.algolia import AlgoliaSpider


class TagHeuerSpider(AlgoliaSpider):
    name = "tag_heuer"
    item_attributes = {
        "brand_wikidata": "Q645984",
        "brand": "TAG Heuer",
    }
    api_key = "8cf40864df513111d39148923f754024"
    app_id = "6OBGA4VJKI"
    index_name = "stores"
    myfilter = "type:FRANCHISE OR type:TAGSTORE"

    # {"params":"filters=products.mechanicalWatches:true AND country:GB&attributesToRetrieve=address,Latitude,zip,country,phone,type,id,image,address2,email,name,description,services,payments,city,openingHours,exceptionalHours,_geoloc,i18nAddress,image1,timezone,sfccUrl","aroundRadius":"15000","hitsPerPage":"1000","getRankingInfo":"1","attributesToRetrieve":"address,Latitude,zip,country,phone,type,id,image,address2,email,name,description,services,payments,city,openingHours,exceptionalHours,_geoloc,i18nAddress,image1,timezone,sfccUrl","attributesToHighlight":"name"}

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        item["ref"] = feature["objectID"]
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["image"] = feature["image"]
        slug = feature["sfccUrl"]
        item["website"] = f"https://www.tagheuer.com/{slug}"

        oh = OpeningHours()
        if feature["openingHours"]:
            for j in range(1, 7):
                if j == 7:
                    i = 0
                else:
                    i = j
                try:
                    oh.add_range(
                        DAYS[j], feature["openingHours"][str(i)][0]["start"], feature["openingHours"][str(i)][0]["end"]
                    )
                except:
                    self.logger.error("No opening hour on day" + str(i))
            item["opening_hours"] = oh

        yield item
