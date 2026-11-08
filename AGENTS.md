# Swietlik - Earth-to-Orbit Laser Communications

## Project concept

Develop and evaluate a high-speed laser communication system from Earth to
low Earth orbit (LEO), at altitudes up to approximately 1,000 km. The intended
application is high-capacity ground-to-satellite uplinks for constellations
such as Starlink and similar systems.

Use NASA TechPort project 95868 as a reference for a related system:
https://techport.nasa.gov/projects/95868
The local TechPort report has been reviewed: project 95868 is TBIRD,
a LEO-to-Earth optical downlink design with burst rates up to 200 Gbps.
NASA separately confirms a 200 Gbps downlink demonstration in April 2023.
Do not treat this as proof of a 200 Gbps ground-to-Starlink uplink.

## Motivation and working assumptions

Investigate whether optical uplinks could reduce a capacity bottleneck in
existing radio feeder links. The initial hypothesis is that relevant radio
links operate around 19-30 GHz and provide approximately 600 Mbps-1.2 Gbps.
These frequencies, capacities, and the proposed bottleneck are unverified
starting assumptions, not established specifications for Starlink. Verify
them and distinguish feeder links from user links before making comparisons.

Compatibility with existing satellites, including their ability to receive
ground-based optical uplinks, must also be established rather than assumed.

## Weather-aware ground network

Study a geographically distributed network of optical ground stations across
Europe. Clouds and rain can degrade or interrupt optical transmission, so
the system should select usable stations and routes as weather changes.

At each candidate site, investigate a monitoring cluster of six antennas
arranged in a straight line. The cluster would monitor signals from nearby
radio stations and track changes in received signal quality. The working
hypothesis is that degradation in these signals may provide advance warning
of conditions that could impair the optical link.

Validate this hypothesis experimentally. Identify suitable radio sources,
frequencies, antenna spacing, measurements, and sampling intervals, and test
whether the observations predict optical attenuation or outages with useful
lead time. Do not assume that degradation of an arbitrary radio signal is a
reliable proxy for optical-link availability.

When monitoring indicates an increased risk of optical-link degradation,
increase the routing cost of the affected laser link. Use smoothing,
hysteresis, and hold-down intervals to avoid route flapping while enabling
proactive switching to healthier paths or ground stations.

## Initial European availability study

Obtain historical cloud-cover maps for Europe from Zoom Earth, subject to
available data access and usage terms. Analyze several days of observations
to estimate how many candidate ground stations would be usable and when.
If suitable historical data cannot be obtained there, document the limitation
and identify an appropriate alternative weather-data source.

Combine weather observations with satellite visibility and elevation
constraints for orbits up to 1,000 km. Report weather availability separately
from actual ground-to-satellite contact opportunities. Define the candidate
station locations, time resolution, cloud and precipitation thresholds, and
missing-data handling explicitly.

The initial study should produce:

- A time series of usable stations and their geographic distribution.
- Estimates of simultaneous station availability and network-wide outages.
- Contact windows that account for both weather and satellite visibility.
- An assessment of the radio-monitoring predictor against observed weather
  and, when available, measured optical-link quality.
- A routing-cost proposal that balances early failover with route stability.
- A documented comparison of potential optical uplink capacity with verified
  radio feeder-link capabilities.

Treat a study spanning only a few days as exploratory; it cannot establish
seasonal or annual service availability.

## Working guidance

Keep project documentation in English. Clearly separate the proposed design,
unverified assumptions, measured results, and externally verified facts.
Record sources and data provenance so that analyses can be reproduced.


## Gateway-only study scope

Use ground-to-satellite gateway sites for optical weather-screening studies.
Do not include internet Points of Presence (PoPs) as optical ground stations.
PoP coordinates retained in older exploratory artifacts are historical context
only. By default, exclude gateways reported as planned from availability
statistics; source claims of operational status remain unverified.

Persist per-gateway, per-timestamp cloud classifications in CSV, including UTC
and Europe/Warsaw timestamps, approximate coordinates, data provenance,
unknown data and mixed-cloud cases. Classify the categorical EUMETSAT cloud
mask rather than interpreting RGB image brightness. Use an infrared background
for multi-day animations so the background remains useful at night.

DSOC is a separate deep-space optical demonstration and an additional reference:
https://www.nasa.gov/mission/deep-space-optical-communications-dsoc/
The 200 Gbps LEO result cited for this project belongs to TBIRD, not DSOC.

## Public project description

Use README.md as the main public-facing project narrative, in English.
Preserve the founder's 60 GHz / 5 GHz field experience as an attributed,
self-reported motivation rather than independently verified experimental data.
Treat gateway bottlenecks and a 100 Gbps optical uplink as hypotheses/design
targets. Do not infer a Starlink data rate from terrestrial radio equipment or
carrier frequency alone, and do not claim zero laser propagation delay.
The 6-8 November weather window is an autumn case study, not a demonstrated
worst-case season. Cloud-free gateway counts are not confirmed optical links.
For gateway-count chronology plots, use time on X (horizontal) and gateway count on Y (vertical).

## Punctuation

Do not use long dashes: em dashes (Unicode U+2014) and en dashes (Unicode U+2013)
are prohibited in authored documentation, plot labels and user-facing text.
Use the ordinary ASCII hyphen (-), commas, colons or parentheses instead.
Preserve original source documents and downloaded datasets unchanged.

## README language and predictive routing

Keep the README in clear, technical English at approximately B2 level.
Use short sentences and explain specialised terms when they first appear.
Preserve the user's edits and chosen structure while correcting mistakes.
The controller must aim to raise optical path costs before a predicted weather
outage, with enough time to prepare a viable alternative and move traffic.
The current monitoring proposal is a two-dimensional honeycomb with a central
gateway and two surrounding rings. Compare an outer and an inner site in each
of six main directions. The 19-cell drawing is illustrative, not a fixed site count. An outer-site fade followed by
an inner-site fade is a hypothesis for approaching weather, to be checked
against satellite data and measured optical performance. It has not been
tested by the cloud-only study. Six antennas remain an initial hardware idea;
their mapping to the monitoring sites is not a final design.

Honeycomb diagrams must show adjoining hexagonal cells in two dimensions,
not a single row of hexagonal flowchart nodes. Use actual site coordinates
for analysis; the regular cell layout is a conceptual monitoring pattern.

Use a Mermaid fenced block in README.md for the honeycomb diagram. Use a
two-dimensional block layout with staggered rows of 3, 4, 5, 4 and 3 hexagons.
Keep the SVG as an optional export, not the primary embedded diagram.

## Concept status

Present Świetlik as an untested research idea throughout the README and new
project documentation. Use conditional wording for the proposed optical
network, predictive controller, honeycomb monitoring and capacity goals.
The existing scripts provide an exploratory cloud-data analysis only. They
do not validate optical availability, the radio warning hypothesis or traffic
switching. Keep actual analysis outputs and externally demonstrated results
(such as NASA TBIRD) factual, and clearly separate them from this proposal.

## Author voice

Write personal experience and motivation in README.md in the user's first-person
voice (I, my), as if the user wrote it. Do not describe the user as "the founder"
or "the author". Keep reported experience distinct from measured project results.

Use the same first-person singular voice for project ideas, assumptions,
choices, analysis descriptions and future plans throughout README.md, not
only for personal history. Prefer I/my to we/our or third-person narration.
Keep general technical facts, third-party results and diagram labels neutral.
