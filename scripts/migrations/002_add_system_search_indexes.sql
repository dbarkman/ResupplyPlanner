-- Migration: Add system search indexes for autocomplete and coordinate queries
-- This migration adds indexes to improve performance for:
-- 1. System name autocomplete (ILIKE queries)
-- 2. Coordinate-based bounding box queries used by plan_route.py

-- Add index for ILIKE autocomplete queries on system names
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_systems_name_ilike ON systems (name text_pattern_ops);

-- Add composite index for coordinate-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_systems_x_y_z ON systems (x, y, z);

-- Add individual coordinate indexes for range queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_systems_x_range ON systems (x) WHERE x IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_systems_y_range ON systems (y) WHERE y IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_systems_z_range ON systems (z) WHERE z IS NOT NULL;

-- Add comment to document the purpose of these indexes
COMMENT ON INDEX idx_systems_name_ilike IS 'Index for system name autocomplete queries using ILIKE';
COMMENT ON INDEX idx_systems_x_y_z IS 'Composite index for coordinate-based bounding box queries';
COMMENT ON INDEX idx_systems_x_range IS 'Index for x-coordinate range queries';
COMMENT ON INDEX idx_systems_y_range IS 'Index for y-coordinate range queries';
COMMENT ON INDEX idx_systems_z_range IS 'Index for z-coordinate range queries'; 