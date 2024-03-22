USE bot;

CREATE TABLE IF NOT EXISTS resources(
    id varchar(255),
    dt varchar(255),
    name varchar(255),
    data json
);