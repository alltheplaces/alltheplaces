## Detection

### Inspection of site

All The Places provides rudimentary tooling to inspect a site for common behaviours.

* [Sitemap inspection](SITEMAP.md) - `pipenv run scrapy sitemap http://example.com/` to detect potential individual store URLs.
* [Structured Data inspection](STRUCTURED_DATA.md) - `pipenv run scrapy sd http://example.com/` to detect potential individual store URLs.
* Links - `pipenv run scrapy links http://example.com/` to look for links with human language labels, such as "Find our stores".

When checking a large number of URLs, these tools can be chained together to highlight potential candidates for spidering.

### Automatic detection from storefinder page

There exist numerous third-party software-as-a-service APIs or self-installed web application software which are used by brands for providing a locations finder or branch locator page on brand websites. All The Places provides reusable [storefinder](../locations/storefinders/) classes, allowing a spider for each brand to inherit common behaviour reducing having to add individually duplicate complex crawler code.

Going one step further, many of these storefinders build in the capabilities to automatically detect the
presence of a common software deployment from either:

- Request patterns made to API endpoints or
- Responses where the HTML matches xpath or creates JS Objects indicating the presence of a store locator.

To automatically attempt detection, pass in a start URL - either the top level domain, or
the specific store page.
Hint: You may wish to use the `pipenv run scrapy links http://example.com/` command to automatically look for
probable store location pages if you are reviewing a number of top level domains.

Example:
```
ubuntu@codespaces-dc76c9:/workspaces/alltheplaces$ pipenv run scrapy sf https://www.saveonfoods.com/
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class SaveOnFoodsCASpider(StorefrontgatewaySpider):
    name = "saveonfoods_ca"
    item_attributes = {
        "brand_wikidata": "Q7427974",
        "brand": "Save-On-Foods",
    }
    start_urls = [
        "https://storefrontgateway.saveonfoods.com/api/",
    ]
```

This tool will attempt to generate a useful class name and spider key name by resolving the URL to any wikidata or name suggestion index entries it can. It will also extract all other attributes to get you started; however you should still run and adjust the generated code before opening a pull request.

If known, you can specify extra arguments such as `--brand-wikidata` or `--brand`

For full usage, run `pipenv run scrapy sf`

### Manual Generation

Where a storefinder isn't detected but you still wish to get a jump start on writing a spider to a common pattern,
use the `pipenv run scrapy genspider` command to generate a common template.

For example, `pipenv run scrapy genspider my_spider_name http://example.com/robots.txt -t sitemap` generates a sitemap spider for example.com with the name my_spider_name.

See the available [templates](../locations/templates) for more, or the [scrapy documentation](https://docs.scrapy.org/en/latest/topics/commands.html#genspider) for further details.

## Adding autodetection to a storefinder

If you have identified a reliable pattern and are creating a storefinder, to add auto detection use one or more of:

- DetectionRequestRule
- DetectionResponseRule

Example:
```
from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule, DetectionResponseRule

class MyNewStoreLocatorSpider(Spider, AutomaticSpiderGenerator):

    detection_rules = [
        # Detect using regex, populating the allowed_domains variable as a list
        DetectionRequestRule(url=r"^https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)\/some\/pattern\/here\/?"),
        DetectionRequestRule(
            url=r"^(?P<start_urls__list>https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)(?:\/[^\/]+)+\/some_other_pattern\/index\/ajax\/?)$"
        ),
        # Or via inspecting the js_objects in memory
        DetectionResponseRule(js_objects={"api_key": r"window.__closeby__.mapKey"}),

        # Or by more traditional xpath
        DetectionResponseRule(xpaths={"company_id": r"//script/@data-storemapper-id"}),
    ]
```

In general, the detection rules attempt to not only detect a telltale pattern; but to also map it to the key variables needed.

See `locations.automatic_spider_generator` for the full possibilities of the API.

Once you have a pattern you think is right; add your newly empowered storefinder to `StorefinderDetectorSpider`'s lists of
automatic detections to attempt.

#### Detection Rules - How do they work?

Playwright with Firefox (Chromium not supported) is required and is used to load the requested URL in a Firefox headless session.

The Playwright Firefox session is kept alive for 30 seconds to observe any dynamic requests made by the page after the DOM has finished loading.

The Playwright Firefox session is configured to automatically deny any requests for browser permissions such as requests for geolocation. This is necessary to ensure that dynamic loading of content is not blocked by a browser permission request that is never responded to by a user.

Automatic redirects are followed in the Playwright Firefox session.

All detection rules are executed against all requests made in the Playwright Firefox session and all iframes which are loaded in the Playwright Firefox session.

An unsuccessful detection can be caused by geoblocking, anti-bot detection and CAPTCHA challenges and blocking modal dialogs that brand websites may present requiring user interaction before the page loads. If a storefinder is not automatically detected, there could still be a storefinder in use that can be observed in a normal interactive web browser session using built-in browser debugging tools.

##### Detection Behaviours

The following behaviours are supported:

URL parameter extraction with PCRE named capture groups

HTTP header parameter extraction with PCRE named capture group

JavaScript lambda execution to return objects (after dynamic loading is complete)

HTML XPATH query to extract strings from DOM objects (after dynamic loading is complete)

JQ language query to extract objects from a JSON object (such as the body of a HTTP POST request)

Additionally, attribute typing with use of the __list suffix is supported; as well as matching but not extracting with use of the __ prefix.
