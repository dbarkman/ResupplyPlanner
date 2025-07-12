-- Drop table if it already exists (useful for fresh setup)
DROP TABLE IF EXISTS systems CASCADE;

-- Create the systems table
CREATE TABLE systems (
    system_address BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    x DOUBLE PRECISION NOT NULL, -- Use DOUBLE PRECISION for floating point numbers
    y DOUBLE PRECISION NOT NULL,
    z DOUBLE PRECISION NOT NULL,
    -- GEOMETRY(PointZ, 0) for 3D points (X, Y, Z) in a Cartesian system (SRID 0)
    coords GEOMETRY(PointZ, 0) NOT NULL,
    requires_permit BOOLEAN NOT NULL DEFAULT FALSE,
    sells_tritium BOOLEAN NOT NULL DEFAULT FALSE,
    -- TIMESTAMP WITH TIME ZONE is recommended for PostgreSQL
    -- DEFAULT NOW() sets the creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create a function to update the 'updated_at' timestamp on row update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger that calls the function before each update on the 'systems' table
CREATE TRIGGER update_systems_updated_at
BEFORE UPDATE ON systems
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for performance
-- The spatial index is automatically handled by GeoAlchemy2 when you create tables
-- via Base.metadata.create_all(), but you can create it manually here if needed.
-- However, it's better to let GeoAlchemy2 manage it for consistency with your ORM.
-- If you were to create it manually, it would look like this:
-- CREATE INDEX idx_systems_coords ON systems USING GIST (coords);

-- Create a regular index on 'name' for quick lookups
CREATE INDEX idx_systems_name ON systems (name);

-- Create indexes on x, y, z for bounding box filtering if you decide to use it
-- instead of pure spatial queries for some operations, or for debugging.
CREATE INDEX idx_systems_x ON systems (x);
CREATE INDEX idx_systems_y ON systems (y);
CREATE INDEX idx_systems_z ON systems (z);
