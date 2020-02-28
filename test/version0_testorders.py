
import api.domain.sensor as sn

good_test_projections = {'aea': {'standard_parallel_1': 29.5,
                                 'standard_parallel_2': 45.5,
                                 'central_meridian': -96,
                                 'latitude_of_origin': 23,
                                 'false_easting': 0,
                                 'false_northing': 0,
                                 'datum': 'nad83'},
                         'utm': {'zone': 33,
                                 'zone_ns': 'south'},
                         'lonlat': None,
                         'sinu': {'central_meridian': 0,
                                  'false_easting': 0,
                                  'false_northing': 0},
                         'ps': {'longitudinal_pole': 0,
                                'latitude_true_scale': 75,
                                'false_easting': 0,
                                'false_northing': 0}}


def build_base_order():
    """
    Builds the following dictionary (with the products filled out from sensor.py):

    base = {'MOD09A1': {'inputs': 'MOD09A1.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MOD09GA': {'inputs': 'MOD09GA.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MOD09GQ': {'inputs': 'MOD09GQ.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MOD09Q1': {'inputs': 'MOD09Q1.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MYD09A1': {'inputs': 'MYD09A1.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MYD09GA': {'inputs': 'MYD09GA.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MYD09GQ': {'inputs': 'MYD09GQ.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MYD09Q1': {'inputs': 'MYD09Q1.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MOD13A1': {'inputs': 'MOD13A1.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MOD13A2': {'inputs': 'MOD13A2.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MOD13A3': {'inputs': 'MOD13A3.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MOD13Q1': {'inputs': 'MOD13Q1.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MYD13A1': {'inputs': 'MYD13A1.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MYD13A2': {'inputs': 'MYD13A2.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MYD13A3': {'inputs': 'MYD13A3.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'MYD13Q1': {'inputs': 'MYD13Q1.A2000072.h02v09.005.2008237032813',
                        'products': ['l1']},
            'vnp09ga': {'inputs': ['VNP09GA.A2014245.h10v04.001.2017043103958',
                                    'VNP09GA.A2014245.h10v04.001.2015012103931'],
                        'products': ['l1']},
            'tm4': {'inputs': 'LT42181092013069PFS00',
                    'products': ['l1']},
            'tm5': {'inputs': 'LT52181092013069PFS00',
                    'products': ['l1']},
            'etm7': {'inputs': 'LE72181092013069PFS00',
                     'products': ['l1']},
            'oli8': {'inputs': 'LO82181092013069PFS00',
                     'products': ['l1']},
            'olitirs8': {'inputs': 'LC82181092013069PFS00',
                         'products': ['l1']},

            'sentinel': {'inputs': ['L1C_T14TPP_A022031_20190910T172721',
                                   'S2A_OPER_MSI_L1C_TL_SGS__20160130T184417_20160130T203840_A003170_T13VCC_N02_01_01'],
                         'products': ['s2_sr', 's2_ndvi', 's2_msavi', 's2_evi', 's2_savi',
                                      's2_nbr', 's2_nbr2', 's2_ndmi']

            'projection': {'lonlat': None},
            'image_extents': {'north': 0.0002695,
                              'south': 0,
                              'east': 0.0002695,
                              'west': 0,
                              'units': 'dd'},
            'format': 'gtiff',
            'resampling_method': 'cc',
            'resize': {'pixel_size': 0.0002695,
                       'pixel_size_units': 'dd'},
            'plot_statistics': True}"""

    base = {'projection': {'lonlat': None},
            'image_extents': {'north': 0.002695,
                              'south': 0,
                              'east': 0.002695,
                              'west': 0,
                              'units': 'dd'},
            'format': 'gtiff',
            'resampling_method': 'cc',
            'resize': {'pixel_size': 0.0002695,
                       'pixel_size_units': 'dd'},
            'plot_statistics': True}

    # This will give the base order 15 scenes
    sensor_acqids = {'.A2000072.h02v09.005.2008237032813': (['MOD09A1', 'MOD09Q1', 'MYD13A1', 'MYD13Q1'],
                                                            ['mod09a1', 'mod09q1', 'myd13a1', 'myd13q1']),
                     '.A2016305.h11v04.006.2016314200836': (['MOD09GA', 'MOD09GQ', 'MYD13A2', 'MYD13A3'],
                                                            ['mod09ga', 'mod09gq', 'myd13a2', 'myd13a3']),
                     '.A2000361.h24v03.006.2015111114747': (['MOD11A1', 'MYD11A1'],
                                                            ['mod11a1', 'myd11a1']),
                     # TODO: REMOVE _collection from IDs
                     'L1TP_044030_19851028_20161004_01_T1': (['LT04_', 'LT05_', 'LE07_', 'LO08_', 'LC08_'],
                                                             ['tm4_collection', 'tm5_collection', 'etm7_collection',
                                                              'oli8_collection', 'olitirs8_collection'])}

    for acq in sensor_acqids:
        for prefix, label in zip(sensor_acqids[acq][0], sensor_acqids[acq][1]):
            # We need to avoid any requests for modis_ndvi - this will raise an error since we have
            # non-NDVI available MODIS products in the base order.  Testing of modis_ndvi
            # and viirs_ndvi orders is conducted separately in test_api.py
            if label.startswith('mod') or label.startswith('myd'):
                base[label] = {'inputs': ['{}{}'.format(prefix, acq)],
                               'products': ['l1']}
            else:
                base[label] = {'inputs': ['{}{}'.format(prefix, acq)],
                               # don't include aq_refl in our test base order since it has sensor restrictions
                               # these restrictions should be tested separately
                               'products': [p for p in sn.instance('{}{}'.format(prefix, acq)).products
                                            if p != 'aq_refl']}

    # We need to have at least 2 scenes for viirs-related tests to work
    base['vnp09ga'] = {'inputs': ['VNP09GA.A2014245.h10v04.001.2017043103958',
                                  'VNP09GA.A2014245.h10v04.001.2015012103931'],
                       'products': ['l1']}

    # add sentinel-2 scene IDs to the order
    base['sentinel'] = {'inputs': ['L1C_T14TPP_A022031_20190910T172721',
                                   'S2A_OPER_MSI_L1C_TL_SGS__20160130T184417_20160130T203840_A003170_T13VCC_N02_01_01'],
                        'products': ['s2_sr', 's2_ndvi', 's2_msavi', 's2_savi', 's2_evi', 's2_ndmi',
                                     's2_nbr', 's2_nbr2']}

    return base
