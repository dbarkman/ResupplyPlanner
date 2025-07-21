-- Drop existing tables in reverse order of dependency to avoid foreign key errors
DROP TABLE IF EXISTS station_commodities;
DROP TABLE IF EXISTS stations;
DROP TABLE IF EXISTS commodities;
DROP TABLE IF EXISTS systems;

-- Create the systems table
-- This table stores all star systems and their coordinates.
CREATE TABLE systems (
    system_address BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    x DOUBLE PRECISION NOT NULL,
    y DOUBLE PRECISION NOT NULL,
    z DOUBLE PRECISION NOT NULL,
    coords GEOMETRY(PointZ, 0) NOT NULL,
    requires_permit BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for the systems table
CREATE INDEX idx_systems_name ON systems (name);
CREATE INDEX idx_systems_name_ilike ON systems (name text_pattern_ops);  -- For ILIKE autocomplete queries
CREATE INDEX idx_systems_coords ON systems USING GIST (coords);
-- Composite indexes for bounding box queries used by plan_route.py
CREATE INDEX idx_systems_x_y_z ON systems (x, y, z);
CREATE INDEX idx_systems_x_range ON systems (x) WHERE x IS NOT NULL;
CREATE INDEX idx_systems_y_range ON systems (y) WHERE y IS NOT NULL;
CREATE INDEX idx_systems_z_range ON systems (z) WHERE z IS NOT NULL;

-- Create the commodities table
-- This table stores all unique commodity types.
CREATE TABLE commodities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE INDEX idx_commodities_name ON commodities (name);

-- Create the stations table
-- This table stores all stations/markets.
CREATE TABLE stations (
    market_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    system_address BIGINT REFERENCES systems(system_address) ON DELETE SET NULL,
    prohibited TEXT[],
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stations_system_address ON stations (system_address);

-- Create the station_commodities table
-- This is a joining table that lists all commodities available at a specific station.
CREATE TABLE station_commodities (
    id BIGSERIAL PRIMARY KEY,
    station_market_id BIGINT NOT NULL REFERENCES stations(market_id) ON DELETE CASCADE,
    commodity_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    buy_price INTEGER NOT NULL,
    sell_price INTEGER NOT NULL,
    demand INTEGER NOT NULL,
    demand_bracket INTEGER NOT NULL,
    stock INTEGER NOT NULL,
    stock_bracket INTEGER NOT NULL,
    mean_price INTEGER NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT _station_commodity_uc UNIQUE (station_market_id, commodity_id)
);

CREATE INDEX idx_station_commodities_updated_at ON station_commodities (updated_at);
