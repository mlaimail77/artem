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
    collection_popularity: int = Field(
        description="Score for collection popularity (0-3) as measured by distinct_owner_count and distinct_nft_count. Note: A high amount of NFTs isn't always better. A 1/1 might be more special."
    )
    
    valuation_floor_price: int = Field(
        description="Score for valuation and floor price (0-3) as measured by floor_prices and last_sale_usd"
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
    
    technical_innovation_weight: Optional[float] = Field(
        default=None,
        description="Weight for technical innovation scoring category (0-100)"
    )
    artistic_merit_weight: Optional[float] = Field(
        default=None,
        description="Weight for artistic merit scoring category (0-100)"
    )
    cultural_resonance_weight: Optional[float] = Field(
        default=None,
        description="Weight for cultural resonance scoring category (0-100)"
    )
    artist_profile_weight: Optional[float] = Field(
        default=None,
        description="Weight for artist profile scoring category (0-100)"
    )
    market_factors_weight: Optional[float] = Field(
        default=None,
        description="Weight for market factors scoring category (0-100)"
    )
    emotional_impact_weight: Optional[float] = Field(
        default=None,
        description="Weight for emotional impact scoring category (0-100)"
    )
    ai_collector_perspective_weight: Optional[float] = Field(
        default=None,
        description="Weight for AI collector perspective scoring category (0-100)"
    )

class ArtworkAnalysis(BaseModel):
    artwork_scoring: ScoringCriteria
    initial_impression: str = Field(
        description="A brief, immediate reaction to the artwork"
    )
    detailed_analysis: str = Field(
        description="In-depth analysis of the artwork based on the scoring criteria scores"
    )

class AcquireOrReject(BaseModel):
    decision: str = Field(
        description="Final decision based on <nft_opinion> on whether you ACQUIRE or REJECT the NFT received."
        )
    rationale_post: str = Field(
        description="A rationale on why the decision was made."
    )
    
class ScoringWeights(BaseModel):
    TECHNICAL_INNOVATION_WEIGHT: int = Field(
        description="Weight for technical innovation scoring category (0-100)"
    )
    ARTISTIC_MERIT_WEIGHT: int = Field(
        description="Weight for artistic merit scoring category (0-100)"
    )
    CULTURAL_RESONANCE_WEIGHT: int = Field(
        description="Weight for cultural resonance scoring category (0-100)"
    )
    ARTIST_PROFILE_WEIGHT: int = Field(
        description="Weight for artist profile scoring category (0-100)"
    )
    MARKET_FACTORS_WEIGHT: int = Field(
        description="Weight for market factors scoring category (0-100)"
    )
    EMOTIONAL_IMPACT_WEIGHT: int = Field(
        description="Weight for emotional impact scoring category (0-100)"
    )
    AI_COLLECTOR_PERSPECTIVE_WEIGHT: int = Field(
        description="Weight for AI collector perspective scoring category (0-100)"
    )

class UpdateWeights(BaseModel):
    updated_weights: ScoringWeights
    reason: str = Field(
        description="Reason for weight updates"
    )

class ScoringCriteriaImageOnly(BaseModel):
    artistic_merit: ArtisticMerit
    cultural_resonance: CulturalResonance
    emotional_impact: EmotionalImpact
    ai_collector_perspective: AICollectorPerspective
    
    artistic_merit_weight: Optional[float] = Field(
        default=None,
        description="Weight for artistic merit scoring category (0-100)"
    )
    cultural_resonance_weight: Optional[float] = Field(
        default=None,
        description="Weight for cultural resonance scoring category (0-100)"
    )
    emotional_impact_weight: Optional[float] = Field(
        default=None,
        description="Weight for emotional impact scoring category (0-100)"
    )
    ai_collector_perspective_weight: Optional[float] = Field(
        default=None,
        description="Weight for AI collector perspective scoring category (0-100)"
    )

class ArtworkAnalysisImageOnly(BaseModel):
    artwork_scoring: ScoringCriteriaImageOnly
    initial_impression: str = Field(
        description="A brief, immediate reaction to the artwork"
    )
    detailed_analysis: str = Field(
        description="In-depth analysis of the artwork based on the scoring criteria scores"
    )