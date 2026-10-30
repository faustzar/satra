import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class SpeciesTaxonomy(Base):
    __tablename__ = "species_taxonomy"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scientific_name = Column(String(100), unique=True, nullable=False, index=True)
    common_name = Column(String(100), nullable=False)
    family = Column(String(50), default="Testudinidae")
    genus = Column(String(50), nullable=False)
    iucn_status = Column(String(10), default="LC")  # CR, EN, VU, NT, LC
    pivotal_temp_c = Column(Float, default=30.8)   # TSD Pivotal Temperature

    specimens = relationship("SpeciesTaxonomy", back_populates="taxonomy") if False else relationship("Specimen", back_populates="taxonomy")


class Specimen(Base):
    __tablename__ = "specimens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    custom_identifier = Column(String(50), unique=True, nullable=False, index=True)
    species_id = Column(String(36), ForeignKey("species_taxonomy.id"), nullable=True)
    species_name = Column(String(100), nullable=False)
    common_name = Column(String(100), nullable=False)
    pit_tag_number = Column(String(50), index=True, nullable=True)
    notch_code = Column(String(50), nullable=True)
    sex = Column(String(20), default="Undetermined")  # Male | Female | Juvenile | Undetermined
    status = Column(String(30), default="Wild")       # Wild | Intake | InRehab | Breeding | Deceased | Released
    primary_photo_id = Column(String(36), nullable=True)

    # Studbook Pedigree
    dam_id = Column(String(36), ForeignKey("specimens.id"), nullable=True)
    sire_id = Column(String(36), ForeignKey("specimens.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    taxonomy = relationship("SpeciesTaxonomy", back_populates="specimens")
    sightings = relationship("Sighting", back_populates="specimen", cascade="all, delete-orphan")
    inspections = relationship("HealthInspection", back_populates="specimen", cascade="all, delete-orphan")
    photos = relationship("PhotoRecord", back_populates="specimen", cascade="all, delete-orphan")


class Sighting(Base):
    __tablename__ = "sightings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    specimen_id = Column(String(36), ForeignKey("specimens.id"), nullable=True, index=True)
    
    # Coordinates (WGS84)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    horizontal_accuracy = Column(Float, default=5.0)
    
    habitat_type = Column(String(100), nullable=True)
    ambient_temp_c = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    observer_id = Column(String(50), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    specimen = relationship("Specimen", back_populates="sightings")


class HealthInspection(Base):
    __tablename__ = "health_inspections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    specimen_id = Column(String(36), ForeignKey("specimens.id"), nullable=False, index=True)
    inspection_type = Column(String(30), default="Scheduled")  # Intake | Scheduled | AdHoc | GravidCheck
    
    # Morphometrics (Matching Legacy AppSheet Spec)
    mass_grams = Column(Float, nullable=False)
    straight_carapace_length_mm = Column(Float, nullable=False)
    shell_width_mm = Column(Float, nullable=True)             # Width (SW)
    shell_height_mm = Column(Float, nullable=True)            # Height (SH)
    plastron_length_mm = Column(Float, nullable=True)         # Plastron Length
    plastron_width_mm = Column(Float, nullable=True)          # Plastron Width
    anal_opening_mm = Column(Float, nullable=True)            # Anal Opening
    anal_width_mm = Column(Float, nullable=True)              # Anal Width
    growth_rings = Column(String(50), nullable=True)          # Scute Laminae / Grow Rings
    body_condition_score = Column(Integer, default=3)         # 1 to 5
    
    # Loehr, Henen & Hofmeyr (2004) Condition & Biometric Metrics (Herpetologica 60:444-454)
    shell_volume_cm3 = Column(Float, nullable=True)          # V_fem = pi * SCL * SH * SW / 6000 (cm3)
    body_condition_index = Column(Float, nullable=True)      # BCI = Mass / V_fem (g/cm3, baseline 1.12)
    mass_to_scl_ratio = Column(Float, nullable=True)         # Mass / SCL (g/mm, baseline 1.62)
    
    # Gravidity, Egg Biometrics (Coleman 1991), Ultrasonography (POS) & Somatic Mass
    eggs_palpated = Column(Boolean, default=False)
    estimated_egg_count = Column(Integer, default=0)
    egg_length_mm = Column(Float, nullable=True)             # Radiographic / Ultrasound egg length
    egg_width_mm = Column(Float, nullable=True)              # Radiographic / Ultrasound egg width
    egg_volume_cm3 = Column(Float, nullable=True)            # V_egg = pi * L * W^2 / 6000 (cm3)
    somatic_mass_grams = Column(Float, nullable=True)        # Somatic Mass = Mass - Egg Mass - Follicle Mass

    # Loehr et al. (2004) Field Weighing, Scute Wear, Ultrasonography & Table 2 ANCOVA Regressions
    weighed_before_excretion = Column(Boolean, default=True) # Weighed prior to urine/fecal loss (±0.1 g)
    scute_wear_status = Column(String(40), nullable=True)    # Countable (8-13) | Worn / Old (>13 laminae)
    follicle_count = Column(Integer, nullable=True)          # Vitellogenic follicles counted via ultrasound (1-6)
    mean_follicle_diameter_mm = Column(Float, nullable=True) # Mean follicle diameter (mm, range 4.7-22.6 mm)
    follicle_volume_cm3 = Column(Float, nullable=True)       # V_foll = pi * d^3 / 6 (cm3 per follicle)
    pos_fraction = Column(Float, nullable=True)              # Fraction of Preovulatory Size (POS = 4.99 cm3)
    predicted_mass_grams = Column(Float, nullable=True)      # Table 2 ANCOVA expected mass (g)
    mass_condition_residual_g = Column(Float, nullable=True) # Observed Somatic/Total Mass - Predicted Mass (g)

    # Legacy Jackson ratio (kept for backward compatibility)
    jacksons_ratio = Column(Float, nullable=True)

    # Clinical findings & notes
    shell_condition_notes = Column(Text, nullable=True)
    observation_notes = Column(Text, nullable=True)
    symptoms_json = Column(JSON, nullable=True)
    
    # Geospatial Coordinates (Automatic GPS Fix)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_accuracy_m = Column(Float, nullable=True)

    inspected_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    specimen = relationship("Specimen", back_populates="inspections")


class BreedingPairing(Base):
    __tablename__ = "breeding_pairings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dam_id = Column(String(36), ForeignKey("specimens.id"), nullable=False)
    sire_id = Column(String(36), ForeignKey("specimens.id"), nullable=False)
    pairing_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    enclosure_or_gps = Column(String(100), nullable=True)
    courtship_behaviors = Column(Text, nullable=True)
    copulation_confirmed = Column(Boolean, default=False)

    clutches = relationship("Clutch", back_populates="pairing")


class Clutch(Base):
    __tablename__ = "clutches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    pairing_id = Column(String(36), ForeignKey("breeding_pairings.id"), nullable=True)
    dam_id = Column(String(36), ForeignKey("specimens.id"), nullable=False)
    clutch_code = Column(String(50), unique=True, nullable=False, index=True)
    oviposition_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    nest_latitude = Column(Float, nullable=True)
    nest_longitude = Column(Float, nullable=True)
    
    total_eggs = Column(Integer, default=1)
    viable_eggs = Column(Integer, default=1)
    incubation_mode = Column(String(20), default="Artificial")  # Artificial | InSitu
    target_incubation_temp_c = Column(Float, default=31.5)
    predicted_sex = Column(String(50), nullable=True)

    pairing = relationship("BreedingPairing", back_populates="clutches")
    eggs = relationship("EggRecord", back_populates="clutch", cascade="all, delete-orphan")


class EggRecord(Base):
    __tablename__ = "egg_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clutch_id = Column(String(36), ForeignKey("clutches.id"), nullable=False, index=True)
    egg_code = Column(String(50), unique=True, nullable=False)
    initial_mass_grams = Column(Float, nullable=True)
    length_mm = Column(Float, nullable=True)
    width_mm = Column(Float, nullable=True)
    fertility_status = Column(String(30), default="Viable")  # Fertile | Infertile | EarlyDeath | Viable
    
    pipping_date = Column(DateTime, nullable=True)
    emergence_date = Column(DateTime, nullable=True)
    neonate_specimen_id = Column(String(36), ForeignKey("specimens.id"), nullable=True)

    clutch = relationship("Clutch", back_populates="eggs")


class PhotoRecord(Base):
    __tablename__ = "photo_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    specimen_id = Column(String(36), ForeignKey("specimens.id"), nullable=True, index=True)
    inspection_id = Column(String(36), ForeignKey("health_inspections.id"), nullable=True)
    photo_type = Column(String(30), default="Carapace")  # Carapace | Plastron | Head | Caudal | Lateral | Injury | Candling
    cloud_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    is_primary_avatar = Column(Boolean, default=False)
    capture_context = Column(String(40), default="ResearchIntake")  # CitizenSpotted | ResearchIntake | ClinicalRounds | AdHoc
    markings_json = Column(JSON, nullable=True)  # List of pins: [{id, type, scute_landmark, x_pct, y_pct, label, schema_values}]
    exif_metadata = Column(JSON, nullable=True)  # Camera, GPS, perpendicularity angle
    feature_descriptors = Column(Text, nullable=True)    # Serialized scute keypoint descriptors
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    specimen = relationship("Specimen", back_populates="photos")
