# ResupplyPlanner
A one-stop tool for hauling Tritium around the galaxy

## User Input
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

## Program Output

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

## Decisions
- web app, better when needing to ready APIs (current favorite)
- desktop client, better when needing to ready CMDR logs locally
