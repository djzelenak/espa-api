
# espa-api [![build status][0]][1] [![Codecov branch][12]][13]

This is an API for interacting with the ESPA ordering system. 

## User API
The User API is public facing and available for anyone to code and interact with.  
Version 1 provides the minimum functionality necessary to determine available 
products from a list of inputs, place orders, and view order status. There are 
endpoints for providing available projections, resampling methods, and output formats.

All user interactions with API functions must be accompanied by valid credentials. 
Accounts are managed in the [USGS EROS Registration system][10].

The api host is `https://espa.cr.usgs.gov/api`. 

### Related Pages
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


### Quick Unix Walk-through

The ESPA ordering system provides an API for users to interact with using
simple HTTP communications through the programming language of their choice.

1. To find what products ESPA can produce for a given Landsat 
acquisition: [/available-products](docs/API-RESOURCES-LIST.md#apiProdsPost)
1. If the acquisition can be processed into a desired product, create a 
processing order request: [/order](docs/API-RESOURCES-LIST.md#apiSubmitOrder)
1. When processing has completed, get the download URL while the output is 
still available: [/item-status](docs/API-RESOURCES-LIST.md#apiItemStats)

For a more detailed list of User API operations, see the [Available Resources List][6]. 

For a language-specific (python) example, please see [an API Demo][11]. 

#### Support Information

This project is unsupported software provided by the U.S. Geological Survey (USGS) Earth Resources Observation and Science (EROS) Land Satellite Data Systems (LSDS) Project. For questions regarding products produced by this source code, please contact the [Landsat Contact Us][2] page and specify USGS Level-2 in the "Regarding" section.

#### Disclaimer

This software is preliminary or provisional and is subject to revision. It is being provided to meet the need for timely best science. The software has not received final approval by the U.S. Geological Survey (USGS). No warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. The software is provided on the condition that neither the USGS nor the U.S. Government shall be held liable for any damages resulting from the authorized or unauthorized use of the software.


[0]: https://img.shields.io/travis/USGS-EROS/espa-api/master.svg?style=flat-square
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
[12]: https://img.shields.io/codecov/c/github/USGS-EROS/espa-api/master.svg?style=flat-square
[13]: https://codecov.io/gh/USGS-EROS/espa-api

