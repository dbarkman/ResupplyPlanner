# ResupplyPlanner
A one-stop tool for hauling Tritium around the galaxy

User Input:
- departure system
- final arrival system
- carrier modules for each carrier
    - whether to decom or not
- ship(s) traveling with carrier(s)
    - available cargo sizes
- miner(s) traveling with the carrier(s)
- expected cost for Tritium
- profit desired in credits (adjust this to find an agreeable price with depot owner)
- final destination
- top-off stops
- other stops
    - specific systems
    - near specific systems (closest jump point to Sag A)
- ability to add mining resupply system and amount (will impact future fuel supplies)
- IRL day and time of departure, local and UTC
- hours available per day
- exploration/mining/non-travel days planned

Program Output:
- sell price to offer
- total round trip jumps, including any relays round trips
- total cost for Tritium
- total cost for Carrier(s) mainenance jumps
- total cost for Carrier(s) upkeep, for days away from originating system
- total costs
- gross profit
- net profit
- need to mine amounts
- amount paid to mine vs purchase
- approximate hours to travel
- approximate hours to mine
- IRL schedule
    - set hours available for each day of schedule
- downloadable CSV route sheets
    - for entire trip or any leg
    - compatible with FCOC routes
- relay fuel transfer instructions
- instructions for topping off depot and transferring from market after each jump
- can communicate with discord bots to provide travel/resupply updates

Decisions:
- web app or desktop client
