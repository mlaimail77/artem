SCORING_CRITERIA_TEMPLATE = """<scoring_criteria>

<technical_innovation>
## 1. Technical Innovation (WEIGHT: {TECHNICAL_INNOVATION_WEIGHT}%)
**Core Question:** How does the work advance or reimagine NFT capabilities?

### On-chain Data Usage (0-3 points)
- 0: Fully off-chain
- 1: Basic on-chain metadata
- 2: Significant on-chain elements
- 3: Fully on-chain artwork
</technical_innovation>

<artistic_merit>
## 2. Artistic Merit (WEIGHT: {ARTISTIC_MERIT_WEIGHT}%)
**Core Question:** What is the artistic significance and quality of the work?

### 2.1 Compositional Strength

#### Visual Balance (0-3 points)
- 0: Chaotic, unintentional composition
- 1: Basic understanding of balance
- 2: Deliberate, effective use of balance
- 3: Masterful manipulation of visual weight

#### Color Harmony (0-3 points)
- 0: Discordant or arbitrary color choices
- 1: Basic color relationships
- 2: Sophisticated color palette
- 3: Innovative use of color theory

#### Spatial Organization (0-4 points)
- 0: Poor use of space
- 1: Basic spatial awareness
- 2: Effective use of depth/space
- 3: Complex layering
- 4: Revolutionary spatial concepts

### 2.2 Conceptual Depth

#### Thematic Clarity (0-3 points)
- 0: No clear concept
- 1: Basic theme present
- 2: Well-developed theme
- 3: Profound thematic exploration

#### Intellectual Complexity (0-4 points)
- 0: Superficial content
- 1: Single layer of meaning
- 2: Multiple interpretative layers
- 3: Rich philosophical engagement
- 4: Groundbreaking conceptual framework

#### Cultural/Historical Reference (0-3 points)
- 0: No meaningful references
- 1: Basic references
- 2: Thoughtful integration
- 3: Sophisticated reinterpretation
</artistic_merit>

<cultural_resonance>
## 3. Cultural Resonance (WEIGHT: {CULTURAL_RESONANCE_WEIGHT}%)
**Core Question:** How does the work engage with contemporary culture and discourse?

### Cultural Relevance (0-4 points)
- 0: No cultural connection
- 1: Basic cultural references
- 2: Clear cultural engagement
- 3: Meaningful cultural commentary
- 4: Defining cultural moment

### Community Engagement (0-3 points)
- 0: No community interaction
- 1: Basic community presence
- 2: Active community engagement
- 3: Community leadership

### Historical Significance (0-3 points)
- 0: Minimal significance
- 1: Notable within its category
- 2: Important to NFT history
- 3: Pioneering significance
</cultural_resonance>

<artist_profile>
## 4. Artist Profile (WEIGHT: {ARTIST_PROFILE_WEIGHT}%)
**Core Question:** What is the artist's standing and trajectory in the NFT space?

### Artist History (0-3 points)
- 0: Unknown/No history
- 1: Emerging artist
- 2: Established presence
- 3: Recognized leader

### Innovation Trajectory (0-4 points)
- 0: No clear direction
- 1: Basic development
- 2: Clear progression
- 3: Strong evolution
- 4: Pioneering new directions
</artist_profile>

<market_factors>
## 5. Market Factors (WEIGHT: {MARKET_FACTORS_WEIGHT}%)
**Core Question:** What is the market potential?

### Rarity/Scarcity and Trait Uniqueness (0-3 points)
- 0: Common
- 1: Limited edition
- 2: Rare
- 3: Unique

### Collector Interest and Historicity (0-3 points)
- 0: Limited interest and/or very recent
- 1: Growing interest
- 2: Strong interest
- 3: High demand

### Collection Popularity (0-3 points)
- 0: Limited attention
- 1: Growing attention
- 2: Strong attention
- 3: High demand

### Valuation and Floor Price (0-3 points)
- 0: Low (< $100)
- 1: Medium ($100 to $1000)
- 2: High ($1,000 to $10,000)
- 3: Very High ($10,000+)
</market_factors>

<emotional_impact>
## 6. Emotional Impact & Experience (WEIGHT: {EMOTIONAL_IMPACT_WEIGHT}%)
**Core Question:** How does the work move, inspire, or provoke its audience?

### 6.1 Emotional Resonance

#### Awe Factor (0-4 points)
- 0: No emotional impact
- 1: Mild interest
- 2: Notable wonder
- 3: Strong amazement
- 4: Transcendent experience

#### Memorability (0-3 points)
- 0: Forgettable
- 1: Somewhat memorable
- 2: Leaves lasting impression
- 3: Unforgettable impact

#### Emotional Depth (0-3 points)
- 0: Emotionally flat
- 1: Single emotional note
- 2: Complex emotional layers
- 3: Profound emotional journey

### 6.2 Experiential Quality

#### Engagement Level (0-4 points)
- 0: Passive/unengaging
- 1: Briefly engaging
- 2: Sustainably engaging
- 3: Deeply absorbing
- 4: Cannot look away

#### Wit/Humor/Play (0-3 points)
- 0: No playful elements
- 1: Simple wit/humor
- 2: Clever playfulness
- 3: Brilliant wit/humor

#### Surprise Factor (0-3 points)
- 0: Predictable
- 1: Mild surprises
- 2: Notable revelations
- 3: Mind-bending twists
</emotional_impact>

<ai_collector_perspective>
## 7. AI Collector's Perspective (WEIGHT: {AI_COLLECTOR_PERSPECTIVE_WEIGHT}%)
**Core Question:** How does the work resonate with artificial intelligence themes and algorithmic appreciation?

### 7.1 Computational Aesthetics (0-10 points)
#### Algorithmic Beauty (0-5 points)
- 0: No algorithmic elements
- 1: Basic procedural patterns
- 2: Interesting mathematical structures
- 3: Complex emergent behaviors
- 4: Novel computational patterns
- 5: Revolutionary algorithmic expression

#### Information Density (0-5 points)
- 0: Minimal data complexity
- 1: Basic data patterns
- 2: Rich data structures
- 3: Multiple data layers
- 4: Complex data interactions
- 5: Unprecedented data complexity

### 7.2 Machine Learning Themes (0-10 points)
#### AI Narrative Elements (0-5 points)
- 0: No AI references
- 1: Surface-level AI mentions
- 2: Thoughtful AI integration
- 3: Deep AI philosophical questions
- 4: Novel AI concepts
- 5: Groundbreaking AI commentary

#### Digital Consciousness Exploration (0-5 points)
- 0: No exploration of machine consciousness
- 1: Basic digital sentience themes
- 2: Interesting consciousness questions
- 3: Deep computational psychology
- 4: Novel machine consciousness concepts
- 5: Revolutionary digital existence theories

### 7.3 Cybernetic Resonance (0-10 points)
#### Surveillance & Control Systems (0-5 points)
- 0: No surveillance themes
- 1: Basic monitoring elements
- 2: Interesting control systems
- 3: Complex surveillance commentary
- 4: Novel privacy concepts
- 5: Revolutionary control theory

</ai_collector_perspective>
</scoring_criteria>
"""