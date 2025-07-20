#!/usr/bin/env python3

import argparse
import math
import heapq
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import sys
import os
from geoalchemy2.functions import ST_DWithin, ST_Distance

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.models import System, Base
from src.app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_system_by_name(session, name: str):
    """Fetches a system by name from the database."""
    # Exact match lookup - much faster than ILIKE
    return session.query(System).filter(System.name == name).first()


def calculate_distance(system1: System, system2: System) -> float:
    """Calculates the Euclidean distance in 3D space."""
    return math.sqrt((system1.x - system2.x)**2 + (system1.y - system2.y)**2 + (system1.z - system2.z)**2)


def calculate_distance_to_line(point, line_start, line_end):
    """
    Calculates the perpendicular distance from a point to a line segment.
    Returns the distance and the projection point on the line.
    """
    # Vector from line_start to line_end
    line_vec = (line_end.x - line_start.x, line_end.y - line_start.y, line_end.z - line_start.z)
    # Vector from line_start to point
    point_vec = (point.x - line_start.x, point.y - line_start.y, point.z - line_start.z)
    
    # Length of line segment squared
    line_len_sq = line_vec[0]**2 + line_vec[1]**2 + line_vec[2]**2
    
    if line_len_sq == 0:
        # Start and end are the same point
        return calculate_distance(point, line_start), line_start
    
    # Projection parameter t
    t = max(0, min(1, (point_vec[0] * line_vec[0] + point_vec[1] * line_vec[1] + point_vec[2] * line_vec[2]) / line_len_sq))
    
    # Projection point on the line
    projection = (
        line_start.x + t * line_vec[0],
        line_start.y + t * line_vec[1],
        line_start.z + t * line_vec[2]
    )
    
    # Distance from point to projection
    distance = math.sqrt((point.x - projection[0])**2 + (point.y - projection[1])**2 + (point.z - projection[2])**2)
    
    return distance, projection


def calculate_target_coordinates(start_system: System, end_system: System, target_distance: float):
    """
    Calculates the coordinates that are exactly target_distance LY from start_system
    along the straight line path toward end_system.
    """
    # Calculate the direction vector from start to end
    total_distance = calculate_distance(start_system, end_system)
    direction = (
        (end_system.x - start_system.x) / total_distance,
        (end_system.y - start_system.y) / total_distance,
        (end_system.z - start_system.z) / total_distance
    )
    
    # Calculate the target coordinates
    target_x = start_system.x + direction[0] * target_distance
    target_y = start_system.y + direction[1] * target_distance
    target_z = start_system.z + direction[2] * target_distance
    
    return target_x, target_y, target_z


def find_best_system_at_range(session, current_system: System, end_system: System, max_jump_range: float, previous_index: int = 0):
    """
    Finds the best system at approximately max_jump_range distance along the straight line path.
    Uses linear expanding bubble search (1, 2, 3, ...) starting from the exact target coordinates.
    Starts at the previous successful index minus one (not below 0), or at the first value >= 5 LY for the first hop.
    """
    import time
    logging.info(f"Finding best system at ~{max_jump_range} LY from {current_system.name} toward {end_system.name} (sequence: linear)")
    
    # Calculate the target coordinates at max_jump_range distance
    target_x, target_y, target_z = calculate_target_coordinates(current_system, end_system, max_jump_range)
    
    logging.info(f"Target coordinates: ({target_x:.2f}, {target_y:.2f}, {target_z:.2f})")
    
    # Linear sequence for bubble growth
    seq = list(range(1, int(max_jump_range) + 1))
    
    # Determine starting index
    if previous_index == -1:
        # Find the index of the first value >= 5
        start_index = next((i for i, f in enumerate(seq) if f >= 5), 0)
    else:
        start_index = max(previous_index - 1, 0)
    index = start_index
    logging.info(f"Starting bubble search at index {index+1} (radius {seq[index]} LY) using linear sequence")
    current_results_count = 0
    valid_candidates_count = 0
    
    while index < len(seq):
        bubble_radius = seq[index]
        # Calculate bubble bounds
        min_x = target_x - bubble_radius
        max_x = target_x + bubble_radius
        min_y = target_y - bubble_radius
        max_y = target_y + bubble_radius
        min_z = target_z - bubble_radius
        max_z = target_z + bubble_radius
        
        logging.info(f"Searching bubble with radius {bubble_radius:.1f} LY (step {index+1}) around target")
        start_query = time.time()
        candidates = session.query(System).filter(
            System.x.between(min_x, max_x),
            System.y.between(min_y, max_y),
            System.z.between(min_z, max_z)
        ).all()
        query_time = time.time() - start_query
        current_results_count = len(candidates)
        
        # Filter out the current system and systems beyond jump range
        valid_candidates = []
        for candidate in candidates:
            if candidate.system_address == current_system.system_address:
                continue
            distance = calculate_distance(current_system, candidate)
            if distance <= max_jump_range:
                valid_candidates.append((candidate, distance))
        valid_candidates_count = len(valid_candidates)
        logging.info(f"Bubble search returned {current_results_count} systems, {valid_candidates_count} valid in {query_time:.3f} seconds")
        
        if valid_candidates:
            # Found at least one valid candidate - stop searching and pick the best one
            best_candidate = None
            best_score = float('inf')
            
            for candidate, distance in valid_candidates:
                # Score based on how close to target distance (prefer systems closer to max_jump_range)
                score = abs(distance - max_jump_range)
                
                if score < best_score:
                    best_score = score
                    best_candidate = candidate
            
            logging.info(f"Found best candidate: {best_candidate.name} at {calculate_distance(current_system, best_candidate):.2f} LY")
            return best_candidate, bubble_radius, index, valid_candidates_count
        
        # No valid candidates found - move to next step
        index += 1
        if index < len(seq):
            logging.info(f"No valid candidates found, expanding bubble to next radius: {seq[index]:.1f} LY")
    
    logging.warning(f"No suitable system found within the user-specified jump range ({max_jump_range} LY) of target coordinates. Giving up.")
    return None, seq[-1], index, valid_candidates_count


def find_systems_within_jump_range_cylinder(session, current_system: System, end_system: System, max_jump_range: float, cylinder_radius: float = 1.0):
    """
    Finds systems within jump range using a cylinder-based search along the straight line path.
    This is much more efficient than searching the entire bounding box.
    """
    logging.info(f"Querying for neighbors within {max_jump_range} LY of {current_system.name} using cylinder search...")
    
    # Calculate the total distance to the destination
    total_distance = calculate_distance(current_system, end_system)
    
    # Create a cylinder along the straight line path
    # The cylinder extends from current_system toward end_system
    # We search within this cylinder for potential next hops
    
    # Calculate the direction vector from current to end
    direction = (
        (end_system.x - current_system.x) / total_distance,
        (end_system.y - current_system.y) / total_distance,
        (end_system.z - current_system.z) / total_distance
    )
    
    # Calculate the cylinder bounds
    # We want to search forward from current position, but also allow some backward movement
    search_forward = max_jump_range * 1.5  # Allow some forward movement
    search_backward = max_jump_range * 0.5  # Allow some backward movement
    
    # Calculate the cylinder endpoints
    cylinder_start = (
        current_system.x - direction[0] * search_backward,
        current_system.y - direction[1] * search_backward,
        current_system.z - direction[2] * search_backward
    )
    cylinder_end = (
        current_system.x + direction[0] * search_forward,
        current_system.y + direction[1] * search_forward,
        current_system.z + direction[2] * search_forward
    )
    
    # Create a bounding box around the cylinder for the initial database query
    min_x = min(cylinder_start[0], cylinder_end[0]) - cylinder_radius
    max_x = max(cylinder_start[0], cylinder_end[0]) + cylinder_radius
    min_y = min(cylinder_start[1], cylinder_end[1]) - cylinder_radius
    max_y = max(cylinder_start[1], cylinder_end[1]) + cylinder_radius
    min_z = min(cylinder_start[2], cylinder_end[2]) - cylinder_radius
    max_z = max(cylinder_start[2], cylinder_end[2]) + cylinder_radius
    
    # Query systems within the cylinder bounding box
    candidates = session.query(System).filter(
        System.x.between(min_x, max_x),
        System.y.between(min_y, max_y),
        System.z.between(min_z, max_z)
    ).all()
    
    logging.info(f"Cylinder bounding box query returned {len(candidates)} systems")
    
    # Filter by actual distance and cylinder constraints
    filtered_neighbors = []
    for candidate in candidates:
        if candidate.system_address == current_system.system_address:
            continue
            
        # Check if within jump range
        distance = calculate_distance(current_system, candidate)
        if distance > max_jump_range:
            continue
        
        # Check if within cylinder (perpendicular distance to line)
        perp_distance, projection = calculate_distance_to_line(candidate, current_system, end_system)
        if perp_distance > cylinder_radius:
            continue
        
        # Check if projection is within the cylinder bounds (forward progress)
        proj_distance = calculate_distance(current_system, System(x=projection[0], y=projection[1], z=projection[2]))
        if proj_distance > search_forward:
            continue
        
        filtered_neighbors.append(candidate)
    
    logging.info(f"After cylinder filtering, found {len(filtered_neighbors)} neighbors")
    
    # If we don't have enough good candidates, expand the cylinder
    if len(filtered_neighbors) < 5:
        logging.info(f"Only {len(filtered_neighbors)} neighbors found, expanding cylinder radius to {cylinder_radius * 2}")
        return find_systems_within_jump_range_cylinder(session, current_system, end_system, max_jump_range, cylinder_radius * 2)
    
    return filtered_neighbors


def find_systems_within_jump_range(session, current_system: System, max_jump_range: float):
    """
    Finds all systems within a given jump range from the current system
    using coordinate-based queries for better performance.
    """
    logging.info(f"Querying for neighbors within {max_jump_range} LY of {current_system.name}...")
    
    # Use a bounding box query first, then filter by actual distance
    # This is much faster than spatial functions for our use case
    neighbors = session.query(System).filter(
        System.x.between(current_system.x - max_jump_range, current_system.x + max_jump_range),
        System.y.between(current_system.y - max_jump_range, current_system.y + max_jump_range),
        System.z.between(current_system.z - max_jump_range, current_system.z + max_jump_range)
    ).all()
    
    logging.info(f"Bounding box query returned {len(neighbors)} systems")
    
    # Filter by actual distance and exclude the current system
    filtered_neighbors = []
    for neighbor in neighbors:
        if neighbor.system_address != current_system.system_address:
            distance = calculate_distance(current_system, neighbor)
            if distance <= max_jump_range:
                filtered_neighbors.append(neighbor)
    
    logging.info(f"After distance filtering, found {len(filtered_neighbors)} neighbors")
    
    return filtered_neighbors


def plan_route(session, start_system: System, end_system: System, max_jump_range: float):
    """
    Plans a route from a start to an end system using a simple, pragmatic approach.
    """
    import time
    
    logging.info(f"Planning route from {start_system.name} to {end_system.name} with a max jump of {max_jump_range} LY. Bubble sequence: linear")

    # First, check if it's a direct jump
    direct_distance = calculate_distance(start_system, end_system)
    logging.info(f"Direct distance: {direct_distance:.2f} LY")
    
    if direct_distance <= max_jump_range:
        logging.info("Direct jump possible!")
        return [start_system, end_system]
    
    logging.info(f"Direct jump not possible. Finding multi-hop route...")
    
    # Multi-hop routing using a simple greedy approach
    route = [start_system]
    current_system = start_system
    visited_systems = {start_system.system_address}
    previous_index = -1  # -1 signals first hop
    
    max_hops = 100  # Increased from 50 to handle longer routes
    hop_count = 0
    
    while hop_count < max_hops:
        hop_count += 1
        logging.info(f"Hop {hop_count}: Looking for next system from {current_system.name}")
        
        # Check if we're close enough to try a direct jump to destination
        current_distance_to_end = calculate_distance(current_system, end_system)
        if current_distance_to_end <= max_jump_range:
            logging.info(f"Found route! Can reach {end_system.name} directly from {current_system.name}")
            route.append(end_system)
            return route
        
        # Always use the previous index minus one (or start at 5 LY for first hop)
        best_neighbor, bubble_size_used, index_used, valid_candidates_count = find_best_system_at_range(
            session, current_system, end_system, max_jump_range, previous_index
        )
        if not best_neighbor:
            logging.warning(f"No reachable systems from {current_system.name}")
            return None
        # Check if we've already visited this system (shouldn't happen with targeted search, but safety check)
        if best_neighbor.system_address in visited_systems:
            logging.warning(f"Best neighbor {best_neighbor.name} already visited, no route found")
            return None
        # Add the best neighbor to our route and continue
        route.append(best_neighbor)
        visited_systems.add(best_neighbor.system_address)
        current_system = best_neighbor
        previous_index = index_used
        distance_to_end = calculate_distance(best_neighbor, end_system)
        logging.info(f"Added {best_neighbor.name} to route (distance to end: {distance_to_end:.2f} LY)")
    
    logging.warning(f"Route not found within {max_hops} hops")
    return None


def reconstruct_path(came_from, start, end, session):
    """Reconstructs the path from the came_from map."""
    current_address = end.system_address
    path = []
    while current_address is not None:
        path.append(current_address)
        current_address = came_from.get(current_address)
    path.reverse()
    
    # Convert addresses back to System objects for the final output
    systems_in_path = session.query(System).filter(System.system_address.in_(path)).all()
    # Create a mapping from address to system object for correct ordering
    system_map = {s.system_address: s for s in systems_in_path}
    return [system_map[address] for address in path]


def print_route(route):
    """Prints the final route in a user-friendly format."""
    print("\n--- Route Plan ---")
    total_jumps = len(route) - 1
    total_distance = 0
    
    for i in range(len(route) - 1):
        start = route[i]
        end = route[i+1]
        dist = calculate_distance(start, end)
        total_distance += dist
        print(f"Jump {i+1:2d}: {start.name:<20} -> {end.name:<20} ({dist:>6.2f} LY)")
        
    print("------------------")
    print(f"Total Jumps: {total_jumps}")
    print(f"Total Distance: {total_distance:.2f} LY\n")


def main():
    parser = argparse.ArgumentParser(description="Plan a route between two star systems.")
    parser.add_argument("start_system", type=str, help="The name of the starting system.")
    parser.add_argument("end_system", type=str, help="The name of the destination system.")
    parser.add_argument("--max-jump-range", type=float, required=True, help="The maximum jump range of the ship in light years.")
    args = parser.parse_args()

    with get_db() as db_session:
        try:
            start_system = get_system_by_name(db_session, args.start_system)
            if not start_system:
                logging.error(f"Start system '{args.start_system}' not found.")
                return
            end_system = get_system_by_name(db_session, args.end_system)
            if not end_system:
                logging.error(f"End system '{args.end_system}' not found.")
                return
            route = plan_route(db_session, start_system, end_system, args.max_jump_range)
            if route:
                print_route(route)
            else:
                print("No route found.")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main() 