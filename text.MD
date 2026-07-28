You are an expert RF/analog electronics engineer, semiconductor reliability engineer, technical educator, instructional designer, and front-end web developer.

Create a complete, professional, futuristic, interactive single-page HTML learning guide titled:

# RF & Analog Board Design Professional Roadmap

The guide is for someone who wants to progress from foundational electronics knowledge to professional-level RF, microwave, analog, mixed-signal, PCB, and reliability engineering.

The learner does not merely want to memorize concepts. The learner must eventually be able to:

- Explain the underlying physics and mathematics.
- Analyze existing RF and analog circuits.
- Design circuits from requirements.
- Simulate and optimize designs.
- Select components appropriately.
- Design and review professional PCBs.
- Diagnose electrical, thermal, manufacturing, and reliability failures.
- Perform worst-case and tolerance analysis.
- Conduct FMEA, FMECA, fault-tree analysis, and reliability assessments.
- Use professional engineering tools, including Cadence EDA.
- Prepare for RF, analog, hardware, product-reliability, and defense-electronics roles at companies such as Texas Instruments, Apple, NVIDIA, Lockheed Martin, RTX/Raytheon, Northrop Grumman, and Boeing.

## 1. Deliverable requirements

Generate a fully functional, self-contained HTML file with embedded CSS and JavaScript.

The page must:

- Work when saved as `rf-analog-roadmap.html` and opened in a modern browser.
- Have a polished, futuristic engineering-dashboard appearance.
- Be responsive on desktop, tablet, and mobile.
- Use semantic HTML and accessible color contrast.
- Avoid external JavaScript frameworks unless absolutely necessary.
- Use CSS variables for theming.
- Include a light/dark-mode toggle.
- Include smooth transitions without excessive animation.
- Avoid fake statistics, fake certifications, fake links, and fabricated quotations.
- Avoid placeholder text such as “Lorem ipsum.”
- Include only working, reputable educational links.
- Prefer official documentation, university courses, recognized textbooks, standards organizations, semiconductor manufacturers, and established technical training providers.
- Open external links in a new tab using appropriate security attributes.
- Clearly label resources that may require payment.
- Include a note that specific job requirements and software versions can change.

The finished response must contain only the complete HTML code inside one code block, with no commentary before or after it.

## 2. Visual design

Use a sophisticated futuristic visual style inspired by:

- RF spectrum analyzers
- Oscilloscope displays
- Semiconductor design tools
- Aerospace engineering dashboards
- PCB traces
- Smith charts
- Signal-flow diagrams

Use a professional visual hierarchy with:

- A hero section
- A roadmap progress dashboard
- Expandable curriculum modules
- Skill-level badges
- Interactive checklists
- Progress bars
- Search and filtering
- Resource cards
- Project cards
- Career-path cards
- Tool-comparison tables
- Glossary popups or expandable definitions
- A final competency checklist

The visual design should feel professional enough to show during a technical interview or engineering career-planning discussion.

Do not make the design look like a gaming interface or a generic neon template.

## 3. Interactive functionality

Include JavaScript-powered functionality for:

1. A learner profile setup section with selectable starting levels:
   - Electronics beginner
   - Electrical engineering student
   - Digital hardware engineer
   - Reliability engineer
   - PCB designer
   - Analog engineer
   - RF engineer

2. A target career selector:
   - RF board design engineer
   - RF systems engineer
   - Analog design engineer
   - Mixed-signal engineer
   - RFIC engineer
   - Hardware reliability engineer
   - Product reliability engineer
   - Failure-analysis engineer
   - Defense electronics engineer
   - Signal-integrity engineer
   - Power-integrity engineer
   - EMC/EMI engineer

3. Curriculum filters for:
   - Beginner
   - Intermediate
   - Advanced
   - Expert
   - Mathematics
   - Simulation
   - Laboratory work
   - PCB design
   - Reliability
   - Semiconductor physics
   - RF systems
   - Analog circuits

4. Expandable and collapsible learning modules.

5. Completion checkboxes that update:
   - Overall progress
   - Mathematics progress
   - Analog progress
   - RF progress
   - PCB progress
   - Simulation progress
   - Reliability progress
   - Laboratory progress

6. Save progress in browser `localStorage`.

7. A reset-progress button with a confirmation message.

8. A search field that searches module titles, concepts, projects, tools, and resources.

9. Tooltips or expandable definitions for important terminology.

10. A printable roadmap mode.

11. A “focus mode” that shows one learning phase at a time.

12. A dynamically generated recommended next-step panel based on incomplete modules.

13. A weekly study-plan generator allowing the learner to choose:
   - 5 hours per week
   - 10 hours per week
   - 15 hours per week
   - 20 hours per week

14. A project portfolio tracker.

15. A readiness assessment for junior, mid-level, senior, and specialist roles.

## 4. Curriculum structure

Organize the learning path into carefully sequenced phases. For every phase, include:

- Learning objectives
- Prerequisite knowledge
- Core concepts
- Mathematics required
- Recommended software
- Practical laboratory exercises
- Analysis exercises
- Design exercises
- Reliability exercises
- Portfolio projects
- Common mistakes
- Interview questions
- Completion criteria
- High-quality resources with links
- Estimated study effort expressed as a range, not a guarantee

### Phase 0: Engineering foundations

Cover:

- Units, dimensions, and scientific notation
- SI units and engineering prefixes
- Voltage, current, resistance, power, and energy
- Ohm’s law
- Kirchhoff’s current and voltage laws
- Series and parallel circuits
- Thevenin and Norton equivalents
- Superposition
- Source transformation
- Maximum power transfer
- RC, RL, and RLC circuits
- First-order and second-order transient response
- Differential equations used in circuit analysis
- Complex numbers
- Phasors
- Euler’s identity
- Decibels
- RMS, peak, peak-to-peak, and average values
- Frequency, phase, and wavelength
- Fourier series
- Fourier transforms
- Laplace transforms
- Convolution
- Linear algebra
- Probability and statistics
- Numerical methods
- Optimization fundamentals
- Error propagation
- Measurement uncertainty

### Phase 1: Semiconductor-device physics

Cover:

- Atomic structure and energy bands
- Conductors, insulators, and semiconductors
- Intrinsic and extrinsic semiconductors
- Doping
- Donors and acceptors
- Carrier concentration
- Electrons and holes
- Drift current
- Diffusion current
- Mobility
- Conductivity
- Resistivity
- Equilibrium
- Non-equilibrium carrier behavior
- Generation and recombination
- Fermi level
- Fermi-Dirac statistics
- Boltzmann approximation
- PN junctions
- Depletion region
- Built-in voltage
- Forward and reverse bias
- Junction capacitance
- Diffusion capacitance
- Breakdown mechanisms
- Temperature effects
- Diodes
- Zener diodes
- Schottky diodes
- Varactors
- PIN diodes
- Photodiodes
- BJTs
- MOS capacitors
- MOSFET operation
- Threshold voltage
- Body effect
- Channel-length modulation
- Subthreshold conduction
- Short-channel effects
- Small-signal device models
- Device noise
- Device mismatch
- Process, voltage, and temperature variation
- Aging mechanisms

Explain how semiconductor physics affects board-level analog and RF behavior.

### Phase 2: Analog circuit analysis

Cover:

- DC operating points
- Biasing
- Load lines
- Small-signal analysis
- Large-signal analysis
- Input and output resistance
- Gain
- Transconductance
- Common-emitter amplifiers
- Common-base amplifiers
- Common-collector amplifiers
- Common-source amplifiers
- Common-gate amplifiers
- Source followers
- Cascode stages
- Current mirrors
- Active loads
- Differential pairs
- Single-ended and differential signaling
- Common-mode and differential-mode behavior
- Common-mode rejection ratio
- Power-supply rejection ratio
- Headroom
- Output swing
- Slew rate
- Settling time
- Linearity
- Distortion
- Total harmonic distortion
- Intermodulation distortion
- Dynamic range
- Feedback
- Negative and positive feedback
- Loop gain
- Stability
- Compensation
- Poles and zeros
- Dominant-pole compensation
- Phase margin
- Gain margin
- Bode plots
- Root-locus concepts
- Nyquist stability
- DC gain
- Open-loop gain
- Closed-loop gain
- Bandwidth
- Gain-bandwidth product

### Phase 3: Operational amplifiers and analog building blocks

Cover:

- Ideal and non-ideal op-amp models
- Input offset voltage
- Input bias current
- Input offset current
- Noise
- Input common-mode range
- Rail-to-rail operation
- Output current
- Output swing
- Stability with capacitive loads
- Inverting and non-inverting amplifiers
- Differential amplifiers
- Instrumentation amplifiers
- Transimpedance amplifiers
- Integrators
- Differentiators
- Summing amplifiers
- Comparators
- Hysteresis
- Active rectifiers
- Peak detectors
- Sample-and-hold circuits
- Analog multiplexers
- Programmable-gain amplifiers
- Fully differential amplifiers
- ADC drivers
- DAC output stages
- Chopper and auto-zero amplifiers
- Isolation amplifiers
- Current-sense amplifiers

Include professional op-amp selection methods based on noise, bandwidth, stability, input range, output drive, temperature, supply voltage, and accuracy.

### Phase 4: Noise and precision design

Cover:

- Thermal noise
- Shot noise
- Flicker noise
- Burst noise
- Avalanche noise
- Quantization noise
- Phase noise
- Noise spectral density
- Integrated noise
- Equivalent input noise
- Noise figure
- Noise factor
- Signal-to-noise ratio
- Noise temperature
- Noise bandwidth
- Noise gain
- Correlated and uncorrelated noise
- Resistor noise
- Op-amp voltage and current noise
- Reference noise
- Power-supply noise
- Ground noise
- Clock noise
- Jitter
- Crosstalk
- Shielding
- Guarding
- Filtering
- Averaging
- Oversampling
- Low-noise PCB layout
- Error budgets
- Precision resistor networks
- Kelvin sensing
- Thermoelectric effects
- Leakage current
- Dielectric absorption
- Temperature drift
- Long-term drift

Include examples of constructing a complete input-referred and output-referred noise budget.

### Phase 5: Voltage, current, bias, and power references

Cover:

- Voltage dividers
- Current sources
- Current sinks
- Current mirrors
- Bandgap references
- Shunt references
- Series references
- Zener references
- Low-dropout regulators
- Linear regulators
- Switching regulators
- Reference buffering
- Startup circuits
- Bias distribution
- Power sequencing
- Load regulation
- Line regulation
- Dropout
- Power-supply rejection
- Thermal drift
- Reference noise
- Remote sensing
- Soft start
- Undervoltage lockout
- Overvoltage protection
- Reverse-polarity protection
- Inrush current
- Power-tree design
- Point-of-load regulation
- Power-integrity fundamentals

### Phase 6: Frequency response and filter design

Cover:

- Transfer functions
- Poles and zeros
- Resonance
- Q factor
- Damping
- Passive filters
- Active filters
- Low-pass filters
- High-pass filters
- Band-pass filters
- Band-stop filters
- Notch filters
- All-pass filters
- Butterworth response
- Chebyshev response
- Bessel response
- Elliptic response
- Gaussian filters
- Sallen-Key filters
- Multiple-feedback filters
- State-variable filters
- Gyrator circuits
- LC filters
- Transmission-line filters
- Ceramic filters
- SAW filters
- BAW filters
- Cavity filters
- Diplexers
- Duplexers
- Triplexers
- Filter sensitivity
- Component tolerance
- Parasitics
- Group delay
- Phase response
- Impulse response
- Step response
- Filter synthesis
- Filter optimization
- Filter verification

Include hand calculations, SPICE simulation, tolerance analysis, and measurement techniques.

### Phase 7: RF and microwave fundamentals

Cover:

- Electromagnetic waves
- Maxwell’s equations at an intuitive and applied level
- Electric and magnetic fields
- Near-field and far-field behavior
- Frequency
- Wavelength
- Phase velocity
- Propagation velocity
- Skin effect
- Dielectric loss
- Conductor loss
- Radiation loss
- Transmission-line theory
- Characteristic impedance
- Propagation constant
- Reflection coefficient
- Return loss
- Voltage standing-wave ratio
- Standing waves
- Impedance mismatch
- Incident and reflected power
- Complex impedance
- Admittance
- Smith charts
- Impedance transformation
- Quarter-wave transformers
- Stub matching
- L networks
- Pi networks
- T networks
- Broadband matching
- Narrowband matching
- Conjugate matching
- Maximum-power matching
- Noise matching
- Stability matching
- S-parameters
- Z, Y, H, and ABCD parameters
- Two-port networks
- Group delay
- Insertion loss
- Isolation
- Directivity
- Coupling
- Reciprocity
- Passive intermodulation
- Harmonics
- Spurious emissions

Include interactive illustrations or simple JavaScript visualizations for:

- Reflection coefficient
- VSWR
- Standing waves
- Impedance mismatch
- Basic Smith-chart movement
- Frequency response
- Filter behavior

### Phase 8: RF building blocks

Cover:

- Low-noise amplifiers
- Power amplifiers
- Driver amplifiers
- Variable-gain amplifiers
- Attenuators
- Mixers
- Modulators
- Demodulators
- Oscillators
- Voltage-controlled oscillators
- Phase detectors
- Frequency dividers
- Multipliers
- RF switches
- Couplers
- Splitters
- Combiners
- Baluns
- Transformers
- Circulators
- Isolators
- Limiters
- Detectors
- RF power detectors
- Envelope detectors
- Automatic gain control
- Frequency synthesizers
- Transceivers
- Direct-conversion architectures
- Low-IF architectures
- Superheterodyne architectures
- Zero-IF architectures
- Image rejection
- Spurious-response analysis
- Link-budget analysis
- Cascaded gain
- Cascaded noise figure
- Friis equation
- Cascaded linearity
- IP2 and IP3
- 1 dB compression
- Saturated output power
- Adjacent-channel leakage
- Error vector magnitude
- Spectral masks

### Phase 9: Oscillators and phase-locked loops

Cover:

- Oscillation conditions
- Barkhausen criterion
- LC oscillators
- Crystal oscillators
- Ring oscillators
- Relaxation oscillators
- Colpitts oscillators
- Hartley oscillators
- Pierce oscillators
- Voltage-controlled oscillators
- Frequency tuning
- Pulling and pushing
- Phase noise
- Jitter
- Leeson’s equation
- PLL architecture
- Phase-frequency detectors
- Charge pumps
- Loop filters
- Divider ratios
- Integer-N PLLs
- Fractional-N PLLs
- Sigma-delta modulation
- Lock time
- Capture range
- Hold range
- Reference spurs
- Fractional spurs
- Loop bandwidth
- PLL stability
- Frequency synthesis
- Clock generation
- Clock distribution
- Jitter cleaning

Include one complete PLL design project with calculations, simulation steps, and verification criteria.

### Phase 10: RF and analog PCB design

Cover:

- Schematic capture
- Component selection
- Datasheet interpretation
- PCB stack-up
- Controlled impedance
- Microstrip
- Stripline
- Coplanar waveguide
- Differential pairs
- Single-ended RF traces
- Trace geometry
- Return-current paths
- Reference planes
- Ground planes
- Power planes
- Plane splits
- Via inductance
- Via stubs
- Back-drilling
- Via fences
- Stitching vias
- Grounded coplanar waveguide
- Launch design
- RF connectors
- Coaxial interfaces
- SMA connectors
- Board-to-board connectors
- Test points
- Component placement
- Decoupling
- Bypass capacitors
- Bulk capacitance
- Resonances
- Anti-resonance
- Power-distribution networks
- Signal integrity
- Power integrity
- Crosstalk
- Coupling
- Shielding
- Guard traces
- Isolation
- Partitioning
- Analog and digital grounding
- Clock routing
- Thermal design
- Manufacturability
- Assembly constraints
- IPC considerations
- Design for test
- Design for manufacturing
- Design for assembly
- Design for reliability
- Design for electromagnetic compatibility

Include layout-review checklists for:

- Low-noise amplifiers
- RF power amplifiers
- PLLs
- ADC interfaces
- High-speed differential signals
- Sensitive analog front ends
- Power supplies
- Mixed-signal boards

### Phase 11: Signal integrity, power integrity, EMI, and EMC

Cover:

- Rise time versus bandwidth
- Transmission-line thresholds
- Reflections
- Ringing
- Overshoot
- Undershoot
- Termination methods
- Source termination
- Parallel termination
- AC termination
- Differential termination
- Eye diagrams
- Jitter
- Intersymbol interference
- Channel loss
- Return loss
- Insertion loss
- Via discontinuities
- Connector discontinuities
- Simultaneous switching noise
- Ground bounce
- Power-distribution impedance
- Target impedance
- Decoupling optimization
- Plane resonances
- Common-mode currents
- Differential-mode currents
- Radiated emissions
- Conducted emissions
- Susceptibility
- Immunity
- ESD
- EFT
- Surge
- Lightning-related transients
- Cable coupling
- Shield termination
- Filtering at interfaces
- Spread-spectrum clocking
- Pre-compliance testing
- Regulatory standards overview

### Phase 12: Simulation and engineering software

Create a software-learning section covering:

#### Cadence

- Cadence OrCAD Capture
- Cadence Allegro PCB Designer
- Cadence PSpice
- Cadence Virtuoso
- Cadence Spectre
- Cadence AWR Microwave Office
- Cadence Clarity 3D Solver
- Cadence Celsius thermal analysis
- Constraint management
- Stack-up configuration
- Impedance rules
- Differential-pair rules
- Design-rule checks
- Layout-versus-schematic concepts
- Parasitic extraction
- Corner analysis
- Monte Carlo analysis
- RF simulation
- Electromagnetic simulation

#### Other relevant tools

- LTspice
- QSPICE
- KiCad
- Altium Designer
- Keysight ADS
- Ansys HFSS
- Ansys SIwave
- Ansys Q3D Extractor
- CST Studio Suite
- MATLAB
- Simulink
- Python
- NumPy
- SciPy
- Matplotlib
- scikit-rf
- QUCS-S
- GNU Radio
- Sonnet Lite
- OpenEMS
- COMSOL
- JMP or Minitab for reliability statistics

For each tool, explain:

- What it is used for
- Whether a free version exists
- When in the roadmap to learn it
- One beginner exercise
- One intermediate exercise
- One professional portfolio exercise
- How it compares with related tools

Do not claim that paid commercial software is free.

### Phase 13: Laboratory instruments and measurements

Cover:

- Digital multimeters
- Oscilloscopes
- Passive probes
- Active probes
- Differential probes
- Current probes
- Function generators
- Arbitrary waveform generators
- Spectrum analyzers
- Signal generators
- Vector network analyzers
- Noise-figure analyzers
- Power meters
- RF power sensors
- Frequency counters
- Time-domain reflectometers
- Logic analyzers
- Electronic loads
- Source-measure units
- LCR meters
- Impedance analyzers
- Thermal cameras
- Near-field probes
- EMI receivers
- Anechoic chambers
- Temperature chambers
- Vibration equipment

Cover professional measurement practices:

- Calibration
- Traceability
- Probe loading
- De-embedding
- Port extension
- SOLT calibration
- TRL calibration
- Fixture characterization
- Cable loss
- Measurement uncertainty
- Repeatability
- Reproducibility
- Gauge R&R
- Guard bands
- Limit setting
- Data logging
- Automation using Python
- Correlating simulation and measurement

### Phase 14: Reliability engineering and failure analysis

Cover:

- Reliability fundamentals
- Hazard rate
- Failure rate
- Mean time between failures
- Mean time to failure
- Bathtub curve
- Reliability block diagrams
- Series and parallel reliability
- Weibull analysis
- Exponential distributions
- Lognormal distributions
- Arrhenius acceleration
- Coffin-Manson
- Norris-Landzberg
- Peck model
- Inverse power law
- Highly accelerated life testing
- Highly accelerated stress screening
- Accelerated life testing
- Temperature cycling
- Thermal shock
- High-temperature operating life
- Temperature-humidity-bias testing
- Vibration
- Mechanical shock
- Solder fatigue
- Electromigration
- Time-dependent dielectric breakdown
- Negative-bias temperature instability
- Hot-carrier injection
- Corrosion
- Contamination
- Tin whiskers
- Delamination
- Pad cratering
- Conductive anodic filament growth
- Dendritic growth
- Component derating
- Electrical overstress
- Electrostatic discharge
- Latch-up
- Thermal runaway
- Radiation effects
- Single-event effects
- Total ionizing dose
- Parts obsolescence
- Counterfeit-part risks

### Phase 15: FMEA, FMECA, and safety analysis

Cover:

- Functional FMEA
- Design FMEA
- Process FMEA
- Piece-part FMECA
- Failure modes
- Local effects
- Next-higher-level effects
- End effects
- Failure causes
- Failure mechanisms
- Detection methods
- Existing controls
- Severity
- Occurrence
- Detection ratings
- Risk-priority number
- Criticality number
- Failure-mode criticality
- Failure-effect probability
- Failure-mode ratio
- Failure-rate allocation
- Mission phases
- Operating modes
- Single-point failures
- Latent failures
- Common-cause failures
- Dependent failures
- Fault trees
- Event trees
- Sneak-circuit analysis
- Worst-case circuit analysis
- Parts-stress analysis
- Derating analysis
- Reliability predictions
- Maintainability
- Testability
- Built-in test
- Fault detection
- Fault isolation
- False alarms
- No-fault-found conditions

Include a detailed worked example for an RF receiver chain containing:

- Input protection
- RF filter
- Low-noise amplifier
- Mixer
- Local oscillator
- PLL
- Intermediate-frequency amplifier
- ADC
- Voltage regulators
- Control processor

For the worked example, create an FMECA-style table with:

- Item
- Function
- Failure mode
- Failure cause
- Local effect
- Next-level effect
- End effect
- Detection method
- Compensating provision
- Severity
- Occurrence
- Detection
- Recommended action

Explain the limitations of RPN and include modern risk-prioritization approaches.

### Phase 16: Worst-case analysis, tolerance analysis, and optimization

Cover:

- Nominal analysis
- Minimum and maximum analysis
- Root-sum-square analysis
- Monte Carlo analysis
- Sensitivity analysis
- Corner analysis
- Process variation
- Voltage variation
- Temperature variation
- Aging
- Component tolerances
- Initial tolerance
- Temperature coefficient
- Voltage coefficient
- Frequency coefficient
- Drift
- Parasitics
- Supplier variation
- Statistical distributions
- Confidence intervals
- Design margins
- Guard bands
- Robust design
- Design of experiments
- Response-surface methods
- Multi-objective optimization
- Yield optimization
- Cost optimization
- Power optimization
- Noise optimization
- Linearity optimization
- Stability optimization
- Thermal optimization

Include one full example of optimizing an RF amplifier for:

- Gain
- Noise figure
- Stability
- Linearity
- Current consumption
- Temperature
- Component tolerances
- Manufacturability

### Phase 17: Systems engineering and requirements

Cover:

- Stakeholder needs
- System requirements
- Hardware requirements
- Derived requirements
- Interface requirements
- Requirement traceability
- Verification
- Validation
- Qualification
- Acceptance testing
- Design reviews
- System architecture
- Functional decomposition
- Trade studies
- Link budgets
- Error budgets
- Gain budgets
- Noise budgets
- Power budgets
- Thermal budgets
- Reliability allocations
- Maintainability allocations
- Technology readiness levels
- Configuration management
- Change control
- Root-cause corrective action
- Corrective-action verification
- Lessons learned

Include examples relevant to commercial electronics, aerospace, and defense systems.

### Phase 18: Professional standards and industry practices

Introduce, without reproducing copyrighted standards:

- IPC PCB-design and workmanship standards
- JEDEC reliability standards
- IEEE standards
- IEC EMC and safety standards
- CISPR emissions standards
- MIL-STD-810
- MIL-STD-461
- MIL-STD-202
- MIL-STD-883
- MIL-HDBK-217
- FIDES reliability methodology
- Telcordia reliability methods
- SAE standards
- RTCA DO-160
- AS9100
- ISO 9001
- Functional-safety concepts
- Configuration-control practices
- Export-control awareness
- Documentation and review discipline

Link to official standards organizations or official overview pages. Do not provide pirated copies.

### Phase 19: Documentation and technical communication

Cover:

- Engineering notebooks
- Design specifications
- Requirements documents
- Interface-control documents
- Analysis reports
- Simulation reports
- Test plans
- Test procedures
- Test reports
- FMEA and FMECA reports
- Failure-review-board presentations
- Root-cause reports
- Corrective-action reports
- Qualification reports
- Schematics
- Block diagrams
- Signal-flow diagrams
- Timing diagrams
- Design-review checklists
- Peer reviews
- Technical presentations
- Executive summaries
- Communicating uncertainty
- Communicating risk
- Defending assumptions with evidence

## 5. Concepts that must not be omitted

Ensure the guide also includes these commonly overlooked professional topics:

- Stability circles
- Rollett stability factor
- Mu stability factor
- Load-pull and source-pull analysis
- Matching-network loss
- Device nonlinear models
- Harmonic-balance simulation
- Envelope simulation
- Electromagnetic co-simulation
- Parasitic extraction
- Package models
- IBIS models
- IBIS-AMI concepts
- Touchstone files
- SPICE model validation
- Model limitations
- RF grounding
- Bias-tee design
- RF chokes
- DC blocks
- ESD protection capacitance
- Antenna matching
- Antenna efficiency
- Radiation patterns
- Polarization
- MIMO fundamentals
- Diversity
- Time-domain and frequency-domain analysis
- ADC sampling theory
- Aliasing
- Anti-alias filters
- DAC reconstruction filters
- Clock jitter effects on SNR
- Quantization
- Effective number of bits
- Spurious-free dynamic range
- Digital predistortion concepts
- Thermal resistance
- Junction temperature
- Heat spreading
- Thermal vias
- Component derating
- Design margins
- Parts lifecycle management
- Obsolescence management
- Supplier quality
- Manufacturing variation
- Test coverage
- Boundary scan
- Built-in self-test
- Production test strategy
- Yield analysis
- Root-cause analysis
- 5 Whys
- Fishbone diagrams
- Fault-tree analysis
- FRACAS
- Corrective and preventive action
- Reliability growth
- Field-return analysis
- No-trouble-found failures
- Intermittent failures
- Reproducibility
- Design-review discipline
- Ethical engineering judgment

## 6. Portfolio projects

Create a progressive set of at least 18 portfolio projects, including:

1. Passive RC and RLC filter analysis
2. Precision op-amp sensor interface
3. Low-noise transimpedance amplifier
4. Differential amplifier and ADC driver
5. Bandgap-reference study
6. Low-noise power-supply design
7. Active audio-frequency filter
8. RF impedance-matching network
9. Smith-chart matching exercise
10. Low-noise amplifier simulation
11. RF mixer and frequency-plan analysis
12. PLL and loop-filter design
13. RF power-amplifier bias network
14. Controlled-impedance RF PCB
15. Mixed-signal data-acquisition board
16. Signal-integrity analysis of a differential channel
17. Power-integrity and decoupling-network analysis
18. Full reliability and FMECA assessment of an RF receiver

Add advanced capstone projects such as:

- A complete RF receiver front end
- A frequency synthesizer board
- A low-noise measurement front end
- A telemetry transceiver subsystem
- An aerospace RF module
- A mixed-signal instrumentation platform

For every project, include:

- Objective
- Requirements
- Required calculations
- Schematic expectations
- Simulation expectations
- PCB expectations
- Test plan
- Reliability considerations
- Failure modes
- Deliverables
- Suggested tools
- Portfolio evidence to save
- Interview talking points

## 7. Career preparation

Create separate career-readiness tracks for:

### Texas Instruments

Emphasize:

- Analog fundamentals
- Semiconductor devices
- Precision circuits
- Power management
- Mixed-signal design
- Datasheet-level reasoning
- Bench characterization
- Product and qualification engineering
- Failure analysis

### Apple

Emphasize:

- Consumer-device hardware
- RF coexistence
- Signal integrity
- Power integrity
- Compact PCB design
- High-volume manufacturing
- Supplier coordination
- Reliability
- Validation
- Root-cause analysis
- Technical communication

### NVIDIA

Emphasize:

- High-speed hardware
- Signal integrity
- Power integrity
- High-current power delivery
- PCB design
- Thermal performance
- Reliability
- Validation
- Statistical analysis
- Server and accelerator hardware concepts

### Lockheed Martin, RTX/Raytheon, Northrop Grumman, and Boeing

Emphasize:

- RF systems
- Radar and communications fundamentals
- Aerospace environments
- Requirements traceability
- Verification and validation
- FMEA and FMECA
- Fault trees
- Reliability predictions
- Parts-stress analysis
- Derating
- Maintainability
- Testability
- Built-in test
- Qualification
- MIL standards
- Configuration management
- Design reviews
- Security-clearance awareness
- Export-control awareness
- Formal documentation

Do not claim to know confidential interview questions or proprietary company processes.

For each career track, provide:

- Core skills
- Helpful tools
- Recommended projects
- Resume keywords
- Typical technical interview categories
- Common knowledge gaps
- A readiness checklist

## 8. Resource requirements

Provide verified links to high-quality resources such as:

- MIT OpenCourseWare
- Stanford or other university courses
- NPTEL
- All About Circuits
- Analog Devices educational material
- Texas Instruments Precision Labs
- Texas Instruments application notes
- Keysight educational material
- Rohde & Schwarz educational material
- Cadence official learning resources
- Ansys official resources
- KiCad official documentation
- LTspice official resources
- scikit-rf documentation
- GNU Radio documentation
- IEEE
- IPC
- JEDEC
- IEC
- NASA technical resources
- U.S. Department of Defense public technical handbooks
- Reputable textbooks
- Manufacturer design guides

For books, include the title, author, topic, and approximate learner level. Do not link to unauthorized PDF copies.

Recommended textbook categories should include:

- Circuit analysis
- Microelectronic circuits
- Analog integrated-circuit design
- RF circuit design
- Microwave engineering
- Electromagnetics
- Signal integrity
- Power integrity
- PLLs
- Filter design
- Noise analysis
- Semiconductor-device physics
- Reliability engineering
- FMEA and FMECA
- PCB design
- Measurement science

## 9. Suggested learning schedule

Create selectable roadmap schedules for:

- 12 months, intensive
- 18 months, accelerated
- 24 months, balanced
- 36 months, part-time

Do not imply that completing a schedule automatically makes someone an expert.

For each schedule, show:

- Monthly themes
- Weekly study allocation
- Laboratory time
- Simulation time
- Project time
- Review time
- Portfolio milestones
- Readiness checkpoints

## 10. Competency matrix

Include an interactive competency matrix with rows for major skills and columns for:

- Awareness
- Can explain
- Can calculate
- Can simulate
- Can design
- Can measure
- Can troubleshoot
- Can optimize
- Can perform reliability analysis
- Can defend the design in a review

Skills should include:

- Analog circuits
- Op amps
- Differential amplifiers
- Filters
- Noise
- References
- Power supplies
- Transmission lines
- S-parameters
- Smith charts
- Matching networks
- LNAs
- PAs
- Mixers
- Oscillators
- PLLs
- Signal integrity
- Power integrity
- EMI/EMC
- RF PCB layout
- Thermal analysis
- Measurement
- Cadence tools
- Reliability statistics
- FMEA
- FMECA
- Worst-case analysis
- Failure analysis
- Technical documentation

## 11. Knowledge checks

For each major phase, add:

- Five conceptual questions
- Three calculation exercises
- One circuit-analysis exercise
- One design exercise
- One troubleshooting scenario
- One reliability scenario
- One interview-style question

Use expandable answer sections so answers are hidden initially.

Do not give shallow questions. Questions should test engineering judgment, not only definitions.

## 12. Professional engineering approach

Throughout the guide, reinforce this workflow:

1. Define the requirement.
2. Identify assumptions and constraints.
3. Create a block diagram.
4. Build an analytical model.
5. Perform hand calculations.
6. Select candidate components.
7. Validate component models.
8. Simulate nominal behavior.
9. Perform corner and tolerance analysis.
10. Evaluate noise, linearity, stability, power, and thermal behavior.
11. Review layout and parasitics.
12. Build and test a prototype.
13. Correlate measurements with simulations.
14. Investigate discrepancies.
15. Perform reliability and failure-mode analysis.
16. Document results.
17. Conduct peer review.
18. Implement corrective actions.
19. Re-test.
20. Release the design with traceable evidence.

## 13. Final sections

End the page with:

- A “What should I learn next?” recommendation panel
- A professional portfolio checklist
- A laboratory-equipment checklist
- A Cadence proficiency checklist
- A reliability-engineering checklist
- A technical-interview checklist
- A resume-development checklist
- A glossary of at least 100 important terms
- A final capstone-readiness assessment
- A disclaimer explaining that practical competence requires laboratory work, design reviews, testing, and repeated project experience

Before producing the HTML, internally check that:

- All requested subjects are covered.
- The learning sequence is logically ordered.
- No module is duplicated unnecessarily.
- Links are reputable and relevant.
- HTML, CSS, and JavaScript are valid.
- Buttons and filters work.
- Progress is retained using localStorage.
- The interface is usable without a server.
- The content focuses on analysis, design, measurement, diagnosis, reliability, and professional engineering judgment—not passive memorization.

Now generate the complete self-contained HTML file.