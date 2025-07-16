-- This script adds database-managed created_at and updated_at timestamps
-- to the main tables for better auditing.

-- 1. Create a reusable function that will be triggered on any update to a table.
--    This function automatically sets the 'row_updated_at' column to the current time.
CREATE OR REPLACE FUNCTION update_row_modified_function()
RETURNS TRIGGER AS $$
BEGIN
    NEW.row_updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 2. Add the new audit columns to the 'systems' table and attach the trigger.
ALTER TABLE systems ADD COLUMN row_created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE systems ADD COLUMN row_updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
CREATE TRIGGER update_systems_row_modified
BEFORE UPDATE ON systems
FOR EACH ROW
EXECUTE PROCEDURE update_row_modified_function();

-- 3. Add the new audit columns to the 'stations' table and attach the trigger.
ALTER TABLE stations ADD COLUMN row_created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE stations ADD COLUMN row_updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
CREATE TRIGGER update_stations_row_modified
BEFORE UPDATE ON stations
FOR EACH ROW
EXECUTE PROCEDURE update_row_modified_function();

-- 4. Add the new audit columns to the 'commodities' table and attach the trigger.
ALTER TABLE commodities ADD COLUMN row_created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE commodities ADD COLUMN row_updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
CREATE TRIGGER update_commodities_row_modified
BEFORE UPDATE ON commodities
FOR EACH ROW
EXECUTE PROCEDURE update_row_modified_function();

-- 5. Add the new audit columns to the 'station_commodities' table and attach the trigger.
--    I've included this table as well as it's a core, frequently updated table.
ALTER TABLE station_commodities ADD COLUMN row_created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE station_commodities ADD COLUMN row_updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
CREATE TRIGGER update_station_commodities_row_modified
BEFORE UPDATE ON station_commodities
FOR EACH ROW
EXECUTE PROCEDURE update_row_modified_function(); 