
# espa-api [![build status][0]][1] [![Codecov branch][12]][13]

This is an API for interacting with the ESPA ordering system. 

For questions regarding this source code, or the ESPA project, please use the
[Landsat Contact Us][2] page and specify USGS ESPA in the "Subject" section.

## Related Pages
* [Description of Products Available][3]
* [Abbreviations & Definitions][4]
* [ESPA Customizations][5]
* **[Available Resources List][6]**

<details>
<summary>Need a scene list?</summary>
The USGS EROS offers two resources for finding valid scene acquisitions:

1. [USGS/EROS Inventory Service API][7]
1. [Entire Collection of Metadata][8]
</details>

## User API
The User API is public facing and available for anyone to code and interact with.  
Version 1 provides the minimum functionality necessary to determine available 
products from a list of inputs, place orders, and view order status. There are 
endpoints for providing available projections, resampling methods, and output formats.

Now that the User API has reached a stable version 1.0, it will always be 
backwards compatible using a _never remove, only add_ strategy. If there will 
ever be a need to break compatibility, it will be announced in the [Changelog][9].

All user interactions with API functions must be accompanied by valid credentials. 
Accounts are managed in the [USGS EROS Registration system][10].

The api host is `https://espa.cr.usgs.gov/api`. 

### Quick Unix Walk-through

The ESPA ordering system provides an API for users to interact with using
simple HTTP communications through the programming language of their choice.

For example, to find what products ESPA can produce for a given Landsat 
acquisition: 
```bash
curl  --user <erosusername>:<erospassword> \
    https://espa.cr.usgs.gov/api/v0/available-products/LC08_L1TP_029030_20161008_20170220_01_T1
```
```json
// Response: 
{
    "olitirs8_collection": {
        "inputs": [
            "LC08_L1TP_029030_20161008_20170220_01_T1"
        ], 
        "products": [
            "source_metadata", "l1", "toa", "bt", 
            "sr", "sr_ndvi", "sr_evi", "sr_savi", "sr_msavi", "sr_ndmi", "sr_nbr", "sr_nbr2", 
            "stats"
        ]
    }
}

```

Then, if the acquisition can be processed into a desired product, create a 
processing order request, including at minimum the output formatting:
```bash
curl  --user <erosusername>:<erospassword> \
    -d '{
          "note": "this is going to be sweet...",
          "format": "gtiff",
          "olitirs8_collection": {
                "inputs": ["LC08_L1TP_029030_20161008_20170220_01_T1"], 
                "products": ["sr_ndvi"]
            }
        }' https://espa.cr.usgs.gov/api/v0/order 
```
```json
// Response: 
{
  "orderid": "espa-production@email.com-05222017-185100-725",
  "status": "ordered"
}
```

Finally, use this order-ID to determine when the scene has completed processing, 
and get the download URL while the output is still on disk:
```bash
curl --user <erosusername>:<erospassword> \
    https://espa.cr.usgs.gov/api/v0/item-status/espa-production@email.com-05222017-185100-725
```
```json
// Response: 
{
  "espa-production@email.com-05222017-185100-725": [
    {
      "cksum_download_url": "https://.../orders/.../LC080290302016100801T1-SC20170329224231.md5",
      "completion_date": "1997-01-01T23:59:59.908435",
      "name": "LC08_L1TP_029030_20161008_20170220_01_T1",
      "note": "",
      "product_dload_url": "https://.../orders/.../LC080290302016100801T1-SC20170329224231.tar.gz",
      "status": "complete"
    }
  ]
}
```

For a more detailed list of User API operations, see the [Available Resources List][6]. 

For a language-specific (python) example, please see [an API Demo][11]. 


[0]: https://img.shields.io/travis/USGS-EROS/espa-api/ee_json_api.svg?style=flat-square
[1]: https://travis-ci.org/USGS-EROS/espa-api
[2]: https://landsat.usgs.gov/contact
[3]: docs/AVAILABLE-PRODUCTS.md
[4]: docs/TERMS.md
[5]: docs/CUSTOMIZATION.md
[6]: docs/API-RESOURCES-LIST.md
[7]: https://earthexplorer.usgs.gov/inventory/documentation
[8]: https://landsat.usgs.gov/download-entire-collection-metadata
[9]: CHANGELOG.md
[10]: https://ers.cr.usgs.gov/register/
[11]: examples/api_demo.ipynb
[12]: https://img.shields.io/codecov/c/github/USGS-EROS/espa-api/ee_json_api.svg?style=flat-square
[13]: https://codecov.io/gh/USGS-EROS/espa-api

