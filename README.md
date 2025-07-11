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

Ensure your MariaDB or MySQL server is running. Connect to your database server and execute the SQL command found in `ResupplyPlanner.md` under the "Database Schema" section to create the `systems` table.

### 5. Log Rotation (Cron Job)

A script is provided to handle daily log rotation and cleanup. This should be run via a cron job to ensure log files do not grow indefinitely.

1.  Make the script executable:
    ```bash
    chmod +x scripts/rotate_logs.py
    ```
2.  Open your crontab for editing:
    ```bash
    crontab -e
    ```
3.  Add the following line to run the script every day at midnight. **Make sure to replace `/path/to/ResupplyPlanner` with the absolute path to the project directory.**

    ```cron
    0 0 * * * /path/to/ResupplyPlanner/venv/bin/python /path/to/ResupplyPlanner/scripts/rotate_logs.py
    ```

This setup ensures that the script runs using the correct Python interpreter from your virtual environment. The script will handle renaming the previous day's log and deleting logs older than 5 days.
