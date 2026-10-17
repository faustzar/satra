from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Response, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import re
import logging
from sqlalchemy import func
import math

from app.db.session import get_db
from app.models.models import Specimen, Sighting, HealthInspection, BreedingPairing, Clutch, EggRecord, SpeciesTaxonomy
from app.services.recognition_service import biometric_catalog_service
from app.services.pdf_report_service import report_generator

logger = logging.getLogger(__name__)

api_router = APIRouter()

# --- Pydantic Schemas ---

class SpecimenBase(BaseModel):
    custom_identifier: str = Field(..., example="LEOP-2026-001")
    species_name: str = Field(..., example="Stigmochelys pardalis")
    common_name: str = Field(..., example="Leopard Tortoise")
    pit_tag_number: Optional[str] = Field(None, example="982000365829104")
    notch_code: Optional[str] = Field(None, example="L3-R2")
    sex: str = Field("Undetermined", example="Female")
    status: str = Field("Wild", example="InRehab")
    dam_id: Optional[str] = None
    sire_id: Optional[str] = None

class SpecimenResponse(SpecimenBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class SightingCreate(BaseModel):
    specimen_id: Optional[str] = None
    latitude: float = Field(..., example=-33.9249)
    longitude: float = Field(..., example=18.4241)
    horizontal_accuracy: Optional[float] = 4.5
    habitat_type: Optional[str] = "Succulent Karoo"
    ambient_temp_c: Optional[float] = 24.5
    notes: Optional[str] = "Healthy adult grazing near fynbos edge"
    observer_id: Optional[str] = "Ranger-04"

class HealthInspectionCreate(BaseModel):
    specimen_id: str
    inspection_type: str = "Scheduled"  # Intake | Scheduled | AdHoc | GravidCheck
    mass_grams: float = Field(..., example=151.4)
    straight_carapace_length_mm: float = Field(..., example=92.6)
    shell_width_mm: Optional[float] = Field(None, example=68.8)
    shell_height_mm: Optional[float] = Field(None, example=40.2)
    plastron_length_mm: Optional[float] = Field(None, example=85.0)
    plastron_width_mm: Optional[float] = None
    anal_opening_mm: Optional[float] = None
    anal_width_mm: Optional[float] = None
    growth_rings: Optional[str] = Field(None, example="10 laminae")
    scute_wear_status: Optional[str] = Field("Countable (8-13)", example="Countable (8-13)")
    weighed_before_excretion: bool = True
    body_condition_score: int = Field(3, ge=1, le=5)
    eggs_palpated: bool = False
    estimated_egg_count: Optional[int] = 0
    egg_length_mm: Optional[float] = None
    egg_width_mm: Optional[float] = None
    follicle_count: Optional[int] = None
    mean_follicle_diameter_mm: Optional[float] = None
    shell_condition_notes: Optional[str] = None
    observation_notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    inspected_at: Optional[datetime] = None

class HealthInspectionResponse(BaseModel):
    id: str
    specimen_id: str
    inspection_type: str
    mass_grams: float
    straight_carapace_length_mm: float
    shell_width_mm: Optional[float] = None
    shell_height_mm: Optional[float] = None
    plastron_length_mm: Optional[float] = None
    plastron_width_mm: Optional[float] = None
    anal_opening_mm: Optional[float] = None
    anal_width_mm: Optional[float] = None
    growth_rings: Optional[str] = None
    scute_wear_status: Optional[str] = None
    weighed_before_excretion: Optional[bool] = True
    body_condition_score: int
    shell_volume_cm3: Optional[float] = None
    body_condition_index: Optional[float] = None
    mass_to_scl_ratio: Optional[float] = None
    jacksons_ratio: Optional[float] = None
    eggs_palpated: bool
    estimated_egg_count: Optional[int] = 0
    egg_length_mm: Optional[float] = None
    egg_width_mm: Optional[float] = None
    egg_volume_cm3: Optional[float] = None
    follicle_count: Optional[int] = None
    mean_follicle_diameter_mm: Optional[float] = None
    follicle_volume_cm3: Optional[float] = None
    pos_fraction: Optional[float] = None
    somatic_mass_grams: Optional[float] = None
    predicted_mass_grams: Optional[float] = None
    mass_condition_residual_g: Optional[float] = None
    shell_condition_notes: Optional[str] = None
    observation_notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    inspected_at: datetime

    class Config:
        from_attributes = True

class BreedingPairingCreate(BaseModel):
    dam_id: str
    sire_id: str
    pairing_date: Optional[datetime] = None
    enclosure_or_gps: Optional[str] = "Enclosure B3"
    courtship_behaviors: Optional[str] = "Observed head-bobbing, mounting and vocalization"
    copulation_confirmed: bool = True

class EggRecordCreate(BaseModel):
    egg_code: Optional[str] = None
    initial_mass_grams: Optional[float] = Field(None, example=12.4)
    length_mm: Optional[float] = Field(None, example=34.6)
    width_mm: Optional[float] = Field(None, example=24.9)
    fertility_status: str = Field("Fertile", example="Fertile")  # Fertile | Infertile | EarlyDeath | Viable | Hatched
    pipping_date: Optional[datetime] = None
    emergence_date: Optional[datetime] = None
    neonate_specimen_id: Optional[str] = None

class EggRecordUpdate(BaseModel):
    initial_mass_grams: Optional[float] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    fertility_status: Optional[str] = None
    pipping_date: Optional[datetime] = None
    emergence_date: Optional[datetime] = None
    neonate_specimen_id: Optional[str] = None

class ClutchCreate(BaseModel):
    pairing_id: Optional[str] = None
    dam_id: str
    clutch_code: Optional[str] = None
    oviposition_date: Optional[datetime] = None
    nest_latitude: Optional[float] = None
    nest_longitude: Optional[float] = None
    total_eggs: int = Field(1, ge=1, le=30)
    viable_eggs: Optional[int] = None
    incubation_mode: str = Field("Artificial", example="Artificial")  # Artificial | InSitu
    target_incubation_temp_c: float = Field(31.5, example=31.5)
    predicted_sex: Optional[str] = None
    initial_egg_mass_grams: Optional[float] = Field(None, description="Optional default egg mass to auto-generate egg records")
    initial_egg_length_mm: Optional[float] = Field(None, description="Optional default egg length (mm) for Coleman volume")
    initial_egg_width_mm: Optional[float] = Field(None, description="Optional default egg width (mm) for Coleman volume")
    eggs: Optional[List[EggRecordCreate]] = None

class RecognitionMatch(BaseModel):
    specimen_id: str
    custom_identifier: str
    species: str
    common_name: Optional[str] = None
    confidence_score: float
    inlier_count: int = 0
    is_match: bool = False
    matched_scute_region: str = "Vertebral & Costal Scute Junctions"
    visualization_base64: Optional[str] = None

# --- Endpoints with Database Session ---

@api_router.get("/specimens", response_model=List[SpecimenResponse])
def get_specimens(db: Session = Depends(get_db)):
    """Retrieve all registered tortoises from database."""
    return db.query(Specimen).order_by(Specimen.created_at.desc()).all()

@api_router.post("/specimens", response_model=SpecimenResponse)
def create_specimen(specimen_in: SpecimenBase, db: Session = Depends(get_db)):
    """Register a new tortoise with unique identifier pattern and taxonomy."""
    existing = db.query(Specimen).filter(Specimen.custom_identifier == specimen_in.custom_identifier).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Specimen '{specimen_in.custom_identifier}' already exists.")

    new_record = Specimen(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        **specimen_in.model_dump()
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@api_router.get("/specimens/{specimen_id}", response_model=SpecimenResponse)
def get_specimen(specimen_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a single specimen."""
    specimen = db.query(Specimen).filter(Specimen.id == specimen_id).first()
    if not specimen:
        raise HTTPException(status_code=404, detail="Specimen not found")
    return specimen

@api_router.post("/sightings")
def record_sighting(sighting_in: SightingCreate, db: Session = Depends(get_db)):
    """Log a field sighting with geospatial location and habitat telemetry."""
    sighting = Sighting(
        id=str(uuid.uuid4()),
        recorded_at=datetime.utcnow(),
        **sighting_in.model_dump()
    )
    db.add(sighting)
    db.commit()
    db.refresh(sighting)
    return {
        "status": "success",
        "sighting_id": sighting.id,
        "recorded_at": sighting.recorded_at,
        "latitude": sighting.latitude,
        "longitude": sighting.longitude
    }

@api_router.get("/health-inspections", response_model=List[HealthInspectionResponse])
def get_health_inspections(specimen_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Retrieve observations / health assessments, optionally filtered by specimen."""
    query = db.query(HealthInspection)
    if specimen_id:
        query = query.filter(HealthInspection.specimen_id == specimen_id)
    return query.order_by(HealthInspection.inspected_at.desc()).all()

@api_router.post("/health-inspections")
def record_health_inspection(inspection_in: HealthInspectionCreate, db: Session = Depends(get_db)):
    """
    Record clinical health assessment and morphometrics evaluated under
    Loehr, Henen & Hofmeyr (2004) Herpetologica 60(4):444-454.
    """
    mass = inspection_in.mass_grams
    scl = inspection_in.straight_carapace_length_mm
    sh = inspection_in.shell_height_mm
    sw = inspection_in.shell_width_mm

    # 1. Linear Mass-to-SCL ratio (Loehr et al. 2004 Table 1: Mean 1.62 g/mm)
    mass_to_scl = round(mass / scl, 4) if scl and scl > 0 else None

    # 2. Ellipsoid Shell Volume (Vfem = pi * SCL * SH * SW / 6000 in cm3)
    shell_volume = None
    bci = None
    if scl and sh and sw and scl > 0 and sh > 0 and sw > 0:
        shell_volume = round((math.pi * scl * sh * sw) / 6000.0, 2)
        # Body Condition Index: Mass / Shell Volume (g/cm3) (Loehr et al. 2004 Table 1: Mean 1.12 g/cm3)
        if shell_volume > 0:
            bci = round(mass / shell_volume, 4)

    # 3. Egg volume (Coleman 1991 formula: pi * L * W^2 / 6000 in cm3)
    egg_volume = None
    egg_mass_estimate = 0.0
    el = inspection_in.egg_length_mm
    ew = inspection_in.egg_width_mm
    if el and ew and el > 0 and ew > 0:
        egg_volume = round((math.pi * el * (ew ** 2)) / 6000.0, 2)
        egg_mass_estimate = egg_volume * 1.0 * (inspection_in.estimated_egg_count or 1)
    elif inspection_in.eggs_palpated and (inspection_in.estimated_egg_count or 0) > 0:
        egg_mass_estimate = 11.3 * inspection_in.estimated_egg_count

    # 4. Ultrasonography Ovarian Follicle Volume (V_foll = pi * d_cm^3 / 6) & Preovulatory Size (POS = 4.99 cm3)
    follicle_volume = None
    pos_fraction = None
    follicle_mass_estimate = 0.0
    f_diam_mm = inspection_in.mean_follicle_diameter_mm
    f_count = inspection_in.follicle_count or 0
    if f_diam_mm and f_diam_mm > 0:
        d_cm = f_diam_mm / 10.0
        follicle_volume = round((math.pi * (d_cm ** 3)) / 6.0, 3)
        pos_fraction = round(follicle_volume / 4.99, 3)
        follicle_mass_estimate = follicle_volume * 1.0 * (f_count if f_count > 0 else 1)

    # 5. Somatic Mass (Mass - Egg Mass - Follicle Mass, assuming 1.0 g/cm3 density)
    somatic_mass = None
    if egg_mass_estimate > 0 or follicle_mass_estimate > 0:
        somatic_mass = round(max(0.0, mass - egg_mass_estimate - follicle_mass_estimate), 1)

    # 6. Table 2 ANCOVA Expected Body Mass & Condition Residual (Loehr et al. 2004, p. 449)
    predicted_mass = None
    mass_residual = None
    if shell_volume and shell_volume > 0:
        if follicle_mass_estimate > 0:
            # Somatic Mass (Body Mass - Egg & Follicle Mass) vs Vfem: 0.886 * Vfem + 13.8 (r2 = 0.952)
            predicted_mass = round(0.886 * shell_volume + 13.8, 1)
        else:
            # Somatic Mass (Body Mass - Egg Mass) vs Vfem: 0.885 * Vfem + 23.6 (r2 = 0.910)
            predicted_mass = round(0.885 * shell_volume + 23.6, 1)
    elif scl and scl > 0:
        if follicle_mass_estimate > 0:
            # Somatic Mass (Body Mass - Egg & Follicle Mass) vs SCL: 4.20 * SCL - 253 (r2 = 0.936)
            predicted_mass = round(4.20 * scl - 253.0, 1)
        else:
            # Somatic Mass (Body Mass - Egg Mass) vs SCL: 4.18 * SCL - 243 (r2 = 0.880)
            predicted_mass = round(4.18 * scl - 243.0, 1)

    if predicted_mass is not None and predicted_mass > 0:
        eval_mass = somatic_mass if somatic_mass is not None else mass
        mass_residual = round(eval_mass - predicted_mass, 1)

    # Legacy Jackson ratio for backwards compatibility
    scl_cm = scl / 10.0 if scl and scl > 0 else 0
    jacksons_ratio = round(mass / (scl_cm ** 3), 4) if scl_cm > 0 else None

    dump_data = inspection_in.model_dump()
    inspected_date = dump_data.pop("inspected_at", None) or datetime.utcnow()

    inspection = HealthInspection(
        id=str(uuid.uuid4()),
        shell_volume_cm3=shell_volume,
        body_condition_index=bci,
        mass_to_scl_ratio=mass_to_scl,
        egg_volume_cm3=egg_volume,
        follicle_volume_cm3=follicle_volume,
        pos_fraction=pos_fraction,
        somatic_mass_grams=somatic_mass,
        predicted_mass_grams=predicted_mass,
        mass_condition_residual_g=mass_residual,
        jacksons_ratio=jacksons_ratio,
        inspected_at=inspected_date,
        **dump_data
    )
    db.add(inspection)

    # Automatically record geospatial Sighting on the telemetry map if GPS coordinates are captured
    sighting_created = False
    if inspection.latitude is not None and inspection.longitude is not None:
        sighting = Sighting(
            id=str(uuid.uuid4()),
            specimen_id=inspection.specimen_id,
            latitude=inspection.latitude,
            longitude=inspection.longitude,
            horizontal_accuracy=inspection.gps_accuracy_m or 5.0,
            notes=f"Automatic GPS fix during observation: {inspection.observation_notes or 'Observation inspection'}",
            recorded_at=inspected_date
        )
        db.add(sighting)
        sighting_created = True

    db.commit()
    db.refresh(inspection)
    return {
        "status": "success",
        "inspection_id": inspection.id,
        "specimen_id": inspection.specimen_id,
        "body_condition_index": bci,
        "shell_volume_cm3": shell_volume,
        "mass_to_scl_ratio": mass_to_scl,
        "egg_volume_cm3": egg_volume,
        "follicle_volume_cm3": follicle_volume,
        "pos_fraction": pos_fraction,
        "somatic_mass_grams": somatic_mass,
        "predicted_mass_grams": predicted_mass,
        "mass_condition_residual_g": mass_residual,
        "jacksons_ratio": jacksons_ratio,
        "inspected_at": inspection.inspected_at,
        "latitude": inspection.latitude,
        "longitude": inspection.longitude,
        "sighting_logged": sighting_created
    }

def _predict_tsd_sex_ratio(temp_c: float) -> str:
    """Predict hatchling sex ratio under Pattern Ia TSD (pivotal threshold ~30.8°C)."""
    if temp_c is None:
        return "Balanced 1:1 Ratio"
    if temp_c >= 31.3:
        return "Predominantly Female (95%+)"
    elif temp_c <= 29.8:
        return "Predominantly Male (90%+)"
    return "Balanced Mixed Ratio (~1:1 Pivotal)"


def _serialize_egg(egg: EggRecord) -> dict:
    coleman_vol = None
    if egg.length_mm and egg.width_mm and egg.length_mm > 0 and egg.width_mm > 0:
        coleman_vol = round((math.pi * egg.length_mm * (egg.width_mm ** 2)) / 6000.0, 2)
    return {
        "id": egg.id,
        "clutch_id": egg.clutch_id,
        "egg_code": egg.egg_code,
        "initial_mass_grams": egg.initial_mass_grams,
        "length_mm": egg.length_mm,
        "width_mm": egg.width_mm,
        "coleman_volume_cm3": coleman_vol,
        "fertility_status": egg.fertility_status or "Fertile",
        "pipping_date": egg.pipping_date.isoformat() if egg.pipping_date else None,
        "emergence_date": egg.emergence_date.isoformat() if egg.emergence_date else None,
        "neonate_specimen_id": egg.neonate_specimen_id,
    }


@api_router.get("/breeding/pairings")
def get_breeding_pairings(
    specimen_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve recorded captive and wild courtship/breeding pairings with dam and sire metadata."""
    query = db.query(BreedingPairing)
    if specimen_id:
        query = query.filter((BreedingPairing.dam_id == specimen_id) | (BreedingPairing.sire_id == specimen_id))
    pairings = query.order_by(BreedingPairing.pairing_date.desc()).all()

    specimens_map = {s.id: s for s in db.query(Specimen).all()}
    result = []
    for p in pairings:
        dam = specimens_map.get(p.dam_id)
        sire = specimens_map.get(p.sire_id)
        result.append({
            "id": p.id,
            "dam_id": p.dam_id,
            "dam_identifier": dam.custom_identifier if dam else p.dam_id,
            "dam_species": dam.species_name if dam else None,
            "sire_id": p.sire_id,
            "sire_identifier": sire.custom_identifier if sire else p.sire_id,
            "sire_species": sire.species_name if sire else None,
            "pairing_date": p.pairing_date.isoformat() if p.pairing_date else None,
            "enclosure_or_gps": p.enclosure_or_gps,
            "courtship_behaviors": p.courtship_behaviors,
            "copulation_confirmed": bool(p.copulation_confirmed),
            "clutch_count": len(p.clutches) if p.clutches else 0,
        })
    return result


@api_router.post("/breeding/pairings")
def log_breeding_pairing(pairing_in: BreedingPairingCreate, db: Session = Depends(get_db)):
    """Log a captive breeding pairing and courtship observation."""
    pairing = BreedingPairing(
        id=str(uuid.uuid4()),
        pairing_date=pairing_in.pairing_date or datetime.utcnow(),
        dam_id=pairing_in.dam_id,
        sire_id=pairing_in.sire_id,
        enclosure_or_gps=pairing_in.enclosure_or_gps,
        courtship_behaviors=pairing_in.courtship_behaviors,
        copulation_confirmed=pairing_in.copulation_confirmed
    )
    db.add(pairing)
    db.commit()
    db.refresh(pairing)
    return {
        "status": "success",
        "pairing_id": pairing.id,
        "pairing_date": pairing.pairing_date
    }


@api_router.get("/breeding/clutches")
def get_clutches(
    dam_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve all clutches with incubation progress, TSD predictions, and individual Coleman egg records."""
    query = db.query(Clutch)
    if dam_id:
        query = query.filter(Clutch.dam_id == dam_id)
    clutches = query.order_by(Clutch.oviposition_date.desc()).all()

    specimens_map = {s.id: s for s in db.query(Specimen).all()}
    now = datetime.utcnow()
    result = []

    for c in clutches:
        dam = specimens_map.get(c.dam_id)
        sire = None
        if c.pairing and c.pairing.sire_id:
            sire = specimens_map.get(c.pairing.sire_id)

        species_name = dam.species_name if dam else "Homopus signatus signatus"
        # Expected incubation duration: ~110 days for Homopus/Chersobius padlopers, ~120 days for larger tortoises
        target_days = 110 if ("homopus" in species_name.lower() or "chersobius" in species_name.lower() or "psammobates" in species_name.lower()) else 120
        ovi_dt = c.oviposition_date or now
        days_incubating = max(0, (now - ovi_dt).days)
        progress_pct = min(100, round((days_incubating / float(target_days)) * 100))

        eggs_serialized = [_serialize_egg(e) for e in sorted(c.eggs or [], key=lambda x: x.egg_code or "")]
        mean_coleman_vol = None
        vols = [e["coleman_volume_cm3"] for e in eggs_serialized if e["coleman_volume_cm3"] is not None]
        if vols:
            mean_coleman_vol = round(sum(vols) / len(vols), 2)

        result.append({
            "id": c.id,
            "clutch_code": c.clutch_code,
            "pairing_id": c.pairing_id,
            "dam_id": c.dam_id,
            "dam_identifier": dam.custom_identifier if dam else c.dam_id,
            "sire_id": sire.id if sire else (c.pairing.sire_id if c.pairing else None),
            "sire_identifier": sire.custom_identifier if sire else None,
            "species_name": species_name,
            "common_name": dam.common_name if dam else "Tortoise",
            "oviposition_date": ovi_dt.isoformat(),
            "days_incubating": days_incubating,
            "target_incubation_days": target_days,
            "progress_pct": progress_pct,
            "nest_latitude": c.nest_latitude,
            "nest_longitude": c.nest_longitude,
            "total_eggs": c.total_eggs or len(eggs_serialized) or 1,
            "viable_eggs": c.viable_eggs if c.viable_eggs is not None else len([e for e in eggs_serialized if e["fertility_status"] not in ("Infertile", "EarlyDeath")]),
            "incubation_mode": c.incubation_mode or "Artificial",
            "target_incubation_temp_c": c.target_incubation_temp_c or 31.5,
            "predicted_sex": c.predicted_sex or _predict_tsd_sex_ratio(c.target_incubation_temp_c or 31.5),
            "mean_coleman_volume_cm3": mean_coleman_vol,
            "eggs": eggs_serialized,
        })
    return result


@api_router.post("/breeding/clutches")
def create_clutch(clutch_in: ClutchCreate, db: Session = Depends(get_db)):
    """Register a newly laid clutch, compute TSD sex prediction, and auto-create individual EggRecords."""
    clutch_id = str(uuid.uuid4())
    year_str = (clutch_in.oviposition_date or datetime.utcnow()).strftime("%Y")
    existing_count = db.query(Clutch).count()
    clutch_code = (clutch_in.clutch_code or "").strip() or f"CLUTCH-{year_str}-{existing_count + 1:03d}"

    dup = db.query(Clutch).filter(Clutch.clutch_code == clutch_code).first()
    if dup:
        clutch_code = f"{clutch_code}-{str(uuid.uuid4())[:4].upper()}"

    pred_sex = clutch_in.predicted_sex or _predict_tsd_sex_ratio(clutch_in.target_incubation_temp_c)
    viable = clutch_in.viable_eggs if clutch_in.viable_eggs is not None else clutch_in.total_eggs

    new_clutch = Clutch(
        id=clutch_id,
        pairing_id=clutch_in.pairing_id or None,
        dam_id=clutch_in.dam_id,
        clutch_code=clutch_code,
        oviposition_date=clutch_in.oviposition_date or datetime.utcnow(),
        nest_latitude=clutch_in.nest_latitude,
        nest_longitude=clutch_in.nest_longitude,
        total_eggs=clutch_in.total_eggs,
        viable_eggs=viable,
        incubation_mode=clutch_in.incubation_mode or "Artificial",
        target_incubation_temp_c=clutch_in.target_incubation_temp_c,
        predicted_sex=pred_sex,
    )
    db.add(new_clutch)
    db.flush()

    created_eggs = []
    if clutch_in.eggs and len(clutch_in.eggs) > 0:
        for idx, e_in in enumerate(clutch_in.eggs, start=1):
            ecode = (e_in.egg_code or "").strip() or f"{clutch_code}-E{idx:02d}"
            egg = EggRecord(
                id=str(uuid.uuid4()),
                clutch_id=clutch_id,
                egg_code=ecode,
                initial_mass_grams=e_in.initial_mass_grams,
                length_mm=e_in.length_mm,
                width_mm=e_in.width_mm,
                fertility_status=e_in.fertility_status or "Fertile",
                pipping_date=e_in.pipping_date,
                emergence_date=e_in.emergence_date,
                neonate_specimen_id=e_in.neonate_specimen_id,
            )
            db.add(egg)
            created_eggs.append(egg)
    else:
        # Auto-populate EggRecords from total_eggs and default dimensions (or latest gravid radiography of Dam)
        default_l = clutch_in.initial_egg_length_mm
        default_w = clutch_in.initial_egg_width_mm
        default_m = clutch_in.initial_egg_mass_grams
        if (default_l is None or default_w is None) and clutch_in.dam_id:
            last_gravid = db.query(HealthInspection).filter(
                HealthInspection.specimen_id == clutch_in.dam_id,
                HealthInspection.egg_length_mm.isnot(None)
            ).order_by(HealthInspection.inspected_at.desc()).first()
            if last_gravid:
                default_l = default_l or last_gravid.egg_length_mm
                default_w = default_w or last_gravid.egg_width_mm
                if default_m is None and last_gravid.egg_volume_cm3:
                    default_m = round(last_gravid.egg_volume_cm3 * 1.08, 1)

        for idx in range(1, (clutch_in.total_eggs or 1) + 1):
            ecode = f"{clutch_code}-E{idx:02d}"
            egg = EggRecord(
                id=str(uuid.uuid4()),
                clutch_id=clutch_id,
                egg_code=ecode,
                initial_mass_grams=default_m,
                length_mm=default_l,
                width_mm=default_w,
                fertility_status="Fertile" if idx <= viable else "Infertile",
            )
            db.add(egg)
            created_eggs.append(egg)

    db.commit()
    db.refresh(new_clutch)
    return {
        "status": "success",
        "clutch_id": new_clutch.id,
        "clutch_code": new_clutch.clutch_code,
        "predicted_sex": new_clutch.predicted_sex,
        "eggs_created": len(created_eggs),
    }


@api_router.post("/breeding/clutches/{clutch_id}/eggs")
def add_egg_to_clutch(clutch_id: str, egg_in: EggRecordCreate, db: Session = Depends(get_db)):
    """Add an individual EggRecord with Coleman (1991) dimensions and candling fertility status to a clutch."""
    clutch = db.query(Clutch).filter(Clutch.id == clutch_id).first()
    if not clutch:
        raise HTTPException(status_code=404, detail="Clutch not found.")

    existing_eggs = db.query(EggRecord).filter(EggRecord.clutch_id == clutch_id).count()
    egg_code = (egg_in.egg_code or "").strip() or f"{clutch.clutch_code}-E{existing_eggs + 1:02d}"
    if db.query(EggRecord).filter(EggRecord.egg_code == egg_code).first():
        egg_code = f"{egg_code}-{str(uuid.uuid4())[:3].upper()}"

    egg = EggRecord(
        id=str(uuid.uuid4()),
        clutch_id=clutch_id,
        egg_code=egg_code,
        initial_mass_grams=egg_in.initial_mass_grams,
        length_mm=egg_in.length_mm,
        width_mm=egg_in.width_mm,
        fertility_status=egg_in.fertility_status or "Fertile",
        pipping_date=egg_in.pipping_date,
        emergence_date=egg_in.emergence_date,
        neonate_specimen_id=egg_in.neonate_specimen_id,
    )
    db.add(egg)
    clutch.total_eggs = existing_eggs + 1
    db.commit()
    db.refresh(egg)
    return _serialize_egg(egg)


@api_router.patch("/breeding/eggs/{egg_id}")
def update_egg_record(egg_id: str, egg_in: EggRecordUpdate, db: Session = Depends(get_db)):
    """Update an egg's fertility status (candling), pipping date, emergence date, or dimensions."""
    egg = db.query(EggRecord).filter(EggRecord.id == egg_id).first()
    if not egg:
        raise HTTPException(status_code=404, detail="Egg record not found.")

    if egg_in.initial_mass_grams is not None:
        egg.initial_mass_grams = egg_in.initial_mass_grams
    if egg_in.length_mm is not None:
        egg.length_mm = egg_in.length_mm
    if egg_in.width_mm is not None:
        egg.width_mm = egg_in.width_mm
    if egg_in.fertility_status is not None:
        egg.fertility_status = egg_in.fertility_status
    if egg_in.pipping_date is not None:
        egg.pipping_date = egg_in.pipping_date
    if egg_in.emergence_date is not None:
        egg.emergence_date = egg_in.emergence_date
    if egg_in.neonate_specimen_id is not None:
        egg.neonate_specimen_id = egg_in.neonate_specimen_id

    # Recompute parent clutch viable_eggs count
    if egg.clutch_id:
        parent_clutch = db.query(Clutch).filter(Clutch.id == egg.clutch_id).first()
        if parent_clutch:
            all_eggs = db.query(EggRecord).filter(EggRecord.clutch_id == egg.clutch_id).all()
            parent_clutch.viable_eggs = len([e for e in all_eggs if (e.fertility_status or "Fertile") not in ("Infertile", "EarlyDeath")])

    db.commit()
    db.refresh(egg)
    return _serialize_egg(egg)


@api_router.post("/recognition/match-shell", response_model=List[RecognitionMatch])
async def match_shell_pattern(
    photo: UploadFile = File(..., description="Dorsal or plastron photo of the tortoise"),
    species_hint: Optional[str] = Form(None)
):
    """
    Biometric Shell Pattern Recognition Endpoint:
    Accepts field photograph, extracts scute topological features,
    and returns top candidate matches from the reference catalog.
    """
    if not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    
    image_bytes = await photo.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    try:
        matches = biometric_catalog_service.match_against_catalog(image_bytes, top_k=5)
        return [RecognitionMatch(**m) for m in matches]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Biometric analysis error: {str(e)}")

@api_router.get("/sightings/geojson")
def get_sightings_geojson(
    obfuscate: bool = False,
    specimen_id: Optional[str] = None,
    species: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns field sightings as a GeoJSON FeatureCollection for Leaflet / GIS mapping.
    Supports anti-poaching coordinate obfuscation (10km grid buffer) for public roles.
    """
    query = db.query(Sighting)
    if specimen_id:
        query = query.filter(Sighting.specimen_id == specimen_id)

    sightings = query.order_by(Sighting.recorded_at.desc()).all()

    features = []
    for s in sightings:
        specimen = s.specimen
        if species and specimen and specimen.species_name != species:
            continue

        lat = s.latitude
        lon = s.longitude
        if obfuscate:
            # Snap to ~10km grid (0.1 degree resolution) to prevent exact poaching location exposure
            lat = round(lat, 1) + 0.05
            lon = round(lon, 1) + 0.05

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "sighting_id": s.id,
                "specimen_id": s.specimen_id,
                "custom_identifier": specimen.custom_identifier if specimen else "Unmarked",
                "species_name": specimen.species_name if specimen else "Unknown Chelonian",
                "common_name": specimen.common_name if specimen else "Tortoise",
                "status": specimen.status if specimen else "Wild",
                "notch_code": specimen.notch_code if specimen else None,
                "pit_tag_number": specimen.pit_tag_number if specimen else None,
                "habitat_type": s.habitat_type,
                "ambient_temp_c": s.ambient_temp_c,
                "horizontal_accuracy": s.horizontal_accuracy,
                "recorded_at": s.recorded_at.isoformat() if s.recorded_at else None,
                "notes": s.notes,
                "obfuscated": obfuscate
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

@api_router.get("/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """Retrieve aggregate KPIs for the conservation management dashboard."""
    total_specimens = db.query(Specimen).count()
    total_sightings = db.query(Sighting).count()
    in_rehab = db.query(Specimen).filter(Specimen.status == "InRehab").count()
    wild = db.query(Specimen).filter(Specimen.status == "Wild").count()
    released = db.query(Specimen).filter(Specimen.status == "Released").count()
    breeding = db.query(Specimen).filter(Specimen.status == "Breeding").count()

    return {
        "total_specimens": total_specimens,
        "total_sightings": total_sightings,
        "in_rehab": in_rehab,
        "wild": wild,
        "released": released,
        "breeding": breeding,
        "active_telemetry_tags": 3
    }

@api_router.get("/reports/specimen/{specimen_id}/pdf")
def get_specimen_pdf_report(
    specimen_id: str,
    notch_system: str = Query("sa_standard", description="Marginal identification scheme: sa_standard, cagle, or binary"),
    mass_unit: str = Query("grams", description="Preferred mass unit: grams or kilograms"),
    length_unit: str = Query("mm", description="Preferred length unit: mm or cm"),
    db: Session = Depends(get_db)
):
    """
    Generates and returns an official Conservation Health & Studbook PDF certificate
    for the specified specimen, including morphometric growth and medical history.
    """
    # Find specimen by ID or by custom_identifier (case-insensitive for convenience)
    specimen = db.query(Specimen).filter(
        (Specimen.id == specimen_id) |
        (Specimen.custom_identifier == specimen_id) |
        (func.lower(Specimen.custom_identifier) == specimen_id.lower())
    ).first()

    if not specimen:
        raise HTTPException(status_code=404, detail=f"Specimen '{specimen_id}' not found.")

    # Fetch longitudinal health inspections safely
    inspections = []
    try:
        inspections = db.query(HealthInspection).filter(
            HealthInspection.specimen_id == specimen.id
        ).order_by(HealthInspection.inspected_at.asc()).all()
    except Exception as db_err:
        logger.warning(f"Could not load health inspections for specimen {specimen_id}: {db_err}")
        # Table might be missing newer morphometric columns in legacy deployments
        inspections = []

    inspection_records = []
    latest_insp = inspections[-1] if inspections else None
    latest_shell_vol = None
    latest_bci = None
    latest_mass_to_scl = None
    latest_egg_vol = None
    latest_somatic_mass = None
    latest_follicle_count = None
    latest_follicle_diam = None
    latest_follicle_vol = None
    latest_pos_fraction = None
    latest_predicted_mass = None
    latest_mass_residual = None
    latest_weighed_before = True
    latest_scute_wear = "Countable (8-13)"

    for insp in inspections:
        # Safe numeric formatting & fallback calculation for Loehr et al. (2004)
        mass_val = getattr(insp, 'mass_grams', None)
        scl_val = getattr(insp, 'straight_carapace_length_mm', None)
        sh_val = getattr(insp, 'shell_height_mm', None)
        sw_val = getattr(insp, 'shell_width_mm', None)

        shell_vol = getattr(insp, 'shell_volume_cm3', None)
        if shell_vol is None and scl_val and sh_val and sw_val and scl_val > 0 and sh_val > 0 and sw_val > 0:
            shell_vol = round((math.pi * scl_val * sh_val * sw_val) / 6000.0, 2)

        bci = getattr(insp, 'body_condition_index', None)
        if bci is None and mass_val and shell_vol and shell_vol > 0:
            bci = round(mass_val / shell_vol, 4)

        mass_to_scl = getattr(insp, 'mass_to_scl_ratio', None)
        if mass_to_scl is None and mass_val and scl_val and scl_val > 0:
            mass_to_scl = round(mass_val / scl_val, 4)

        egg_vol = getattr(insp, 'egg_volume_cm3', None)
        el = getattr(insp, 'egg_length_mm', None)
        ew = getattr(insp, 'egg_width_mm', None)
        if egg_vol is None and el and ew and el > 0 and ew > 0:
            egg_vol = round((math.pi * el * (ew ** 2)) / 6000.0, 2)

        f_count = getattr(insp, 'follicle_count', None)
        f_diam = getattr(insp, 'mean_follicle_diameter_mm', None)
        f_vol = getattr(insp, 'follicle_volume_cm3', None)
        pos_frac = getattr(insp, 'pos_fraction', None)
        if f_vol is None and f_diam and f_diam > 0:
            d_cm = f_diam / 10.0
            f_vol = round((math.pi * (d_cm ** 3)) / 6.0, 3)
            pos_frac = round(f_vol / 4.99, 3)

        somatic_mass = getattr(insp, 'somatic_mass_grams', None)
        if somatic_mass is None and mass_val is not None:
            egg_m = (egg_vol * 1.0 * (getattr(insp, 'estimated_egg_count', 1) or 1)) if egg_vol else (11.3 if getattr(insp, 'eggs_palpated', False) else 0.0)
            foll_m = (f_vol * 1.0 * (f_count if f_count and f_count > 0 else 1)) if f_vol else 0.0
            if egg_m > 0 or foll_m > 0:
                somatic_mass = round(max(0.0, mass_val - egg_m - foll_m), 1)

        pred_mass = getattr(insp, 'predicted_mass_grams', None)
        if pred_mass is None:
            if shell_vol and shell_vol > 0:
                pred_mass = round((0.886 * shell_vol + 13.8) if f_vol else (0.885 * shell_vol + 23.6), 1)
            elif scl_val and scl_val > 0:
                pred_mass = round((4.20 * scl_val - 253.0) if f_vol else (4.18 * scl_val - 243.0), 1)

        mass_res = getattr(insp, 'mass_condition_residual_g', None)
        if mass_res is None and pred_mass and pred_mass > 0 and mass_val is not None:
            eval_m = somatic_mass if somatic_mass is not None else mass_val
            mass_res = round(eval_m - pred_mass, 1)

        mass_str = f"{mass_val:.1f} g" if mass_val is not None else "--"
        scl_str = f"{scl_val:.1f} mm" if scl_val is not None else "--"
        vol_str = f"{shell_vol:.1f} cm³" if shell_vol is not None else "--"
        bci_str = f"{bci:.3f}" if bci is not None else "--"
        mass_to_scl_str = f"{mass_to_scl:.2f} g/mm" if mass_to_scl is not None else "--"

        ratio_val = getattr(insp, 'jacksons_ratio', None)
        ratio_str = f"{ratio_val:.4f}" if ratio_val is not None else bci_str

        bcs_val = getattr(insp, 'body_condition_score', None)
        bcs_str = f"Score {bcs_val}/5" if bcs_val is not None else "--"

        date_val = getattr(insp, 'inspected_at', None)
        date_str = date_val.strftime("%Y-%m-%d") if date_val else "--"

        # Check shell_condition_notes or observation_notes
        findings_notes = (
            getattr(insp, 'shell_condition_notes', None) or
            getattr(insp, 'observation_notes', None) or
            "Normal clinical state; no acute trauma detected."
        )

        inspection_records.append({
            "date": date_str,
            "type": getattr(insp, 'inspection_type', None) or "Scheduled",
            "mass": mass_str,
            "mass_val": mass_val,
            "scl": scl_str,
            "scl_val": scl_val,
            "shell_vol": vol_str,
            "bci": bci_str,
            "mass_to_scl": mass_to_scl_str,
            "ratio": bci_str if bci is not None else ratio_str,
            "bcs": bcs_str,
            "findings": findings_notes,
            "shell_volume_cm3": shell_vol,
            "body_condition_index": bci,
            "mass_to_scl_ratio": mass_to_scl,
            "growth_rings": getattr(insp, 'growth_rings', None),
            "scute_wear_status": getattr(insp, 'scute_wear_status', None),
            "weighed_before_excretion": getattr(insp, 'weighed_before_excretion', True),
            "follicle_count": f_count,
            "mean_follicle_diameter_mm": f_diam,
            "follicle_volume_cm3": f_vol,
            "pos_fraction": pos_frac,
            "somatic_mass_grams": somatic_mass,
            "predicted_mass_grams": pred_mass,
            "mass_condition_residual_g": mass_res
        })

    if latest_insp:
        latest_mass = getattr(latest_insp, 'mass_grams', None)
        latest_scl = getattr(latest_insp, 'straight_carapace_length_mm', None)
        latest_sh = getattr(latest_insp, 'shell_height_mm', None)
        latest_sw = getattr(latest_insp, 'shell_width_mm', None)
        latest_rings = getattr(latest_insp, 'growth_rings', None)
        latest_scute_wear = getattr(latest_insp, 'scute_wear_status', None) or "Countable (8-13)"
        latest_weighed_before = getattr(latest_insp, 'weighed_before_excretion', True)
        if latest_weighed_before is None:
            latest_weighed_before = True
        latest_eggs = getattr(latest_insp, 'eggs_palpated', False)
        latest_egg_count = getattr(latest_insp, 'estimated_egg_count', 0)
        latest_el = getattr(latest_insp, 'egg_length_mm', None)
        latest_ew = getattr(latest_insp, 'egg_width_mm', None)
        latest_follicle_count = getattr(latest_insp, 'follicle_count', None)
        latest_follicle_diam = getattr(latest_insp, 'mean_follicle_diameter_mm', None)
        latest_follicle_vol = getattr(latest_insp, 'follicle_volume_cm3', None)
        latest_pos_fraction = getattr(latest_insp, 'pos_fraction', None)

        if latest_scl and latest_sh and latest_sw and latest_scl > 0 and latest_sh > 0 and latest_sw > 0:
            latest_shell_vol = round((math.pi * latest_scl * latest_sh * latest_sw) / 6000.0, 2)
        if latest_mass and latest_shell_vol and latest_shell_vol > 0:
            latest_bci = round(latest_mass / latest_shell_vol, 4)
        if latest_mass and latest_scl and latest_scl > 0:
            latest_mass_to_scl = round(latest_mass / latest_scl, 4)
        if latest_el and latest_ew and latest_el > 0 and latest_ew > 0:
            latest_egg_vol = round((math.pi * latest_el * (latest_ew ** 2)) / 6000.0, 2)
        if latest_follicle_vol is None and latest_follicle_diam and latest_follicle_diam > 0:
            d_cm = latest_follicle_diam / 10.0
            latest_follicle_vol = round((math.pi * (d_cm ** 3)) / 6.0, 3)
            latest_pos_fraction = round(latest_follicle_vol / 4.99, 3)

        latest_somatic_mass = getattr(latest_insp, 'somatic_mass_grams', None)
        if latest_somatic_mass is None and latest_mass is not None:
            egg_m = (latest_egg_vol * 1.0 * (latest_egg_count or 1)) if latest_egg_vol else (11.3 * (latest_egg_count or 1) if latest_eggs else 0.0)
            foll_m = (latest_follicle_vol * 1.0 * (latest_follicle_count if latest_follicle_count and latest_follicle_count > 0 else 1)) if latest_follicle_vol else 0.0
            if egg_m > 0 or foll_m > 0:
                latest_somatic_mass = round(max(0.0, latest_mass - egg_m - foll_m), 1)

        latest_predicted_mass = getattr(latest_insp, 'predicted_mass_grams', None)
        if latest_predicted_mass is None:
            if latest_shell_vol and latest_shell_vol > 0:
                latest_predicted_mass = round((0.886 * latest_shell_vol + 13.8) if latest_follicle_vol else (0.885 * latest_shell_vol + 23.6), 1)
            elif latest_scl and latest_scl > 0:
                latest_predicted_mass = round((4.20 * latest_scl - 253.0) if latest_follicle_vol else (4.18 * latest_scl - 243.0), 1)

        latest_mass_residual = getattr(latest_insp, 'mass_condition_residual_g', None)
        if latest_mass_residual is None and latest_predicted_mass and latest_predicted_mass > 0 and latest_mass is not None:
            eval_m = latest_somatic_mass if latest_somatic_mass is not None else latest_mass
            latest_mass_residual = round(eval_m - latest_predicted_mass, 1)
    else:
        latest_mass = None
        latest_scl = None
        latest_sh = None
        latest_sw = None
        latest_rings = None
        latest_eggs = False
        latest_egg_count = 0
        latest_el = None
        latest_ew = None

    # Safely retrieve taxonomy IUCN status
    iucn_status = "LC (Least Concern)"
    try:
        if specimen.taxonomy and getattr(specimen.taxonomy, 'iucn_status', None):
            iucn_status = specimen.taxonomy.iucn_status
    except Exception:
        pass

    # Query recorded clutches and breeding pairings for this specimen
    specimen_clutches = []
    clutch_count = 0
    try:
        raw_clutches = db.query(Clutch).filter(Clutch.dam_id == specimen.id).order_by(Clutch.oviposition_date.desc()).all()
        if not raw_clutches:
            # Check if sire via BreedingPairing
            sire_pairing_ids = [p.id for p in db.query(BreedingPairing).filter(BreedingPairing.sire_id == specimen.id).all()]
            if sire_pairing_ids:
                raw_clutches = db.query(Clutch).filter(Clutch.pairing_id.in_(sire_pairing_ids)).order_by(Clutch.oviposition_date.desc()).all()
        clutch_count = len(raw_clutches)
        for c in raw_clutches:
            eggs_list = [_serialize_egg(e) for e in sorted(c.eggs or [], key=lambda x: x.egg_code or "")]
            specimen_clutches.append({
                "clutch_code": c.clutch_code,
                "oviposition_date": c.oviposition_date.strftime("%Y-%m-%d") if c.oviposition_date else "--",
                "total_eggs": c.total_eggs or len(eggs_list) or 1,
                "viable_eggs": c.viable_eggs if c.viable_eggs is not None else len(eggs_list),
                "incubation_mode": c.incubation_mode or "Artificial",
                "target_temp_c": c.target_incubation_temp_c or 31.5,
                "predicted_sex": c.predicted_sex or _predict_tsd_sex_ratio(c.target_incubation_temp_c or 31.5),
                "eggs": eggs_list,
            })
    except Exception as cl_err:
        logger.warning(f"Could not query clutches for specimen {specimen.id}: {cl_err}")

    specimen_data = {
        "custom_identifier": specimen.custom_identifier or "N/A",
        "species_name": specimen.species_name or "N/A",
        "common_name": specimen.common_name or "Chelonian",
        "iucn_status": iucn_status,
        "pit_tag_number": specimen.pit_tag_number,
        "notch_code": specimen.notch_code,
        "notch_system": notch_system,
        "mass_unit": mass_unit,
        "length_unit": length_unit,
        "sex": specimen.sex or "Undetermined",
        "status": specimen.status or "Wild",
        "dam_id": specimen.dam_id,
        "sire_id": specimen.sire_id,
        "clutch_count": clutch_count,
        "clutches": specimen_clutches,
        "inspections": inspection_records,
        "latest_mass": latest_mass,
        "latest_scl": latest_scl,
        "latest_sh": latest_sh,
        "latest_sw": latest_sw,
        "latest_shell_volume": latest_shell_vol,
        "latest_bci": latest_bci,
        "latest_mass_to_scl": latest_mass_to_scl,
        "latest_growth_rings": latest_rings,
        "latest_scute_wear": latest_scute_wear,
        "weighed_before_excretion": latest_weighed_before,
        "eggs_palpated": latest_eggs,
        "estimated_egg_count": latest_egg_count,
        "egg_length_mm": latest_el,
        "egg_width_mm": latest_ew,
        "egg_volume_cm3": latest_egg_vol,
        "follicle_count": latest_follicle_count,
        "mean_follicle_diameter_mm": latest_follicle_diam,
        "follicle_volume_cm3": latest_follicle_vol,
        "pos_fraction": latest_pos_fraction,
        "somatic_mass_grams": latest_somatic_mass,
        "predicted_mass_grams": latest_predicted_mass,
        "mass_condition_residual_g": latest_mass_residual,
        "is_adult_breeding_size": (latest_scl >= 84.1) if latest_scl is not None else None
    }

    try:
        pdf_bytes = report_generator.generate_specimen_report(specimen_data)
        safe_identifier = re.sub(r'[^a-zA-Z0-9_\-]', '_', specimen.custom_identifier or 'specimen')
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="SATRA_Report_{safe_identifier}.pdf"',
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    except Exception as e:
        logger.error(f"Failed to render specimen report PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to render PDF: {str(e)}")


@api_router.get("/exports/specimens.csv")
def export_specimens_csv(
    notch_system: str = Query("sa_standard", description="sa_standard, cagle, or binary"),
    mass_unit: str = Query("grams", description="grams or kilograms"),
    length_unit: str = Query("mm", description="mm or cm"),
    db: Session = Depends(get_db)
):
    """Export the full Specimen Registry with latest Loehr (2004) biometrics and active unit/notch preferences as CSV."""
    import csv
    import io

    specimens = db.query(Specimen).order_by(Specimen.created_at.desc()).all()
    all_insp = db.query(HealthInspection).order_by(HealthInspection.inspected_at.desc()).all()
    latest_by_spec = {}
    count_by_spec = {}
    for ins in all_insp:
        count_by_spec[ins.specimen_id] = count_by_spec.get(ins.specimen_id, 0) + 1
        if ins.specimen_id not in latest_by_spec:
            latest_by_spec[ins.specimen_id] = ins

    is_kg = mass_unit.lower() in ("kilograms", "kg")
    is_cm = length_unit.lower() in ("cm", "centimeters")
    m_hdr = "kg" if is_kg else "g"
    l_hdr = "cm" if is_cm else "mm"

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Specimen_UUID",
        "Custom_Identifier",
        "Scientific_Name",
        "Common_Name",
        "Sex",
        "Status",
        "Raw_Notch_Code",
        f"Formatted_Notch_ID ({notch_system})",
        "PIT_Microchip_15Digit",
        "Inspection_Count",
        f"Latest_Mass ({m_hdr})",
        f"Latest_SCL ({l_hdr})",
        f"Latest_SW ({l_hdr})",
        f"Latest_SH ({l_hdr})",
        "Latest_Shell_Volume_cm3",
        "Latest_BCI_g_cm3",
        f"Latest_Somatic_Mass ({m_hdr})",
        f"Table2_Expected_Mass ({m_hdr})",
        "Table2_Condition_Residual_g",
        "Created_At_UTC"
    ])

    for sp in specimens:
        formatted_notch, _ = report_generator._format_notch_code(sp.notch_code, notch_system)
        lat = latest_by_spec.get(sp.id)
        cnt = count_by_spec.get(sp.id, 0)

        def conv_m(val):
            if val is None:
                return ""
            return f"{val / 1000.0:.3f}" if is_kg else f"{val:.1f}"

        def conv_l(val):
            if val is None:
                return ""
            return f"{val / 10.0:.2f}" if is_cm else f"{val:.1f}"

        writer.writerow([
            sp.id,
            sp.custom_identifier,
            sp.species_name,
            sp.common_name,
            sp.sex,
            sp.status,
            sp.notch_code or "",
            formatted_notch,
            sp.pit_tag_number or "",
            cnt,
            conv_m(lat.mass_grams) if lat else "",
            conv_l(lat.straight_carapace_length_mm) if lat else "",
            conv_l(lat.shell_width_mm) if lat else "",
            conv_l(lat.shell_height_mm) if lat else "",
            f"{lat.shell_volume_cm3:.2f}" if (lat and lat.shell_volume_cm3 is not None) else "",
            f"{lat.body_condition_index:.4f}" if (lat and lat.body_condition_index is not None) else "",
            conv_m(lat.somatic_mass_grams) if lat else "",
            conv_m(lat.predicted_mass_grams) if lat else "",
            f"{lat.mass_condition_residual_g:+.1f}" if (lat and lat.mass_condition_residual_g is not None) else "",
            sp.created_at.strftime("%Y-%m-%d %H:%M:%S") if sp.created_at else ""
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="SATRA_Specimens_Registry.csv"',
            "Cache-Control": "no-cache"
        }
    )


@api_router.get("/exports/health-inspections.csv")
def export_health_inspections_csv(
    specimen_id: Optional[str] = None,
    notch_system: str = Query("sa_standard", description="sa_standard, cagle, or binary"),
    mass_unit: str = Query("grams", description="grams or kilograms"),
    length_unit: str = Query("mm", description="mm or cm"),
    db: Session = Depends(get_db)
):
    """Export longitudinal Health Inspections with all Loehr et al. (2004), Coleman (1991), and POS ultrasound metrics as CSV."""
    import csv
    import io

    query = db.query(HealthInspection)
    if specimen_id:
        query = query.filter(HealthInspection.specimen_id == specimen_id)
    inspections = query.order_by(HealthInspection.inspected_at.desc()).all()
    spec_map = {s.id: s for s in db.query(Specimen).all()}

    is_kg = mass_unit.lower() in ("kilograms", "kg")
    is_cm = length_unit.lower() in ("cm", "centimeters")
    m_hdr = "kg" if is_kg else "g"
    l_hdr = "cm" if is_cm else "mm"

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Inspection_UUID",
        "Inspected_At_UTC",
        "Specimen_Identifier",
        "Species_Name",
        f"Formatted_Notch ({notch_system})",
        "Inspection_Type",
        "Weighed_Before_Excretion",
        f"Body_Mass ({m_hdr})",
        f"Somatic_Mass ({m_hdr})",
        f"Table2_Expected_Mass ({m_hdr})",
        "Table2_Condition_Residual_g",
        f"SCL ({l_hdr})",
        f"Shell_Width_SW ({l_hdr})",
        f"Shell_Height_SH ({l_hdr})",
        f"Plastron_Length_PL ({l_hdr})",
        f"Plastron_Width_PW ({l_hdr})",
        "Shell_Volume_Vshell_cm3",
        "Volumetric_BCI_g_cm3",
        "Linear_Mass_to_SCL_g_mm",
        "Costal1_Growth_Rings",
        "Scute_Wear_Class",
        "Body_Condition_Score_1to5",
        "Eggs_Palpated_or_Xray",
        "Egg_Count",
        f"Egg_Length ({l_hdr})",
        f"Egg_Width ({l_hdr})",
        "Coleman_Egg_Volume_cm3",
        "Ultrasound_Follicle_Count",
        f"Mean_Follicle_Diameter ({l_hdr})",
        "Single_Follicle_Volume_cm3",
        "POS_Fraction_vs_4.99cm3",
        "GPS_Latitude",
        "GPS_Longitude",
        "GPS_Accuracy_m",
        "Clinical_and_Field_Notes"
    ])

    def conv_m(val):
        if val is None:
            return ""
        return f"{val / 1000.0:.3f}" if is_kg else f"{val:.1f}"

    def conv_l(val):
        if val is None:
            return ""
        return f"{val / 10.0:.2f}" if is_cm else f"{val:.1f}"

    for ins in inspections:
        sp = spec_map.get(ins.specimen_id)
        formatted_notch, _ = report_generator._format_notch_code(sp.notch_code if sp else None, notch_system)
        writer.writerow([
            ins.id,
            ins.inspected_at.strftime("%Y-%m-%d %H:%M:%S") if ins.inspected_at else "",
            sp.custom_identifier if sp else ins.specimen_id,
            sp.species_name if sp else "",
            formatted_notch,
            ins.inspection_type or "Scheduled",
            "Yes" if getattr(ins, "weighed_before_excretion", True) is not False else "No",
            conv_m(ins.mass_grams),
            conv_m(ins.somatic_mass_grams),
            conv_m(ins.predicted_mass_grams),
            f"{ins.mass_condition_residual_g:+.1f}" if ins.mass_condition_residual_g is not None else "",
            conv_l(ins.straight_carapace_length_mm),
            conv_l(ins.shell_width_mm),
            conv_l(ins.shell_height_mm),
            conv_l(ins.plastron_length_mm),
            conv_l(ins.plastron_width_mm),
            f"{ins.shell_volume_cm3:.2f}" if ins.shell_volume_cm3 is not None else "",
            f"{ins.body_condition_index:.4f}" if ins.body_condition_index is not None else "",
            f"{ins.mass_to_scl_ratio:.3f}" if ins.mass_to_scl_ratio is not None else "",
            ins.growth_rings or "",
            getattr(ins, "scute_wear_status", "") or "",
            ins.body_condition_score or 3,
            "Yes" if ins.eggs_palpated else "No",
            ins.estimated_egg_count or 0,
            conv_l(ins.egg_length_mm),
            conv_l(ins.egg_width_mm),
            f"{ins.egg_volume_cm3:.2f}" if ins.egg_volume_cm3 is not None else "",
            ins.follicle_count if ins.follicle_count is not None else "",
            conv_l(ins.mean_follicle_diameter_mm),
            f"{ins.follicle_volume_cm3:.3f}" if ins.follicle_volume_cm3 is not None else "",
            f"{ins.pos_fraction:.2f}" if ins.pos_fraction is not None else "",
            f"{ins.latitude:.5f}" if ins.latitude is not None else "",
            f"{ins.longitude:.5f}" if ins.longitude is not None else "",
            f"{ins.gps_accuracy_m:.1f}" if ins.gps_accuracy_m is not None else "",
            ins.observation_notes or ins.shell_condition_notes or ""
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="SATRA_Longitudinal_Biometrics_Loehr2004.csv"',
            "Cache-Control": "no-cache"
        }
    )


# --- APPSHEET CSV IMPORTER & DIRECT APPSHEET CLOUD REST API SYNC ---

class AppSheetRowImportRequest(BaseModel):
    rows: List[dict]
    column_mapping: Optional[dict] = None
    default_species_name: str = "Chersobius signatus"
    default_common_name: str = "Speckled Padloper"
    mass_unit: str = "grams"  # grams | kilograms
    length_unit: str = "mm"   # mm | cm


class AppSheetCloudSyncRequest(BaseModel):
    app_id: str = Field(..., description="AppSheet Application ID (UUID)")
    access_key: str = Field(..., description="AppSheet ApplicationAccessKey")
    table_name: str = Field(..., description="AppSheet Table Name (e.g. Specimens, Inspections, Observations)")
    region_host: str = Field("api.appsheet.com", description="api.appsheet.com or eu.appsheet.com")
    selector: Optional[str] = Field(None, description="Optional AppSheet Filter/Selector expression")
    column_mapping: Optional[dict] = None
    default_species_name: str = "Chersobius signatus"
    default_common_name: str = "Speckled Padloper"
    mass_unit: str = "grams"
    length_unit: str = "mm"
    preview_only: bool = False


APPSHEET_FIELD_ALIASES = {
    "custom_identifier": [
        "custom_identifier", "specimen_identifier", "tortoise_id", "tortoise id", "specimen_id", "specimen id",
        "id_code", "id code", "accession", "accession_id", "animal_id", "animal id", "mark_id", "name", "code",
        "tortoise_no", "tortoise #", "id", "_rownumber", "row id"
    ],
    "species_name": [
        "species_name", "scientific_name", "scientific name", "species", "taxon", "latin_name", "binomial"
    ],
    "common_name": [
        "common_name", "common name", "vernacular", "english_name", "species_common"
    ],
    "sex": [
        "sex", "gender"
    ],
    "status": [
        "status", "cohort", "disposition", "rehab_status", "state"
    ],
    "notch_code": [
        "notch_code", "raw_notch_code", "notch", "notches", "notch id", "marginal_notch", "cagle_code",
        "shell_notch", "marking", "scute_notch"
    ],
    "pit_tag_number": [
        "pit_tag_number", "pit_microchip_15digit", "pit_tag", "pit tag", "microchip", "rfid", "chip_number", "transponder"
    ],
    "inspected_at": [
        "inspected_at", "inspected_at_utc", "date", "observation_date", "inspection_date", "timestamp",
        "capture_date", "date_time", "recorded_at", "survey_date"
    ],
    "inspection_type": [
        "inspection_type", "type", "assessment_type", "visit_type", "event_type"
    ],
    "mass_grams": [
        "mass_grams", "body_mass (g)", "body_mass (kg)", "latest_mass (g)", "latest_mass (kg)",
        "mass", "weight", "body_mass", "mass_g", "weight_g", "mass (g)", "weight (g)"
    ],
    "straight_carapace_length_mm": [
        "straight_carapace_length_mm", "scl (mm)", "scl (cm)", "latest_scl (mm)", "latest_scl (cm)",
        "scl", "carapace_length", "length", "scl_mm", "length_mm", "carapace length"
    ],
    "shell_width_mm": [
        "shell_width_mm", "shell_width_sw (mm)", "shell_width_sw (cm)", "latest_sw (mm)",
        "sw", "scw", "shell_width", "width", "carapace_width", "sw_mm", "width_mm", "mid_body_width"
    ],
    "shell_height_mm": [
        "shell_height_mm", "shell_height_sh (mm)", "shell_height_sh (cm)", "latest_sh (mm)",
        "sh", "shell_height", "height", "doming", "sh_mm", "height_mm"
    ],
    "plastron_length_mm": [
        "plastron_length_mm", "plastron_length_pl (mm)", "plastron_length_pl (cm)",
        "pl", "plastron_length", "plastron length", "pl_mm"
    ],
    "plastron_width_mm": [
        "plastron_width_mm", "plastron_width_pw (mm)", "plastron_width_pw (cm)",
        "pw", "plastron_width", "plastron width", "pw_mm"
    ],
    "growth_rings": [
        "growth_rings", "costal1_growth_rings", "rings", "annuli", "scute_rings", "growth rings", "laminae"
    ],
    "scute_wear_status": [
        "scute_wear_status", "scute_wear_class", "wear", "scute_wear", "shell_wear"
    ],
    "body_condition_score": [
        "body_condition_score", "body_condition_score_1to5", "bcs", "condition_score", "health_score"
    ],
    "eggs_palpated": [
        "eggs_palpated", "eggs_palpated_or_xray", "gravid", "is_gravid", "pregnant", "calcified_eggs"
    ],
    "estimated_egg_count": [
        "estimated_egg_count", "egg_count", "eggs", "clutch_size", "number_of_eggs"
    ],
    "egg_length_mm": [
        "egg_length_mm", "egg_length (mm)", "egg_length (cm)", "egg_length", "el", "egg_l"
    ],
    "egg_width_mm": [
        "egg_width_mm", "egg_width (mm)", "egg_width (cm)", "egg_width", "ew", "egg_w"
    ],
    "follicle_count": [
        "follicle_count", "ultrasound_follicle_count", "follicles", "ovarian_follicles"
    ],
    "mean_follicle_diameter_mm": [
        "mean_follicle_diameter_mm", "mean_follicle_diameter (mm)", "follicle_diameter", "follicle_size_mm"
    ],
    "latitude": [
        "latitude", "gps_latitude", "lat", "y_coord", "decimal_latitude"
    ],
    "longitude": [
        "longitude", "gps_longitude", "lon", "lng", "long", "x_coord", "decimal_longitude"
    ],
    "observation_notes": [
        "observation_notes", "clinical_and_field_notes", "notes", "comments", "remarks", "field_notes", "clinical_notes", "description"
    ]
}


def _auto_detect_appsheet_mapping(headers: List[str]) -> dict:
    """Automatically map incoming AppSheet CSV or REST API column names to SATRA canonical fields."""
    mapping = {}
    norm_to_orig = {}
    for h in headers:
        if not h:
            continue
        norm = re.sub(r"[\s_\-]+", "_", str(h).strip().lower())
        norm_to_orig[norm] = h
        norm_plain = str(h).strip().lower()
        norm_to_orig[norm_plain] = h

    used_headers = set()
    for target_field, aliases in APPSHEET_FIELD_ALIASES.items():
        for alias in aliases:
            alias_norm = re.sub(r"[\s_\-]+", "_", alias.lower())
            if alias.lower() in norm_to_orig and norm_to_orig[alias.lower()] not in used_headers:
                orig_col = norm_to_orig[alias.lower()]
                mapping[target_field] = orig_col
                used_headers.add(orig_col)
                break
            if alias_norm in norm_to_orig and norm_to_orig[alias_norm] not in used_headers:
                orig_col = norm_to_orig[alias_norm]
                mapping[target_field] = orig_col
                used_headers.add(orig_col)
                break

    # Look for AppSheet Combined LatLong column ("LatLong", "Location", "GPS", "Coordinates")
    if "latitude" not in mapping and "longitude" not in mapping:
        for h in headers:
            hl = str(h).strip().lower()
            if hl in ("latlong", "location", "gps", "coordinates", "gps_coordinates", "position"):
                mapping["latlong_combined"] = h
                break

    return mapping


def _parse_float(val) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "na", "n/a", "-", "--"):
        return None
    s = re.sub(r"[^\d.\-+]", "", s.replace(",", "."))
    try:
        return float(s)
    except Exception:
        return None


def _parse_int(val) -> Optional[int]:
    f = _parse_float(val)
    return int(round(f)) if f is not None else None


def _parse_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("true", "yes", "y", "1", "gravid", "confirmed", "checked")


def _parse_datetime(val) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    s = str(val).strip()
    if not s:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y/%m/%d",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _normalize_notch_code(raw_val: Optional[str]) -> Optional[str]:
    """Normalize AppSheet notch codes (e.g. '1L, 4R', 'L1 R4', 'L1-R4') into SATRA's 'L1-R4' format."""
    if not raw_val:
        return None
    s = str(raw_val).strip().upper()
    if not s or s in ("NONE", "NULL", "UNMARKED", "N/A", "--"):
        return None
    tokens = re.findall(r"(?:[LR]\d{1,2}|\d{1,2}[LR]|SUPRACAUDAL|SC)", s)
    if not tokens:
        return s
    normalized = []
    for t in tokens:
        if re.match(r"^\d{1,2}[LR]$", t):
            normalized.append(t[-1] + t[:-1])
        else:
            normalized.append(t)
    return "-".join(normalized)


def _ingest_appsheet_rows(
    rows: List[dict],
    db: Session,
    column_mapping: Optional[dict] = None,
    default_species_name: str = "Chersobius signatus",
    default_common_name: str = "Speckled Padloper",
    mass_unit: str = "grams",
    length_unit: str = "mm"
) -> dict:
    """Idempotently upsert Specimens, HealthInspections (with full Loehr 2004 calculations), and Sightings from AppSheet rows."""
    if not rows:
        return {
            "status": "success",
            "rows_processed": 0,
            "specimens_created": 0,
            "specimens_updated": 0,
            "inspections_created": 0,
            "sightings_created": 0,
            "skipped_rows": 0,
            "applied_mapping": {}
        }

    headers = list(rows[0].keys())
    auto_map = _auto_detect_appsheet_mapping(headers)
    mapping = {**auto_map, **(column_mapping or {})}

    is_kg = mass_unit.lower() in ("kilograms", "kg")
    is_cm = length_unit.lower() in ("cm", "centimeters")

    specimens_created = 0
    specimens_updated = 0
    inspections_created = 0
    sightings_created = 0
    skipped_rows = 0

    existing_specimens = {s.custom_identifier.upper(): s for s in db.query(Specimen).all() if s.custom_identifier}

    def get_val(row: dict, field_key: str):
        col = mapping.get(field_key)
        if not col or col not in row:
            return None
        v = row.get(col)
        if v is None:
            return None
        sv = str(v).strip()
        return sv if sv != "" else None

    for idx, row in enumerate(rows):
        raw_id = get_val(row, "custom_identifier")
        raw_notch = _normalize_notch_code(get_val(row, "notch_code"))
        raw_pit = get_val(row, "pit_tag_number")

        if not raw_id:
            if raw_notch:
                raw_id = f"APPSHEET-{raw_notch}"
            elif raw_pit:
                raw_id = f"PIT-{raw_pit[-6:]}"
            else:
                skipped_rows += 1
                continue

        norm_id_key = raw_id.upper()
        sp = existing_specimens.get(norm_id_key)

        species = get_val(row, "species_name") or default_species_name
        common = get_val(row, "common_name") or default_common_name
        sex_raw = (get_val(row, "sex") or "Undetermined").strip()
        if sex_raw.upper().startswith("F"):
            sex = "Female"
        elif sex_raw.upper().startswith("M"):
            sex = "Male"
        else:
            sex = "Undetermined"

        status_raw = (get_val(row, "status") or "Wild").strip()
        if "rehab" in status_raw.lower() or "icu" in status_raw.lower():
            status = "InRehab"
        elif "releas" in status_raw.lower():
            status = "Released"
        elif "breed" in status_raw.lower() or "captiv" in status_raw.lower():
            status = "Breeding"
        else:
            status = "Wild"

        if not sp:
            sp = Specimen(
                id=str(uuid.uuid4()),
                custom_identifier=raw_id,
                species_name=species,
                common_name=common,
                sex=sex,
                status=status,
                notch_code=raw_notch,
                pit_tag_number=raw_pit,
                created_at=_parse_datetime(get_val(row, "inspected_at")) or datetime.utcnow()
            )
            db.add(sp)
            db.flush()
            existing_specimens[norm_id_key] = sp
            specimens_created += 1
        else:
            updated = False
            if raw_notch and not sp.notch_code:
                sp.notch_code = raw_notch
                updated = True
            if raw_pit and not sp.pit_tag_number:
                sp.pit_tag_number = raw_pit
                updated = True
            if sex != "Undetermined" and sp.sex == "Undetermined":
                sp.sex = sex
                updated = True
            if updated:
                specimens_updated += 1

        # Parse Biometric & Health Inspection fields if present in row
        mass_val = _parse_float(get_val(row, "mass_grams"))
        scl_val = _parse_float(get_val(row, "straight_carapace_length_mm"))
        sw_val = _parse_float(get_val(row, "shell_width_mm"))
        sh_val = _parse_float(get_val(row, "shell_height_mm"))
        pl_val = _parse_float(get_val(row, "plastron_length_mm"))
        pw_val = _parse_float(get_val(row, "plastron_width_mm"))

        if is_kg and mass_val is not None:
            mass_val = round(mass_val * 1000.0, 2)
        if is_cm:
            if scl_val is not None:
                scl_val = round(scl_val * 10.0, 2)
            if sw_val is not None:
                sw_val = round(sw_val * 10.0, 2)
            if sh_val is not None:
                sh_val = round(sh_val * 10.0, 2)
            if pl_val is not None:
                pl_val = round(pl_val * 10.0, 2)
            if pw_val is not None:
                pw_val = round(pw_val * 10.0, 2)

        # Parse GPS coordinates (either separate Lat/Lon or AppSheet "Lat, Long" LatLong column)
        lat_val = _parse_float(get_val(row, "latitude"))
        lon_val = _parse_float(get_val(row, "longitude"))
        if (lat_val is None or lon_val is None) and mapping.get("latlong_combined"):
            raw_ll = row.get(mapping["latlong_combined"])
            if raw_ll and "," in str(raw_ll):
                parts = str(raw_ll).split(",")
                if len(parts) >= 2:
                    lat_val = _parse_float(parts[0])
                    lon_val = _parse_float(parts[1])

        inspected_at = _parse_datetime(get_val(row, "inspected_at")) or datetime.utcnow()
        notes_val = get_val(row, "observation_notes")

        if mass_val is not None and scl_val is not None and mass_val > 0 and scl_val > 0:
            # Check for duplicate inspection on same specimen, date, and mass
            existing_insp = db.query(HealthInspection).filter(
                HealthInspection.specimen_id == sp.id,
                HealthInspection.mass_grams == mass_val,
                HealthInspection.straight_carapace_length_mm == scl_val
            ).first()

            if not existing_insp or (existing_insp.inspected_at and abs((existing_insp.inspected_at - inspected_at).total_seconds()) > 43200):
                el_val = _parse_float(get_val(row, "egg_length_mm"))
                ew_val = _parse_float(get_val(row, "egg_width_mm"))
                f_diam = _parse_float(get_val(row, "mean_follicle_diameter_mm"))
                if is_cm:
                    if el_val is not None:
                        el_val = round(el_val * 10.0, 2)
                    if ew_val is not None:
                        ew_val = round(ew_val * 10.0, 2)
                    if f_diam is not None:
                        f_diam = round(f_diam * 10.0, 2)

                egg_cnt = _parse_int(get_val(row, "estimated_egg_count")) or 0
                gravid_flag = _parse_bool(get_val(row, "eggs_palpated")) or (egg_cnt > 0) or (el_val is not None and el_val > 0)

                # Compute Loehr et al. (2004) biometrics via record_health_inspection logic
                mass_to_scl = round(mass_val / scl_val, 4) if scl_val > 0 else None
                shell_volume = None
                bci = None
                if scl_val and sh_val and sw_val and scl_val > 0 and sh_val > 0 and sw_val > 0:
                    shell_volume = round((math.pi * scl_val * sh_val * sw_val) / 6000.0, 2)
                    if shell_volume > 0:
                        bci = round(mass_val / shell_volume, 4)

                egg_volume = None
                egg_mass_est = 0.0
                if el_val and ew_val and el_val > 0 and ew_val > 0:
                    egg_volume = round((math.pi * el_val * (ew_val ** 2)) / 6000.0, 2)
                    egg_mass_est = egg_volume * 1.0 * (egg_cnt or 1)
                elif gravid_flag and egg_cnt > 0:
                    egg_mass_est = 11.3 * egg_cnt

                f_cnt = _parse_int(get_val(row, "follicle_count"))
                follicle_volume = None
                pos_fraction = None
                follicle_mass_est = 0.0
                if f_diam and f_diam > 0:
                    d_cm = f_diam / 10.0
                    follicle_volume = round((math.pi * (d_cm ** 3)) / 6.0, 3)
                    pos_fraction = round(follicle_volume / 4.99, 3)
                    follicle_mass_est = follicle_volume * 1.0 * (f_cnt if f_cnt and f_cnt > 0 else 1)

                somatic_mass = None
                if egg_mass_est > 0 or follicle_mass_est > 0:
                    somatic_mass = round(max(0.0, mass_val - egg_mass_est - follicle_mass_est), 1)

                predicted_mass = None
                mass_residual = None
                if shell_volume and shell_volume > 0:
                    predicted_mass = round((0.886 * shell_volume + 13.8) if follicle_mass_est > 0 else (0.885 * shell_volume + 23.6), 1)
                elif scl_val and scl_val > 0:
                    predicted_mass = round((4.20 * scl_val - 253.0) if follicle_mass_est > 0 else (4.18 * scl_val - 243.0), 1)

                if predicted_mass is not None and predicted_mass > 0:
                    eval_mass = somatic_mass if somatic_mass is not None else mass_val
                    mass_residual = round(eval_mass - predicted_mass, 1)

                scl_cm = scl_val / 10.0
                jacksons_ratio = round(mass_val / (scl_cm ** 3), 4) if scl_cm > 0 else None
                bcs_val = _parse_int(get_val(row, "body_condition_score"))
                if bcs_val is None or bcs_val < 1 or bcs_val > 5:
                    bcs_val = 4 if (bci and bci >= 1.0) else 3

                insp = HealthInspection(
                    id=str(uuid.uuid4()),
                    specimen_id=sp.id,
                    inspection_type=get_val(row, "inspection_type") or "AppSheet Import",
                    mass_grams=mass_val,
                    straight_carapace_length_mm=scl_val,
                    shell_width_mm=sw_val,
                    shell_height_mm=sh_val,
                    plastron_length_mm=pl_val,
                    plastron_width_mm=pw_val,
                    growth_rings=get_val(row, "growth_rings"),
                    scute_wear_status=get_val(row, "scute_wear_status") or "Countable (8-13)",
                    weighed_before_excretion=True,
                    body_condition_score=bcs_val,
                    shell_volume_cm3=shell_volume,
                    body_condition_index=bci,
                    mass_to_scl_ratio=mass_to_scl,
                    jacksons_ratio=jacksons_ratio,
                    eggs_palpated=gravid_flag,
                    estimated_egg_count=egg_cnt if gravid_flag else 0,
                    egg_length_mm=el_val,
                    egg_width_mm=ew_val,
                    egg_volume_cm3=egg_volume,
                    follicle_count=f_cnt,
                    mean_follicle_diameter_mm=f_diam,
                    follicle_volume_cm3=follicle_volume,
                    pos_fraction=pos_fraction,
                    somatic_mass_grams=somatic_mass,
                    predicted_mass_grams=predicted_mass,
                    mass_condition_residual_g=mass_residual,
                    observation_notes=notes_val or "Imported from Google AppSheet historical database",
                    latitude=lat_val,
                    longitude=lon_val,
                    gps_accuracy_m=5.0 if (lat_val is not None and lon_val is not None) else None,
                    inspected_at=inspected_at
                )
                db.add(insp)
                inspections_created += 1

        if lat_val is not None and lon_val is not None:
            sighting = Sighting(
                id=str(uuid.uuid4()),
                specimen_id=sp.id,
                latitude=lat_val,
                longitude=lon_val,
                horizontal_accuracy=5.0,
                notes=notes_val or f"AppSheet GPS import for {sp.custom_identifier}",
                recorded_at=inspected_at
            )
            db.add(sighting)
            sightings_created += 1

    db.commit()
    return {
        "status": "success",
        "rows_processed": len(rows),
        "specimens_created": specimens_created,
        "specimens_updated": specimens_updated,
        "inspections_created": inspections_created,
        "sightings_created": sightings_created,
        "skipped_rows": skipped_rows,
        "applied_mapping": mapping
    }


@api_router.post("/imports/appsheet-rows")
def import_appsheet_rows(payload: AppSheetRowImportRequest, db: Session = Depends(get_db)):
    """Import parsed CSV rows from Google AppSheet Database with custom or auto-detected column mapping."""
    return _ingest_appsheet_rows(
        rows=payload.rows,
        db=db,
        column_mapping=payload.column_mapping,
        default_species_name=payload.default_species_name,
        default_common_name=payload.default_common_name,
        mass_unit=payload.mass_unit,
        length_unit=payload.length_unit
    )


@api_router.post("/imports/appsheet-cloud-sync")
def sync_from_appsheet_cloud(payload: AppSheetCloudSyncRequest, db: Session = Depends(get_db)):
    """
    Connect directly to Google AppSheet REST API v2:
    POST https://{region_host}/api/v2/apps/{app_id}/tables/{table_name}/Action
    with header ApplicationAccessKey and Action="Find", then preview or ingest all rows.
    """
    import urllib.request
    import urllib.parse
    import urllib.error
    import json

    host = payload.region_host.strip().replace("https://", "").replace("http://", "").strip("/")
    if host not in ("api.appsheet.com", "eu.appsheet.com"):
        host = "api.appsheet.com"

    encoded_table = urllib.parse.quote(payload.table_name.strip(), safe="")
    encoded_app = urllib.parse.quote(payload.app_id.strip(), safe="")
    url = f"https://{host}/api/v2/apps/{encoded_app}/tables/{encoded_table}/Action"

    props = {"Locale": "en-US"}
    if payload.selector and payload.selector.strip():
        props["Selector"] = payload.selector.strip()

    body_bytes = json.dumps({
        "Action": "Find",
        "Properties": props,
        "Rows": []
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body_bytes,
        headers={
            "ApplicationAccessKey": payload.access_key.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SATRA-AppSheet-Connector/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw_resp = resp.read().decode("utf-8")
            data = json.loads(raw_resp) if raw_resp.strip() else []
    except urllib.error.HTTPError as he:
        err_body = ""
        try:
            err_body = he.read().decode("utf-8")[:300]
        except Exception:
            pass
        raise HTTPException(
            status_code=400,
            detail=f"AppSheet API HTTP {he.code}: {err_body or he.reason}. Verify App ID, ApplicationAccessKey, and Table Name '{payload.table_name}'."
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to AppSheet REST API ({host}): {str(e)}"
        )

    rows = data if isinstance(data, list) else (data.get("Rows") or data.get("rows") or [])
    headers = list(rows[0].keys()) if rows else []
    detected_mapping = _auto_detect_appsheet_mapping(headers)

    if payload.preview_only:
        return {
            "status": "preview",
            "table_name": payload.table_name,
            "total_rows_found": len(rows),
            "headers": headers,
            "detected_mapping": detected_mapping,
            "sample_rows": rows[:5]
        }

    result = _ingest_appsheet_rows(
        rows=rows,
        db=db,
        column_mapping=payload.column_mapping,
        default_species_name=payload.default_species_name,
        default_common_name=payload.default_common_name,
        mass_unit=payload.mass_unit,
        length_unit=payload.length_unit
    )
    result["table_name"] = payload.table_name
    result["headers"] = headers
    return result

