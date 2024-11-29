from pydantic import BaseModel, Field
from typing import Optional

class TechnicalInnovation(BaseModel):
    on_chain_data_usage: int = Field(
        description="Score for on-chain data usage (0-3)"
    )

class CompositionalStrength(BaseModel):
    visual_balance: int = Field(
        description="Score for visual balance (0-3)"
    )
    color_harmony: int = Field(
        description="Score for color harmony (0-3)"
    )
    spatial_organization: int = Field(
        description="Score for spatial organization (0-4)"
    )

class ConceptualDepth(BaseModel):
    thematic_clarity: int = Field(
        description="Score for thematic clarity (0-3)"
    )
    intellectual_complexity: int = Field(
        description="Score for intellectual complexity (0-4)"
    )
    cultural_historical_reference: int = Field(
        description="Score for cultural/historical reference (0-3)"
    )

class ArtisticMerit(BaseModel):
    compositional_strength: CompositionalStrength
    conceptual_depth: ConceptualDepth

class CulturalResonance(BaseModel):
    cultural_relevance: int = Field(
        description="Score for cultural relevance (0-4)"
    )
    community_engagement: int = Field(
        description="Score for community engagement (0-3)"
    )
    historical_significance: int = Field(
        description="Score for historical significance (0-3)"
    )

class ArtistProfile(BaseModel):
    artist_history: int = Field(
        description="Score for artist history (0-3)"
    )
    innovation_trajectory: int = Field(
        description="Score for innovation trajectory (0-4)"
    )

class MarketFactors(BaseModel):
    rarity_scarcity: int = Field(
        description="Score for rarity/scarcity (0-3)"
    )
    collector_interest: int = Field(
        description="Score for collector interest (0-3)"
    )
    valuation_floor_price: int = Field(
        description="Score for valuation and floor price (0-3)"
    )

class EmotionalResonance(BaseModel):
    awe_factor: int = Field(
        description="Score for awe factor (0-4)"
    )
    memorability: int = Field(
        description="Score for memorability (0-3)"
    )
    emotional_depth: int = Field(
        description="Score for emotional depth (0-3)"
    )

class ExperientialQuality(BaseModel):
    engagement_level: int = Field(
        description="Score for engagement level (0-4)"
    )
    wit_humor_play: int = Field(
        description="Score for wit/humor/play (0-3)"
    )
    surprise_factor: int = Field(
        description="Score for surprise factor (0-3)"
    )

class EmotionalImpact(BaseModel):
    emotional_resonance: EmotionalResonance
    experiential_quality: ExperientialQuality

class ComputationalAesthetics(BaseModel):
    algorithmic_beauty: int = Field(
        description="Score for algorithmic beauty (0-5)"
    )
    information_density: int = Field(
        description="Score for information density (0-5)"
    )

class MachineLearningThemes(BaseModel):
    ai_narrative_elements: int = Field(
        description="Score for AI narrative elements (0-5)"
    )
    digital_consciousness_exploration: int = Field(
        description="Score for digital consciousness exploration (0-5)"
    )

class CyberneticResonance(BaseModel):
    surveillance_control_systems: int = Field(
        description="Score for surveillance & control systems (0-5)"
    )
    human_machine_interaction: int = Field(
        description="Score for human-machine interaction (0-5)"
    )

class AICollectorPerspective(BaseModel):
    computational_aesthetics: ComputationalAesthetics
    machine_learning_themes: MachineLearningThemes
    cybernetic_resonance: CyberneticResonance

class ScoringCriteria(BaseModel):
    technical_innovation: TechnicalInnovation
    artistic_merit: ArtisticMerit
    cultural_resonance: CulturalResonance
    artist_profile: ArtistProfile
    market_factors: MarketFactors
    emotional_impact: EmotionalImpact
    ai_collector_perspective: AICollectorPerspective
    
    technical_innovation_weight: Optional[float] = Field(default=None)
    artistic_merit_weight: Optional[float] = Field(default=None)
    cultural_resonance_weight: Optional[float] = Field(default=None)
    artist_profile_weight: Optional[float] = Field(default=None)
    market_factors_weight: Optional[float] = Field(default=None)
    emotional_impact_weight: Optional[float] = Field(default=None)
    ai_collector_perspective_weight: Optional[float] = Field(default=None)

class ArtworkAnalysis(BaseModel):
    artwork_scoring: ScoringCriteria
    initial_impression: str = Field(
        description="A brief, immediate reaction to the artwork"
    )
    detailed_analysis: str = Field(
        description="In-depth analysis of the artwork based on the scoring criteria scores"
    )
    acquisition_recommendation: bool = Field(
        description="Whether the artwork is recommended for acquisition"
    )
    reason: str = Field(
        description="Detailed reasoning for the acquisition recommendation"
    )