set search_path =  espa_unit_test;

INSERT INTO ordering_configuration (key, value) VALUES

-- api.external.hadoop & api.external.onlinecache
    ('landsatds.host', 'dummy_host'),
    ('landsatds.password', 'dummy_password'),
    ('landsatds.port', '22'),
    ('landsatds.username', 'dummy_username'),

-- api.external.lta
    ('url.dev.orderservice', 'http://host.com'),
    ('url.dev.orderupdate', 'http://host.com'),
    ('url.dev.orderdelivery', 'http://host.com'),
    ('url.dev.registration', 'http://host.com'),
    ('url.dev.earthexplorer', 'https://somehost'),
    ('url.dev.internal_cache', 'localhost,localhost'),
    ('url.dev.external_cache', 'localhost'),
    ('url.dev.landsat.external', 'localhost,localhost'),
    ('url.dev.landsat.datapool', 'localhost'),

    ('soap.cache_location', '/tmp/suds'),
    ('soap.client_timeout', '1800'),

-- api.external.m2m
    ('url.dev.earthexplorer.json', 'http://host.com/inventory/json/'),
    ('bulk.dev.json.version', '0.0.0'),
    ('bulk.dev.json.username', 'dummy_username'),
    ('bulk.dev.json.password', 'dummy_password'),

    ('system.m2m_url_enabled', 'False'),
    ('system.m2m_val_enabled', 'False'),

-- api.external.ers
    ('url.dev.ersapi', 'http://host.com'),

-- api.external.lpdaac
    ('url.dev.modis.datapool', 'localhost'),
    ('url.dev.modis.external', 'localhost,localhost'),
    ('path.aqua_base_source', '/MOLA'),
    ('path.terra_base_source', '/MOLT'),

-- api.external.onlinecache
    ('online_cache_orders_dir', '/path/2/output'),

    ('ladsftp.password', 'dummy_password'),
    ('ladsftp.username', 'dummy_username'),

-- api.notification.email
    ('url.dev.status_url', 'http://localhost:5000/ordering/status'),

    ('email.corrupt_gzip_notification_list', 'username@emailhost,username@emailhost'),
    ('email.espa_address', 'system@mail_address'),
    ('email.espa_server', 'mail_host'),
    ('email.purge_report_list', 'username@emailhost'),

-- api.providers.administration
    ('system_message_title', 'text'),
    ('system_message_body', 'text'),
    ('display_system_message', 'True'),

    ('msg.system_message_body', ''),
    ('msg.system_message_title', ''),
    ('msg.system_message_updated_by', ''),
    ('msg.system_message_updated_date', ''),

    ('system.display_system_message', 'True'),
    ('system.load_ee_orders_enabled', 'True'),
    ('system.run_order_purge_every', '86400'),

-- api.providers.production
    ('policy.purge_orders_after', '10'),
    ('system.ondemand_enabled', 'False'),
    ('system.order_disposition_enabled', 'True'),

    ('cache.key.handle_orders_lock_timeout', '1260'),
    ('cache.ttl', '604800'),

    ('lock.timeout.handle_orders', '1260'),

-- api.system.errors
    ('retry.db_lock_timeout.retries', '10'),
    ('retry.db_lock_timeout.timeout', '300'),
    ('retry.ftp_errors.retries', '10'),
    ('retry.ftp_errors.timeout', '900'),
    ('retry.gzip_errors.retries', '10'),
    ('retry.gzip_errors.timeout', '21600'),
    ('retry.http_errors.retries', '10'),
    ('retry.http_errors.timeout', '900'),
    ('retry.lta_soap_errors.retries', '12'),
    ('retry.lta_soap_errors.timeout', '3600'),
    ('retry.missing_aux_data.retries', '5'),
    ('retry.missing_aux_data.timeout', '86400'),
    ('retry.network_errors.retries', '5'),
    ('retry.network_errors.timeout', '120'),
    ('retry.retry_missing_l1.retries', '8'),
    ('retry.retry_missing_l1.timeout', '3600'),
    ('retry.sixs_errors.retries', '3'),
    ('retry.sixs_errors.timeout', '60'),
    ('retry.ssh_errors.retries', '3'),
    ('retry.ssh_errors.timeout', '300'),
    ('retry.node_space_errors.retries', '3'),
    ('retry.node_space_errors.timeout', '600'),
    ('retry.segfault_errors.retries', '5'),
    ('retry.segfault_errors.timeout', '3600'),
    ('retry.missed_extraction.retries', '3'),
    ('retry.missed_extraction.timeout', '300')

;
