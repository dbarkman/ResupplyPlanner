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
    
    logging.info(f"Planning route from {start_system.name} to {end_system.name} with a max jump of {max_jump_range} LY.")

    # First, check if it's a direct jump
    direct_distance = calculate_distance(start_system, end_system)
    logging.info(f"Direct distance: {direct_distance:.2f} LY")
    
    if direct_distance <= max_jump_range:
        logging.info("Direct jump possible!")
        return [start_system, end_system]
    
    logging.info(f"Direct jump not possible. Need to find intermediate systems.")
    
    # For now, let's just return None and add a TODO
    # TODO: Implement multi-hop routing
    logging.warning("Multi-hop routing not yet implemented.")
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

    # Use a 'with' statement to correctly manage the database session
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