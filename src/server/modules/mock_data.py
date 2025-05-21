#!/usr/bin/env python3
"""
Mock data for PartSelect agent.
This provides sample data for refrigerator and dishwasher parts when live scraping is not possible.
"""

import json
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Sample refrigerator parts - extended catalog
REFRIGERATOR_PARTS = [
    {
        "partNumber": "PS11746337",
        "name": "Water Inlet Valve",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2198202.jpg",
        "price": 89.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT780SAEM1", 
            "WRS325SDHZ", 
            "WRF555SDFZ", 
            "WRX735SDHZ"
        ],
        "description": "The water inlet valve controls the flow of water into the refrigerator for the ice maker and water dispenser. If the valve fails, it can cause leaking, no water flow, or low water pressure."
    },
    {
        "partNumber": "PS11752778",
        "name": "Dispenser Module",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268383.jpg",
        "price": 158.67,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SMBM00", 
            "WRF535SWHZ", 
            "WRF767SDHZ", 
            "WRF555SDHV"
        ],
        "description": "The dispenser module controls the water and ice dispensing functions. If your dispenser isn't working properly, this module might need to be replaced."
    },
    {
        "partNumber": "PS11722167",
        "name": "Refrigerator Ice Maker Assembly",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8180356.jpg",
        "price": 239.50,
        "stock": "In Stock",
        "compatibleModels": [
            "WRS321SDHZ", 
            "WRS325FDAM", 
            "WRF535SWHZ", 
            "WRS571CIHZ"
        ],
        "description": "The ice maker assembly produces ice cubes for your refrigerator. If your refrigerator isn't making ice or is making too much ice, the ice maker may need to be replaced."
    },
    {
        "partNumber": "PS11705149",
        "name": "Temperature Control Thermostat",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2198202.jpg",
        "price": 142.75,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SMBM00", 
            "WRB322DMBM", 
            "WRS321SDHZ", 
            "WRF767SDHZ"
        ],
        "description": "The temperature control thermostat regulates the temperature in your refrigerator and freezer compartments. If your refrigerator is too warm or too cold, the thermostat may need to be replaced."
    },
    {
        "partNumber": "PS11703459",
        "name": "Defrost Timer",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp67003927.jpg",
        "price": 79.88,
        "stock": "Out of Stock",
        "compatibleModels": [
            "WDT780SAEM1", 
            "WRF535SWHZ", 
            "WRS571CIHZ", 
            "WRF767SDHZ"
        ],
        "description": "The defrost timer controls the defrost cycle of your refrigerator. If your refrigerator is building up too much frost, the defrost timer may need to be replaced."
    },
    {
        "partNumber": "PS11787619",
        "name": "Refrigerator Door Bin",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2256758.jpg",
        "price": 45.29,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SWHZ",
            "WRF767SDHZ",
            "WRS325FDAM",
            "WRS571CIHZ"
        ],
        "description": "The door bin is a shelf on the inside of the refrigerator door that holds bottles, jars, and other items. If your door bin is cracked or broken, it should be replaced."
    },
    {
        "partNumber": "PS11784756",
        "name": "Refrigerator Evaporator Fan Motor",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2188874.jpg",
        "price": 105.49,
        "stock": "In Stock",
        "compatibleModels": [
            "WRS325FDAM",
            "WRS571CIHZ",
            "WRF767SDHZ",
            "WRF535SWHZ"
        ],
        "description": "The evaporator fan motor circulates air through the evaporator and into the refrigerator and freezer compartments. If your refrigerator is making noise or not cooling properly, the fan motor may need to be replaced."
    },
    {
        "partNumber": "PS11761591",
        "name": "Refrigerator Water Filter",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wpw10295370a.jpg",
        "price": 49.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SWHZ",
            "WRF767SDHZ",
            "WRS325FDAM",
            "WRF555SDFZ"
        ],
        "description": "The water filter removes contaminants from the water used for the ice maker and water dispenser. It should be replaced every 6 months for optimal performance."
    },
    {
        "partNumber": "PS11748915",
        "name": "Refrigerator Compressor",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2319489.jpg",
        "price": 289.95,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SMBM00",
            "WRF767SDHZ",
            "WRS325FDAM",
            "WRS571CIHZ"
        ],
        "description": "The compressor is the heart of the refrigeration system, pumping refrigerant through the coils. If your refrigerator isn't cooling at all, the compressor may have failed."
    },
    {
        "partNumber": "PS11792457",
        "name": "Refrigerator Light Bulb",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2319962.jpg",
        "price": 12.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SWHZ",
            "WRF767SDHZ",
            "WRS325FDAM",
            "WRS571CIHZ",
            "WDT780SAEM1"
        ],
        "description": "The light bulb illuminates the interior of the refrigerator. If your refrigerator light isn't working, the bulb may need to be replaced."
    },
    {
        "partNumber": "PS11776283",
        "name": "Refrigerator Condenser Fan Motor",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2188908.jpg",
        "price": 79.95,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SWHZ",
            "WRF767SDHZ",
            "WRS325FDAM",
            "WRB322DMBM"
        ],
        "description": "The condenser fan motor cools the condenser coils by drawing air through them. If your refrigerator is overheating or not cooling properly, the condenser fan motor may need to be replaced."
    },
    {
        "partNumber": "PS11782143",
        "name": "Refrigerator Door Gasket",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2188479.jpg",
        "price": 89.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SWHZ",
            "WRF767SDHZ",
            "WRS571CIHZ",
            "WRB322DMBM"
        ],
        "description": "The door gasket creates a seal between the refrigerator door and cabinet. If your door isn't sealing properly or you feel cold air escaping, the gasket may need to be replaced."
    },
    {
        "partNumber": "PS11771924",
        "name": "Refrigerator Defrost Heater",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2213136.jpg",
        "price": 65.75,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SWHZ",
            "WRF767SDHZ",
            "WRS571CIHZ",
            "WRS325FDAM"
        ],
        "description": "The defrost heater melts frost that accumulates on the evaporator coils. If your refrigerator is building up excessive frost, the defrost heater may need to be replaced."
    },
    {
        "partNumber": "PS11758624",
        "name": "Refrigerator Control Board",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8201649.jpg",
        "price": 199.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SWHZ",
            "WRF767SDHZ",
            "WRS571CIHZ",
            "WRF535SMBM00"
        ],
        "description": "The control board regulates the refrigerator's functions. If your refrigerator is having multiple issues or not responding to controls, the control board may need to be replaced."
    },
    {
        "partNumber": "PS11795632",
        "name": "Refrigerator Shelf",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp2174744.jpg",
        "price": 59.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WRF535SWHZ",
            "WRF767SDHZ",
            "WRS571CIHZ",
            "WRS325FDAM"
        ],
        "description": "The shelf provides storage space inside the refrigerator. If your shelf is cracked or broken, it should be replaced."
    }
]

# Sample dishwasher parts - extended catalog
DISHWASHER_PARTS = [
    {
        "partNumber": "PS11743427",
        "name": "Dishwasher Drain Pump",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp661658.jpg",
        "price": 71.95,
        "stock": "In Stock",
        "compatibleModels": [
            "KDFE104HPS", 
            "WDT730PAHZ", 
            "WDT750SAHZ", 
            "WDF520PADM"
        ],
        "description": "The drain pump removes water from the dishwasher during the drain cycle. If your dishwasher isn't draining properly, the drain pump may need to be replaced."
    },
    {
        "partNumber": "PS11756393",
        "name": "Dishwasher Water Inlet Valve",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8531669.jpg",
        "price": 52.49,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT750SAHZ", 
            "WDF520PADM", 
            "KDFE104HPS", 
            "WDT970SAHZ"
        ],
        "description": "The water inlet valve controls the flow of water into the dishwasher. If your dishwasher isn't filling with water, the inlet valve might be defective."
    },
    {
        "partNumber": "PS11723171",
        "name": "Dishwasher Door Latch Assembly",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8193830.jpg",
        "price": 94.88,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ", 
            "WDT750SAHZ", 
            "WDF560SAFM", 
            "KDFE104HPS"
        ],
        "description": "The door latch assembly secures the dishwasher door and activates the door switch. If your dishwasher won't start or the door doesn't latch properly, this part may need to be replaced."
    },
    {
        "partNumber": "PS11708155",
        "name": "Dishwasher Control Board",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8564547.jpg",
        "price": 219.95,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ", 
            "WDT750SAHZ", 
            "WDF560SAFM", 
            "KDFE104HPS"
        ],
        "description": "The control board manages the dishwasher's functions and cycles. If your dishwasher isn't working correctly or isn't responding to commands, the control board may need to be replaced."
    },
    {
        "partNumber": "PS11769123",
        "name": "Dishwasher Spray Arm",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268433r.jpg",
        "price": 35.27,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT730PAHZ", 
            "WDT750SAHZ", 
            "WDF520PADM", 
            "KDFE104HPS"
        ],
        "description": "The spray arm distributes water throughout the dishwasher to clean your dishes. If your dishes aren't getting clean, the spray arm might be clogged or damaged."
    },
    {
        "partNumber": "PS11763814",
        "name": "Dishwasher Heating Element",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8194300.jpg",
        "price": 84.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDT750SAHZ",
            "WDF560SAFM",
            "KDFE104HPS"
        ],
        "description": "The heating element heats water during wash cycles and helps dry dishes. If your dishes aren't drying properly, the heating element may be defective."
    },
    {
        "partNumber": "PS11754921",
        "name": "Dishwasher Dispenser Assembly",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268391.jpg",
        "price": 105.75,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDT750SAHZ",
            "WDT730PAHZ",
            "WDF520PADM"
        ],
        "description": "The dispenser assembly releases detergent and rinse aid at the appropriate times during the wash cycle. If detergent isn't being dispensed properly, this assembly may need to be replaced."
    },
    {
        "partNumber": "PS11742639",
        "name": "Dishwasher Door Gasket",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268385.jpg",
        "price": 42.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDT750SAHZ",
            "WDF560SAFM",
            "KDFE104HPS"
        ],
        "description": "The door gasket creates a watertight seal when the dishwasher door is closed. If your dishwasher is leaking from the door, the gasket may need to be replaced."
    },
    {
        "partNumber": "PS11778432",
        "name": "Dishwasher Circulation Pump",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8269145.jpg",
        "price": 119.95,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDT750SAHZ",
            "WDF520PADM",
            "KDFE104HPS"
        ],
        "description": "The circulation pump circulates water through the spray arms during wash cycles. If your dishwasher isn't cleaning dishes properly, the circulation pump may be defective."
    },
    {
        "partNumber": "PS11735184",
        "name": "Dishwasher Timer",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268413.jpg",
        "price": 145.49,
        "stock": "Out of Stock",
        "compatibleModels": [
            "WDF520PADM",
            "KDFE104HPS",
            "WDT730PAHZ",
            "WDF560SAFM"
        ],
        "description": "The timer controls the duration of each wash cycle. If your dishwasher is stuck in one cycle or won't advance to the next cycle, the timer may need to be replaced."
    },
    {
        "partNumber": "PS11749673",
        "name": "Dishwasher Float Switch Assembly",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268429.jpg",
        "price": 28.75,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDF520PADM",
            "KDFE104HPS",
            "WDT750SAHZ"
        ],
        "description": "The float switch prevents the dishwasher from overfilling. If your dishwasher keeps filling with water or won't fill at all, the float switch may be defective."
    },
    {
        "partNumber": "PS11767529",
        "name": "Dishwasher Wash Arm Bearing Kit",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268375.jpg",
        "price": 18.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDT750SAHZ",
            "WDF560SAFM",
            "WDF520PADM"
        ],
        "description": "The wash arm bearing kit allows the spray arm to rotate freely. If the spray arm isn't spinning properly, the bearing kit may need to be replaced."
    },
    {
        "partNumber": "PS11751892",
        "name": "Dishwasher Silverware Basket",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268376.jpg",
        "price": 37.49,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDT750SAHZ",
            "WDF560SAFM",
            "KDFE104HPS",
            "WDT730PAHZ"
        ],
        "description": "The silverware basket holds utensils during wash cycles. If your silverware basket is damaged or missing, it should be replaced for optimal cleaning."
    },
    {
        "partNumber": "PS11759246",
        "name": "Dishwasher Rack Adjuster",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268404.jpg",
        "price": 22.99,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDT750SAHZ",
            "WDF560SAFM",
            "KDFE104HPS"
        ],
        "description": "The rack adjuster allows you to raise or lower the upper dish rack. If your rack won't stay in position or is difficult to adjust, the rack adjuster may need to be replaced."
    },
    {
        "partNumber": "PS11774635",
        "name": "Dishwasher Rinse Aid Dispenser Cap",
        "imageUrl": "https://www.appliancepartspros.com/images/thmb/65-wp8268398.jpg",
        "price": 15.45,
        "stock": "In Stock",
        "compatibleModels": [
            "WDT970SAHZ",
            "WDT750SAHZ",
            "WDF560SAFM",
            "WDF520PADM",
            "KDFE104HPS"
        ],
        "description": "The rinse aid dispenser cap covers the rinse aid reservoir. If your rinse aid is leaking or not dispensing, the cap may need to be replaced."
    }
]

# Sample documentation content for refrigerator and dishwasher parts
DOCS_CONTENT = [
    {
        "title": "How to Replace a Refrigerator Water Filter",
        "type": "installation",
        "applianceType": "refrigerator",
        "content": """
# Water Filter Replacement Guide

## Tools Required
- No tools required

## Estimated Time
- 5 minutes

## Step-by-Step Instructions
1. Locate your water filter inside the refrigerator, typically in the upper right corner of the fresh food section or in the base grille.
2. If your filter is in the interior, push the button next to the filter to release it.
3. Pull the old filter straight out and remove it completely.
4. Remove the protective cap from the new filter.
5. Insert the new filter into the same location, pushing until it clicks into place.
6. Run 2-3 gallons of water through the dispenser to clear the system and remove any carbon residue.

## Important Notes
- Replace your water filter every 6 months for optimal performance.
- Some models may require turning the filter counter-clockwise to remove.
- Check your model's manual for specific instructions related to your refrigerator model.
"""
    },
    {
        "title": "Refrigerator Ice Maker Troubleshooting",
        "type": "troubleshooting",
        "applianceType": "refrigerator",
        "content": """
# Ice Maker Not Working

## Common Issues and Solutions

### Ice maker not producing ice
1. Check that the ice maker is turned on.
2. Ensure water supply to the refrigerator is connected and turned on.
3. Verify that the water filter is not clogged (replace if needed).
4. Check for frozen water line - thaw if necessary.
5. Inspect the water inlet valve for proper operation.

### Ice maker producing small or hollow ice cubes
1. Low water pressure may be the cause.
2. Check water filter and replace if clogged.
3. Verify water line is not kinked or restricted.
4. Inspect the water inlet valve for partial blockage.

### Ice maker making too much ice or overflowing
1. Check the ice maker's shut-off arm or sensor for proper operation.
2. Inspect the water inlet valve for leaks or sticking.
3. Consider replacing the ice maker assembly if persistent.

## When to Call a Professional
- If water is leaking inside the freezer compartment
- If electrical components aren't functioning
- If replacing parts doesn't resolve the issue
"""
    },
    {
        "title": "Dishwasher Not Draining Troubleshooting Guide",
        "type": "troubleshooting",
        "applianceType": "dishwasher",
        "content": """
# Dishwasher Not Draining

## Common Causes and Solutions

### Check for visible blockages
1. Remove any standing water with a cup and towel.
2. Remove and clean the dishwasher filter assembly at the bottom of the tub.
3. Check for food particles or foreign objects in the sump area.
4. Ensure the spray arms are free of debris and can rotate freely.

### Inspect the drain hose
1. Locate the drain hose at the back of the dishwasher.
2. Check for kinks, bends, or blockages in the hose.
3. Disconnect the hose from the sink drain or garbage disposal and check for clogs.
4. Ensure the drain hose is properly installed with a high loop to prevent backflow.

### Check the drain pump
1. Listen for the drain pump running at the end of a cycle.
2. If no sound, the pump may be defective and need replacement.
3. Check the pump impeller for obstructions if accessible.

### Garbage disposal connection
1. If connected to a garbage disposal, make sure the knockout plug was removed during installation.
2. Run the garbage disposal to clear any debris that might be blocking the dishwasher drain.

## Preventative Maintenance
- Always scrape plates before loading
- Clean the filter regularly (weekly to monthly)
- Run hot water in sink before starting dishwasher
- Use a dishwasher cleaner monthly

## When to Call a Professional
- If water is leaking onto the floor
- If none of the above solutions resolve the issue
- If the drain pump makes unusual noises
"""
    },
    {
        "title": "How to Replace a Dishwasher Door Seal",
        "type": "installation",
        "applianceType": "dishwasher",
        "content": """
# Dishwasher Door Seal Replacement

## Tools Required
- Clean cloth
- Mild detergent
- Scissors (if needed)
- Screwdriver (for some models)

## Estimated Time
- 30 minutes

## Step-by-Step Instructions
1. Unplug the dishwasher or turn off power at the circuit breaker for safety.
2. Open the dishwasher door completely.
3. Locate the door seal (gasket) around the perimeter of the dishwasher opening.
4. Starting at one corner, carefully pull the old seal away from the door channel.
5. Continue removing the entire seal, noting how it was installed.
6. Clean the channel with mild detergent and a cloth to remove any residue.
7. Allow the channel to dry completely.
8. If the new seal is longer than needed, measure against the old seal and trim with scissors.
9. Starting at the top center of the door, press the new seal into the channel.
10. Work your way around the door, ensuring the seal is fully seated in the channel.
11. Close the door to check that the seal is properly positioned and makes full contact.

## Important Notes
- Make sure the lip of the seal faces the correct direction (usually inward).
- Some models may have clips or screws securing the seal that need to be removed first.
- Handle the new seal carefully to avoid tears or stretching.
- If the door doesn't close properly after installation, check for proper positioning of the seal.

## When to Replace the Door Seal
- Visible cracks, tears, or deterioration
- Water leaking from the dishwasher during operation
- Door not closing properly
- Unusual odors coming from the dishwasher
"""
    },
    {
        "title": "Refrigerator Temperature Troubleshooting",
        "type": "troubleshooting",
        "applianceType": "refrigerator",
        "content": """
# Refrigerator Temperature Issues

## Refrigerator Not Cold Enough

### Check the settings
1. Verify the temperature controls are set correctly (typically 37°F for refrigerator, 0°F for freezer).
2. If you recently added a large amount of food, the refrigerator may need time to recover.
3. Make sure the refrigerator is not in demo or showroom mode.

### Check for airflow issues
1. Ensure vents between compartments are not blocked by food items.
2. Leave space between items and walls to allow for proper air circulation.
3. Check that the condenser coils are clean (unplug refrigerator first).
4. Verify the condenser fan is operating properly.

### Door seals and usage
1. Inspect door gaskets for tears, gaps, or food debris.
2. Minimize how often and how long doors are opened.
3. Ensure doors are closing completely.

## Refrigerator Too Cold or Freezing Food

1. Check temperature settings and adjust if necessary.
2. Verify the temperature sensor or thermistor is functioning properly.
3. Keep items away from the coldest areas (typically rear walls or certain shelves).
4. For frost buildup, check door seals and humidity levels.

## Common Parts That May Need Replacement
- Thermistor/temperature sensor
- Damper control assembly
- Main control board
- Evaporator fan motor
- Door gaskets

## When to Call a Professional
- If food is spoiling despite correct settings
- If the compressor is running constantly
- If there are unusual noises
- If adjusting settings has no effect on temperature
"""
    },
    {
        "title": "How to Install a Dishwasher Heating Element",
        "type": "installation",
        "applianceType": "dishwasher",
        "content": """
# Dishwasher Heating Element Replacement

## Tools Required
- Phillips screwdriver
- Nut driver or socket set
- Multimeter (for testing)
- Towel or shallow pan (for water collection)
- Work gloves

## Estimated Time
- 45-60 minutes

## Safety Precautions
- Disconnect power to the dishwasher at the circuit breaker
- Shut off water supply to the dishwasher
- Allow the dishwasher to cool completely if recently used

## Step-by-Step Instructions

### Preparation and Access
1. Turn off power to the dishwasher at the circuit breaker.
2. Open the dishwasher door and remove the lower dish rack.
3. Remove any bottom spray arm or filter assembly that blocks access to the heating element.
4. Place a towel or shallow pan at the base to catch any water.

### Remove the Old Heating Element
1. Locate the heating element at the bottom of the dishwasher tub (circular or horseshoe-shaped metal tube).
2. Inside the tub, remove any brackets or screws securing the heating element to the tub floor.
3. From underneath or behind the dishwasher (you may need to pull the unit out), locate the heating element terminals.
4. Take a photo or note the wire connections before disconnecting.
5. Disconnect the electrical wires from the element terminals.
6. Remove any nuts or brackets securing the element to the dishwasher.
7. Carefully pull the heating element out of the dishwasher tub.

### Install the New Heating Element
1. Compare the new heating element to the old one to ensure it's the correct replacement.
2. Insert the new heating element through the holes in the dishwasher tub.
3. Secure the element with the brackets and screws inside the tub.
4. Reconnect the electrical wires to the appropriate terminals.
5. Secure any nuts or brackets on the exterior connections.
6. Reinstall the spray arm, filter assembly, and other components removed earlier.
7. Replace the lower dish rack.

### Testing
1. Restore power at the circuit breaker.
2. Run a short dishwasher cycle to verify the heating element is functioning properly.
3. Check for leaks around the heating element connections.

## Troubleshooting
- If the dishwasher doesn't heat, verify electrical connections.
- If leaking occurs, check the seals where the element passes through the tub.
- Use a multimeter to test for continuity if the element doesn't heat up.

## When to Call a Professional
- If you're uncomfortable working with electrical components
- If the heating element appears damaged during installation
- If leaking persists after installation
- If the dishwasher control panel shows error codes after installation
"""
    },
    {
        "title": "How to Replace a Refrigerator Ice Maker Assembly",
        "type": "installation",
        "applianceType": "refrigerator",
        "content": """
# Refrigerator Ice Maker Assembly Replacement

## Tools Required
- Phillips screwdriver
- Flat-head screwdriver
- Quarter-inch nut driver
- Work gloves
- Towel

## Estimated Time
- 30-45 minutes

## Step-by-Step Instructions

### Preparation
1. Unplug the refrigerator or turn off power at the circuit breaker.
2. Turn off the water supply to the refrigerator.
3. Remove any ice from the ice bucket and set aside.

### Remove the Old Ice Maker
1. Remove the ice bucket from beneath the ice maker.
2. Locate the mounting screws securing the ice maker to the freezer wall (typically 2-3 screws).
3. Remove these screws and carefully pull the ice maker assembly away from the wall, but don't pull it out completely yet.
4. Locate the wiring harness connecting the ice maker to the refrigerator.
5. Press the tab on the wiring harness connector and disconnect it from the ice maker.
6. If your model has a water tube connected directly to the ice maker, disconnect it by pulling the locking clip and gently removing the tube.
7. Remove the old ice maker assembly completely.

### Install the New Ice Maker
1. Unpack the new ice maker and check that it matches your old unit.
2. Connect the wiring harness to the new ice maker until it clicks into place.
3. If applicable, reconnect the water tube by pushing it firmly into the fitting until it stops, then secure with the locking clip.
4. Position the ice maker against the freezer wall, aligning the mounting holes.
5. Insert and tighten the mounting screws to secure the ice maker in place.
6. Reinstall the ice bucket beneath the ice maker.

### Finishing Up
1. Turn the water supply back on.
2. Plug the refrigerator back in or turn on power at the circuit breaker.
3. Discard the first few batches of ice (2-3 batches) to ensure any manufacturing residue is flushed out.

## Important Notes
- Some ice makers have a fill tube heater that needs to be transferred to the new unit.
- Check your model's specifications to determine if you need to adjust the water level after installation.
- It may take 24 hours before the new ice maker begins producing ice.

## Troubleshooting
- If the ice maker doesn't produce ice, check that the wire harness is fully connected.
- Ensure the water supply is turned on and the line isn't frozen.
- Verify that the ice maker is turned on (some have an on/off switch or arm).
- Check for proper water pressure (typically 40-120 psi required).

## When to Call a Professional
- If there are water leaks after installation
- If the ice maker still doesn't produce ice after 24 hours
- If error codes appear on the refrigerator display
"""
    },
    {
        "title": "Dishwasher Spray Arm Troubleshooting and Replacement",
        "type": "installation",
        "applianceType": "dishwasher",
        "content": """
# Dishwasher Spray Arm Troubleshooting and Replacement

## Common Spray Arm Problems
- Spray arms not rotating
- Poor cleaning performance
- Blocked spray holes
- Cracked or damaged arms
- Loose or wobbly movement

## Diagnostic Steps
1. Inspect spray arms for visible damage or cracks.
2. Check spray holes for food debris or mineral buildup.
3. Verify that the spray arms rotate freely by hand.
4. Ensure nothing in the dishwasher is blocking arm rotation.
5. Check the water pressure by running hot water at a nearby sink.

## Tools Required for Replacement
- Towel or cloth
- Small brush or toothpick (for cleaning)
- Screwdriver (for some models)

## Estimated Time
- 15-30 minutes

## Step-by-Step Replacement Instructions

### Lower Spray Arm Replacement
1. Remove the bottom dish rack from the dishwasher.
2. Locate the lower spray arm at the bottom of the dishwasher tub.
3. For most models, simply lift the spray arm straight up to remove it.
4. Some models may have a cap or retaining nut - turn counterclockwise to remove.
5. Lift out the old spray arm.
6. Place the new spray arm in the same position.
7. If applicable, replace the retaining nut or cap and turn clockwise to tighten.
8. Verify the arm rotates freely by spinning it by hand.

### Middle or Upper Spray Arm Replacement
1. Remove the upper or middle dish rack by sliding it out and lifting.
2. Some racks have stops that need to be released first (check user manual).
3. Locate the spray arm attached to the bottom of the upper rack or the middle of the dishwasher.
4. For upper rack spray arms, look for clips, tabs, or screws securing it to the rack.
5. Release these fasteners and remove the old spray arm.
6. Install the new spray arm in the same orientation and secure with the fasteners.
7. For middle spray arms, they typically unscrew or pull straight down to remove.
8. Install the new middle spray arm and ensure it's securely attached.
9. Test that all spray arms rotate freely before replacing the racks.

## Maintenance Tips
- Clean spray arm holes monthly using a toothpick or small wire.
- Rinse dishes thoroughly before loading to prevent food buildup.
- Run vinegar through the dishwasher periodically to reduce mineral deposits.
- Check and clean the filter regularly to ensure proper water flow.

## When to Call a Professional
- If replacing the spray arm doesn't improve cleaning performance
- If there are unusual noises during operation
- If water pressure seems insufficient despite spray arm replacement
- If connections are leaking after replacement
"""
    },
    {
        "title": "Refrigerator Compressor Troubleshooting Guide",
        "type": "troubleshooting",
        "applianceType": "refrigerator",
        "content": """
# Refrigerator Compressor Issues

## Signs of Compressor Problems
- Refrigerator not cooling properly
- Compressor continuously running without stopping
- Refrigerator not running at all
- Unusual sounds (clicking, buzzing, or humming)
- Refrigerator cycling on and off frequently
- Exterior of refrigerator unusually hot

## Diagnostic Steps

### Listen for the compressor
1. Locate the compressor (typically at the bottom rear of the refrigerator).
2. The compressor should make a low humming sound when running.
3. If you hear clicking or buzzing instead of humming, there may be an electrical issue.
4. Complete silence from the compressor area when the refrigerator should be cooling indicates a potential problem.

### Check for heat
1. The compressor should feel warm to the touch when running (not extremely hot).
2. If the compressor is very hot, it may be overworking due to:
   - Low refrigerant
   - Poor ventilation
   - Dirty condenser coils
   - Faulty components

### Inspect related components
1. Check condenser coils for dust and debris (unplug refrigerator first).
2. Verify the condenser fan is running when the compressor is on.
3. Ensure proper clearance around the refrigerator for ventilation.
4. Test the thermostat by adjusting settings to see if the compressor responds.

## Possible Solutions

### For a compressor that won't start
1. Check power supply and make sure the refrigerator is plugged in securely.
2. Test the outlet with another appliance.
3. Inspect for tripped circuit breakers or blown fuses.
4. The start relay or overload protector may be faulty and need replacement.

### For a constantly running compressor
1. Clean condenser coils (unplug refrigerator first).
2. Check door seals for leaks or gaps.
3. Ensure doors are closing properly.
4. Verify the refrigerator isn't in a hot environment.
5. The thermostat may be malfunctioning.

### For noisy operation
1. Make sure the refrigerator is level on the floor.
2. Check that the compressor mounting hardware is tight.
3. Verify nothing is touching or vibrating against the compressor.
4. The compressor may have internal damage if noise persists.

## Important Cautions
- Never attempt to repair or replace a compressor yourself unless you are a qualified technician.
- The compressor contains refrigerant under pressure and requires special tools and certification.
- Tampering with a compressor may release harmful chemicals and void your warranty.

## When to Call a Professional
- If the compressor is not running and basic checks don't resolve the issue
- If the refrigerator is not cooling despite the compressor running
- If there are unusual or loud noises from the compressor
- If the compressor cycles on and off rapidly
- If the compressor feels extremely hot to the touch
"""
    },
    {
        "title": "Dishwasher Control Board Replacement Guide",
        "type": "installation",
        "applianceType": "dishwasher",
        "content": """
# Dishwasher Control Board Replacement

## Tools Required
- Phillips screwdriver
- Flat-head screwdriver
- Nut driver (¼-inch)
- Needle-nose pliers
- Work gloves
- Flashlight
- Container for screws

## Estimated Time
- 45-60 minutes

## Safety Precautions
- Disconnect power to the dishwasher at the circuit breaker
- Wear work gloves to protect hands from sharp edges
- Use caution when handling electronic components

## Step-by-Step Instructions

### Preparation
1. Turn off power to the dishwasher at the circuit breaker.
2. Turn off the water supply to the dishwasher.
3. Open the dishwasher door and remove any items.
4. Take a photo of the control panel and buttons for reference.

### Access the Control Board
1. Depending on your model, the control board may be located:
   - Behind the control panel at the top of the door
   - Behind the kick plate at the bottom front of the dishwasher
   - Behind the inner door panel

#### For Control Panel Access:
1. Locate the screws securing the control panel (usually on the underside of the panel or behind the door).
2. Remove these screws and set aside in a container.
3. Carefully pull the control panel forward or lift it up, depending on the model.
4. The control board should be visible, typically in a plastic housing.

#### For Inner Door Access:
1. Remove the screws around the perimeter of the inner door panel.
2. Carefully separate the inner panel from the door, being mindful of any wires.
3. The control board is typically mounted to the inside of the outer door panel.

### Remove the Old Control Board
1. Take a photo of all wire connections before disconnecting anything.
2. Using needle-nose pliers, carefully disconnect all wire harnesses from the control board.
3. Note the position and color of each wire connection.
4. Remove the screws or clips securing the control board to its mounting location.
5. Carefully lift out the old control board.

### Install the New Control Board
1. Compare the new control board to the old one to ensure they match.
2. Place the new control board in the same position as the old one.
3. Secure it with the screws or clips you removed earlier.
4. Reconnect all wire harnesses according to your photo reference.
5. Ensure all connections are secure and properly seated.

### Reassemble the Dishwasher
1. Replace the control panel or inner door panel.
2. Secure all screws in their original positions.
3. Double-check that all components are properly aligned and secured.

### Test the Installation
1. Restore power at the circuit breaker.
2. Turn on the water supply.
3. Test various cycles and functions to ensure the new control board is working properly.

## Troubleshooting
- If the dishwasher doesn't power on, check all wire connections.
- If certain functions don't work, verify the corresponding wire harnesses are properly connected.
- If error codes appear, consult the manufacturer's documentation for the specific code meaning.

## When to Call a Professional
- If you're uncomfortable working with electronic components
- If the dishwasher still doesn't function after replacement
- If you see signs of water damage or corrosion on the new board
- If additional components appear damaged
"""
    },
    {
        "title": "Safety Guidelines for Appliance Repair",
        "type": "safety",
        "applianceType": "general",
        "content": """
# Important Safety Guidelines for DIY Appliance Repair

## General Safety Precautions

### Electrical Safety
1. **ALWAYS disconnect power** before working on any appliance:
   - Unplug the appliance from the outlet
   - Or turn off the circuit breaker/remove the fuse for hardwired appliances
2. Use a voltage tester to confirm power is off before touching any electrical components.
3. Never touch electrical components with wet hands.
4. Avoid using extension cords with major appliances.
5. If you smell burning or see damaged wires, stop immediately and consult a professional.

### Gas Appliance Safety
1. If you smell gas, do NOT:
   - Turn on/off any electrical switches
   - Use phones in the area
   - Light matches or candles
2. Instead:
   - Turn off the gas supply if possible
   - Open windows and doors
   - Evacuate and call your gas company from a safe location
3. Always shut off the gas supply before working on gas appliances.
4. Test for gas leaks with approved methods after completing repairs.

### Water-Connected Appliance Safety
1. Turn off the water supply before working on refrigerators, dishwashers, or washing machines.
2. Have towels and a bucket ready to catch any water when disconnecting water lines.
3. Check for leaks thoroughly after reconnecting water lines.

### Physical Safety
1. Wear appropriate safety gear:
   - Work gloves for sharp edges
   - Safety glasses for protection from debris
   - Closed-toe shoes
2. Use proper lifting techniques for heavy appliances.
3. Secure appliances properly to prevent tipping.
4. Keep work area clean and free of trip hazards.
5. Use proper tools designed for the specific task.

## When NOT to DIY
1. If the repair involves:
   - Sealed refrigeration systems containing refrigerant
   - Major gas line repairs
   - Complex electrical system work
2. If you don't have the proper tools or knowledge.
3. If repairs could void the warranty.
4. If you're dealing with water or fire damage.

## After Completing Repairs
1. Double-check all connections before restoring power or water.
2. Keep others away until you've verified the appliance is working safely.
3. Monitor the appliance after repair to ensure it's functioning correctly.
4. Keep repair documentation and receipts for future reference.

## Emergency Contacts
- Keep these numbers accessible:
  - Local fire department
  - Gas company
  - Qualified appliance repair technician
  - Poison control (1-800-222-1222 in the US)

Remember: When in doubt, always consult with a professional technician. Your safety is more important than saving money on repairs.
"""
    }
]

class MockDataProvider:
    """
    Provides mock data for the PartSelect agent when live scraping is not possible.
    Handles both product catalog data and documentation.
    """
    
    def __init__(self):
        """Initialize the mock data provider with refrigerator and dishwasher parts and documentation."""
        self.refrigerator_parts = REFRIGERATOR_PARTS
        self.dishwasher_parts = DISHWASHER_PARTS
        self.docs = DOCS_CONTENT
        self.logger = logging.getLogger(__name__)
        self.logger.info("MockDataProvider initialized with %d refrigerator parts, %d dishwasher parts, and %d docs", 
                         len(self.refrigerator_parts), len(self.dishwasher_parts), len(self.docs))
    
    def get_all_parts(self):
        """Return all parts in the mock catalog."""
        return self.refrigerator_parts + self.dishwasher_parts
    
    def get_part_by_number(self, part_number):
        """Retrieve a part by its part number."""
        for part in self.get_all_parts():
            if part["partNumber"] == part_number:
                return part
        return None
    
    def search_parts(self, query, appliance_type=None, limit=10):
        """
        Search for parts based on a query string.
        
        Args:
            query: The search term
            appliance_type: Optional filter for refrigerator or dishwasher
            limit: Maximum number of results to return
            
        Returns:
            List of matching parts
        """
        query = query.lower()
        results = []
        
        # Determine which collections to search
        collections = []
        if appliance_type == "refrigerator" or appliance_type is None:
            collections.append(self.refrigerator_parts)
        if appliance_type == "dishwasher" or appliance_type is None:
            collections.append(self.dishwasher_parts)
        
        # Search through the collections
        for collection in collections:
            for part in collection:
                if (query in part["name"].lower() or 
                    query in part["description"].lower() or 
                    query in part["partNumber"].lower()):
                    results.append(part)
                
                # Stop if we've reached the limit
                if len(results) >= limit:
                    break
            
            if len(results) >= limit:
                break
                
        return results[:limit]
    
    def find_compatible_parts(self, model_number, limit=10):
        """Find parts compatible with a specific model number."""
        model_number = model_number.upper()
        results = []
        
        for part in self.get_all_parts():
            if "compatibleModels" in part and model_number in part["compatibleModels"]:
                results.append(part)
                if len(results) >= limit:
                    break
                    
        return results
    
    def is_part_compatible(self, part_number, model_number):
        """Check if a specific part is compatible with a model number."""
        part = self.get_part_by_number(part_number)
        if not part or "compatibleModels" not in part:
            return False
            
        return model_number.upper() in part["compatibleModels"]
    
    def get_popular_parts(self, appliance_type, limit=5):
        """Get a list of popular parts for a specific appliance type."""
        if appliance_type.lower() == "refrigerator":
            return self.refrigerator_parts[:limit]
        elif appliance_type.lower() == "dishwasher":
            return self.dishwasher_parts[:limit]
        else:
            return []
    
    # Documentation methods
    
    def get_doc_by_title(self, title):
        """Retrieve a document by its title."""
        for doc in self.docs:
            if doc["title"].lower() == title.lower():
                return doc
        return None
    
    def search_docs(self, query, doc_type=None, appliance_type=None, limit=5):
        """
        Search for documentation based on a query string.
        
        Args:
            query: The search term
            doc_type: Optional filter for installation or troubleshooting
            appliance_type: Optional filter for refrigerator or dishwasher
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        query = query.lower()
        results = []
        
        for doc in self.docs:
            # Apply filters if specified
            if doc_type and doc["type"] != doc_type:
                continue
                
            if appliance_type and doc["applianceType"] != appliance_type:
                continue
                
            # Check if query appears in title or content
            if query in doc["title"].lower() or query in doc["content"].lower():
                results.append(doc)
                
            if len(results) >= limit:
                break
                
        return results[:limit]
    
    def get_installation_docs(self, part_name=None, appliance_type=None, limit=5):
        """Get installation documentation for a part or appliance type."""
        results = []
        
        for doc in self.docs:
            if doc["type"] != "installation":
                continue
                
            if appliance_type and doc["applianceType"] != appliance_type:
                continue
                
            if part_name and part_name.lower() not in doc["title"].lower():
                continue
                
            results.append(doc)
            
            if len(results) >= limit:
                break
                
        return results[:limit]
    
    def get_troubleshooting_docs(self, problem=None, appliance_type=None, limit=5):
        """Get troubleshooting documentation for a specific problem or appliance type."""
        results = []
        
        for doc in self.docs:
            if doc["type"] != "troubleshooting":
                continue
                
            if appliance_type and doc["applianceType"] != appliance_type:
                continue
                
            if problem and problem.lower() not in doc["title"].lower() and problem.lower() not in doc["content"].lower():
                continue
                
            results.append(doc)
            
            if len(results) >= limit:
                break
                
        return results[:limit]
    
    def get_repair_steps(self, part_name, appliance_type=None):
        """Extract repair steps for replacing a specific part."""
        # First try to find installation docs for this specific part
        docs = self.get_installation_docs(part_name, appliance_type, limit=1)
        
        if not docs:
            # If no specific docs, return generic steps
            return ["1. Turn off power to the appliance", 
                    "2. Remove the old part carefully", 
                    "3. Install the new part in the same position", 
                    "4. Restore power and test the appliance"]
        
        # Parse the markdown content to extract the steps section
        content = docs[0]["content"]
        
        # Look for Step-by-Step Instructions section
        if "## Step-by-Step Instructions" in content:
            steps_section = content.split("## Step-by-Step Instructions")[1]
            # Find the end of the section (next ## heading or end of content)
            if "##" in steps_section:
                steps_section = steps_section.split("##")[0]
            
            # Extract steps (lines starting with numbers)
            steps = []
            for line in steps_section.strip().split("\n"):
                if line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")):
                    steps.append(line.strip())
            
            return steps
        
        # Fallback to generic steps
        return ["1. Turn off power to the appliance", 
                "2. Remove the old part carefully", 
                "3. Install the new part in the same position", 
                "4. Restore power and test the appliance"]
    
    def get_safety_notes(self, appliance_type=None):
        """Get safety notes for appliance repair."""
        # First try to find the general safety document
        for doc in self.docs:
            if doc["type"] == "safety":
                # Extract the most important safety points
                content = doc["content"]
                safety_notes = []
                
                # Look for important safety points (usually after ### headings)
                for line in content.split("\n"):
                    if line.strip().startswith("###"):
                        safety_notes.append(line.strip().replace("###", "").strip())
                    elif line.strip().startswith("1. **ALWAYS"):
                        safety_notes.append("ALWAYS disconnect power before repairs")
                    elif "If you smell gas" in line:
                        safety_notes.append("If you smell gas, evacuate and call from a safe location")
                
                return safety_notes[:5]  # Return up to 5 safety notes
        
        # Fallback to generic safety notes
        return [
            "ALWAYS disconnect power before attempting repairs",
            "Use appropriate safety gear (gloves, eye protection)",
            "Turn off water supply for water-connected appliances",
            "Keep a fire extinguisher nearby",
            "When in doubt, consult a professional"
        ] 