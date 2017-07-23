set search_path = espa_unit_test;

INSERT INTO ordering_configuration (key, value) VALUES

-- api.external.lta
    ('url.dev.orderservice', 'http://host.com'),
    ('url.dev.orderupdate', 'http://host.com'),
    ('url.dev.orderdelivery', 'http://host.com'),
    ('url.dev.registration', 'http://host.com'),
    ('url.dev.earthexplorer', 'http://host.com'),
    ('url.dev.internal_cache', 'hostname'),
    ('url.dev.external_cache', 'hostname'),

-- api.external.ers
    ('url.dev.ersapi', 'http://host.com'),

-- api.external.lpdaac
    ('url.dev.modis.datapool', 'hostname:port'),

-- api.external.onlinecache
    ('online_cache_orders_dir', '/path/2/output'),
    ('landsatds.host', 'hostname'),
    ('landsatds.username', 'username'),
    ('landsatds.password', 'password'),

-- api.notification.email
    ('url.dev.status_url', 'http://host.com'),

-- api.providers.administration.administration_provider.
    ('system_message_title', 'text'),
    ('system_message_body', 'text'),
    ('display_system_message', 'False')

;
