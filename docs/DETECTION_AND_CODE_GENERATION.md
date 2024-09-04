### Detection

#### Inspection of site

Alltheplaces provides rudimentary tooling to inspect a site for common behaviours.

* [Sitemap inspection](SITEMAP.md) - `pipenv run scrapy sitemap http://example.com/` to detect potential individual store URLs.
* [Structured Data inspection](STRUCTURED_DATA.md) - `pipenv run scrapy sitemap http://example.com/` to detect potential individual store URLs.
* Links - `pipenv run scrapy links http://example.com/` to look for links with human language labels, such as "Find our stores".

When checking a large number of URLs, these tools can be chained together to highlight potential candidates for spidering.

#### Automatic detection from storefinder page

Alltheplaces has a number of key storefinders which gather together common functionality.

Going one step further, many of these store finders build in the capabilities to automatically detect the 
presence of a common storefinder from either:

- Request patterns made to API endpoints or
- Responses that contain xpath or JS Objects indicating the presence of a store locator.

To automatically attempt to detect a storefinder, pass in a start URL - either the top level domain, or
the specific store page.
Hint: You may wish to use the `pipenv run scrapy links http://example.com/` command to automatically look for
probably storefinder pages if you are reviewing a number of top level domains.

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

This tool will attempt to generate a useful class name, spider key name, and 
all other attributes to get you started; however you should still run and adjust the generated code
before opening a pull request.

If known, you can specify extra arguments such as `--brand-wikidata`.

For full usage, run `pipenv run scrapy sf`

### Manual Generation

Where a storefinder isn't detected but you still wish to get a jump start on writing a spider to a common pattern,
use the `pipenv run scrapy genspider` command to generate a common template.