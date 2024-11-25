create table scan_queue
(
    id              int auto_increment     primary key,
    event_id        int                    not null,
    contribution_id int                    not null,
    revision_id     int                    not null,
    requested       datetime default now() not null,
    scan_start      datetime default null  null,
    scanned         datetime default null  null,
    failure_reason  VARCHAR(200)           null
);