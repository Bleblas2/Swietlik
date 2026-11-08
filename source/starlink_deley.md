
1. Space Leg (User Terminal ⇄ Satellite)

• Time: 1.8 ms to 3.6 ms per leg
• Details: Driven by the speed of light over the 550 km low Earth orbit (LEO) altitude. A direct overhead satellite takes about 3.7 ms for a round-trip (up and down), while satellites lower on the horizon increase the slant distance and add a few extra milliseconds.

2. Inter-Satellite Laser Links (Optional / Remote routing)

• Time: Variable (adds 1 ms to tens of ms depending on distance routed)
• Details: Used when traffic cannot route straight down to a ground station beneath the satellite (due to ocean gaps, lack of local gateways, or network congestion mitigation). Photons travel through space vacuum via optical inter-satellite links.

3. Ground Leg (Satellite ⇄ Gateway / Ground Station)

• Time: 1.8 ms to 3.6 ms per leg
• Details: The downlink/uplink distance from the satellite to the nearest terrestrial gateway station.

4. Ground Network & PoP Transit (Gateway ⇄ Internet / Point of Presence)

• Time: 5 ms to 20+ ms
• Details: Transport from the physical Starlink gateway site through SpaceX’s private fiber backbone to a regional Point of Presence (PoP) or Internet Exchange Point (IXP).