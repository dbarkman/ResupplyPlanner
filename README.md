# ResupplyPlanner
A one-stop tool for hauling Tritium around the galaxy

## Expected features

### User Input
Travel:
- departure system
- delivery system(s)
- final arrival system at the end of the resupply mission
- top-off stops
- other stops
    - specific systems
    - near specific systems (closest jump point to Sag A)
- ability to add mining resupply system and amount (will impact future fuel supplies and jump requirements)
- IRL day and time of departure, local and UTC
- hours available per day
- exploration/mining/non-travel days planned

Carrier and Ship details:
- carrier modules for each carrier
    - whether to decom any carriers or not
- ship(s) traveling with carrier(s)
    - available cargo sizes
    - what legs any ships will participate in (staying behind to mine at relay, going ahead for final delivery)
- miner(s) traveling with the carrier(s)
    - expected tritium mined per hour

Known Costs:
- expected cost for Tritium (will default to galactic average on day of first purchase)
- ability to add Tritium top off costs
- ability to add other, miscellaneous costs

Desired Profits:
- profit desired in credits (adjust this to find an agreeable price with depot owner)

### Program Output

Financials:
- sell price to offer
- amount saved by mining vs purchasing (will use average purchase price entered for entire trip)
- total cost for Tritium, for selling and travel
- total cost for Carrier(s) mainenance jumps
- total cost for Carrier(s) upkeep, for days away from originating system
- total costs
- gross profit
- net profit

Travel:
- total trip jumps, including any relay round trips
- optimal relay stops (two carriers travel together, one stops, refuels other, one ship delivers and returns)
- approximate hours/days of travel

Mining:
- amount needed to mine
- approximate hours to mine (will default 200t/hour (seems to be what most CMDRs report)

Schedule:
- IRL schedule
    - set hours available for each day of schedule

Downloads and Miscellaneous:
- downloadable CSV route sheets
    - for entire trip or any leg
    - compatible with FCOC routes
- relay fuel transfer instructions
- reminder to top off depot and transfer from market after each jump

### Decisions
- web app, better when needing to ready APIs (current favorite)
- desktop client, better when needing to ready CMDR logs locally

### Todo
- Get list of permit locked systems: https://forums.frontier.co.uk/threads/updated-permit-list.122593/
    - Can mark systems as permit locked if the user's permits can't be determined
- Get user's list of permits for correct route plotting
    - Or allow users to choose the systems they have permits for

## Setup

This project uses Python and a MariaDB/MySQL database. The following steps will guide you through setting up the application environment.

### 1. Initial Setup & Virtual Environment

First, clone the repository to your local machine. It is highly recommended to use a Python virtual environment to manage project dependencies and avoid conflicts with system-wide packages.

```bash
# Navigate to your project directory
cd /path/to/ResupplyPlanner

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\\Scripts\\activate

# Now your shell prompt should be prefixed with (venv)
```

### 2. Install Dependencies

With the virtual environment activated, install the required Python packages using pip.

```bash
# Install all dependencies from the requirements file
pip install -r requirements.txt
```

### 3. Environment Configuration

The application requires environment variables for configuration, such as database credentials. An example file is provided.

```bash
# Copy the example config file to a new .env file
cp config.example.env .env
```

After copying, you **must** edit the `.env` file and provide the correct values for your database connection and any other settings.

### 4. Database Setup

This project requires a PostgreSQL server with the PostGIS extension enabled.

1.  **Ensure PostgreSQL is running.**
2.  **Connect to your PostgreSQL server** and create a new database for the project if you haven't already.
3.  **Execute the setup script** against your new database. This script will create all the necessary tables, indexes, and constraints. You can run it using `psql` like this:

    ```bash
    psql -h your_host -U your_user -d your_database -f scripts/create_systems_pg.sql
    ```

### 5. Systemd Service Setup

To run the EDDN listener as a managed background service, a `systemd` unit file is provided. This is the recommended way to run the application in a production environment. It will handle automatic restarts and process monitoring.

**Important:** The provided `resupply-planner.service` file assumes your project is located at `/var/www/html/ResupplyPlanner` and will be run by the `apache` user. If your path or user is different, you **must** edit the `WorkingDirectory`, `ExecStart`, `EnvironmentFile`, `User`, and `Group` directives in the service file before proceeding.

1.  **Copy the Service File:**
    Copy the service file from the repository into the systemd directory.
    ```bash
    sudo cp resupply-planner.service /etc/systemd/system/resupply-planner.service
    ```

2.  **Reload Systemd:**
    Tell systemd to reload its configuration to recognize the new service.
    ```bash
    sudo systemctl daemon-reload
    ```

3.  **Enable the Service:**
    Enable the service to start automatically on system boot.
    ```bash
    sudo systemctl enable resupply-planner.service
    ```

4.  **Start and Verify the Service:**
    Start the service and check its status to ensure it's running correctly.
    ```bash
    # Start the service
    sudo systemctl start resupply-planner.service

    # Check the status
    sudo systemctl status resupply-planner.service
    ```

    You can view the service's log output in real-time using `journalctl`:
    ```bash
    journalctl -u resupply-planner.service -f
    ```
