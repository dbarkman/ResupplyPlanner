# **Elite: Dangerous Fleet Carrier Route Planner \- Project Overview**

This document outlines the technical approach for building a companion application for Elite: Dangerous, with a primary focus on long-range route planning for Fleet Carriers. The goal is to provide a highly accurate and efficient tool for the community, initially hosted on a Linode server for development and testing.

## **1\. Project Goal**

To develop a web-based companion application that enables Elite: Dangerous players to plan extensive, multi-jump routes for their Fleet Carriers. This tool aims to replicate and potentially enhance the capabilities of existing popular route planners by leveraging a local, up-to-date galaxy database.

## **2\. Data Source Strategy**

Maintaining an accurate and comprehensive galaxy map is central to this project. Our strategy involves a two-pronged approach, prioritizing the real-time data stream:

* **Ongoing Data Updates (EDDN Firehose \- Setup First):** We will first integrate with the Elite Dangerous Data Network (EDDN) by setting up a ZeroMQ (ZMQ) subscriber client. This will allow us to immediately begin listening to the tcp://eddn.edcd.io:9500/ stream, filtering for relevant Commodity and Journal schema messages that contain system coordinate updates or new system discoveries. This ensures our mechanism for keeping data current is robust before importing historical data.  
* **Initial Bulk Data Load (After EDDN Setup):** Once the EDDN processing and upserting mechanism is stable and proven, we will proceed with the bulk import. We will manually download the systems.json.gz data dump from Spansh (over 158 million star system records, approximately 26 GB uncompressed). This data will then be imported into our database in chunks, allowing EDDN to fill in any gaps or updates that occurred since the dump was generated.

## **3\. Database Choice: MySQL with Spatial Extensions**

Given the existing MySQL installation and its capabilities, we will utilize MySQL as our local database solution. MySQL 8.0+ offers robust built-in spatial data types and indexing, making it a suitable choice for handling the large volume of galactic coordinate data and performing efficient spatial queries.

### **Database Schema (Core systems table)**

The `systems` table is designed to efficiently store and query celestial bodies. The schema has been updated to include flags for routing-critical information like system permits and Tritium availability, and is compatible with MariaDB.

To satisfy the `NOT NULL` constraint for the `SPATIAL INDEX`, systems with initially unknown coordinates will be stored with a sentinel coordinate value of `POINT(999999.999, 999999.999, 999999.999)`. A separate process can later identify and update these systems. The `x`, `y`, and `z` columns default to `999999.999` to simplify `INSERT` operations for these systems.

```sql
CREATE TABLE systems (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    x DOUBLE DEFAULT 999999.999,
    y DOUBLE DEFAULT 999999.999,
    z DOUBLE DEFAULT 999999.999,
    coords POINT NOT NULL,
    requires_permit BOOLEAN NOT NULL DEFAULT FALSE,
    sells_tritium BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

-- Essential Spatial Index for fast proximity queries  
```sql
CREATE SPATIAL INDEX idx_systems_coords ON systems(coords);
```

-- Index on name for quick lookups from EDDN commodity messages
```sql
CREATE INDEX idx_systems_name ON systems (name);
```

### **Initial Data Import (Bulk Load Process)**

After the EDDN listener is successfully processing live updates, the 26 GB systems.json.gz dump will be manually downloaded. A temporary script will be developed to:

1. Decompress the systems.json.gz file using a gzip compatible library.  
2. Parse the JSON, extracting id, name, x, y, z, and primary\_star\_type.  
3. Convert the parsed data into a format suitable for MySQL's LOAD DATA INFILE command (e.g., CSV).  
4. Perform the import in chunks over several hours, leveraging LOAD DATA INFILE for its speed.  
5. **Crucially, spatial indexes should be created *after* the bulk data load is complete for optimal performance.**

Once this bulk import is finished, the continuously running EDDN listener will keep the database upserted with any new or changed information.

## **4\. Key Technical Challenges & Components**

### **a. Data Ingestion & Management**

* **EDDN Listener & Processor:** This is the first component to be developed. A ZeroMQ (ZMQ) subscriber client will connect to the EDDN tcp://eddn.edcd.io:9500/ stream. It will parse incoming JSON messages, filter for Commodity and Journal schemas containing system data, and perform upserts (update or insert) to keep the local systems table current.  
* **MySQL Setup & Optimization:** Configuring MySQL 8.0+ on the Linode server with appropriate memory (innodb\_buffer\_pool\_size), I/O, and indexing settings for a dataset of this scale.  
* **Spansh Dump Bulk Importer:** A temporary script to handle the one-time, chunked import of the systems.json.gz data dump into MySQL, as described above.

### **b. Route Planning Algorithm (A\* Search)**

* **Core Algorithm:** Implementation of the A\* pathfinding algorithm.  
  * **Nodes:** Star systems retrieved from the local MySQL database.  
  * **Edges:** Represent potential jumps between systems. An edge exists if the ST\_Distance between two system coords is less than or equal to the Fleet Carrier's maximum jump range (500 LY).  
  * **Heuristic:** Euclidean distance (straight-line distance) from the current system to the destination system.  
  * **Cost:** Tritium consumption per jump (proportional to jump distance).  
* **Fleet Carrier Specifics:** The algorithm must account for:  
  * A fixed **500 LY jump range** per jump.  
  * **No neutron star boosting** for Fleet Carriers (this simplifies the algorithm compared to ship plotting).  
  * Tritium fuel management (though for 10,000 LY, a full carrier typically has enough fuel).  
* **Iterative Querying:** The A\* algorithm will iteratively query the local MySQL database for systems within the 500 LY jump range of the current node, expanding its search until the destination is reached. This avoids loading the entire galaxy into memory.

### **c. Web Application Development**

* **Backend:** A web framework (e.g., Python/Flask/Django, Node.js/Express, etc.) to serve the web UI and expose API endpoints for route planning requests. This backend will interact with the local MySQL database.  
* **Frontend:** A web UI (HTML, CSS, JavaScript/React/Vue.js) to allow users to input start/end systems, view plotted routes, and interact with the application.  
  * Initial development can focus on a functional command-line interface for testing the core routing logic.

## **5\. Deployment Environment**

The project will initially be hosted on a Linode server. We will monitor resource usage (CPU, RAM, disk I/O) closely to inform future scaling decisions.  
This project combines large-scale data management, efficient spatial querying, and complex pathfinding to create a valuable tool for the Elite: Dangerous community.