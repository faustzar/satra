import 'dart:convert';

class PhotoRecord {
  final String id;
  final String? specimenId;
  final String? inspectionId;
  final String? sightingId;
  final String photoType; // Carapace, Plastron, Head, Caudal, Lateral, Injury
  final String localPath;
  final String? cloudUrl;
  final String? thumbnailUrl;
  final bool isPrimaryAvatar;
  final String captureContext; // CitizenSpotted, ResearchIntake, ClinicalRounds, AdHoc
  final List<PhotoMarking> markings;
  final Map<String, dynamic>? exifMetadata;
  final DateTime capturedAt;
  final bool isSynced;

  PhotoRecord({
    required this.id,
    this.specimenId,
    this.inspectionId,
    this.sightingId,
    required this.photoType,
    required this.localPath,
    this.cloudUrl,
    this.thumbnailUrl,
    this.isPrimaryAvatar = false,
    this.captureContext = 'ResearchIntake',
    this.markings = const [],
    this.exifMetadata,
    required this.capturedAt,
    this.isSynced = false,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'specimen_id': specimenId,
      'inspection_id': inspectionId,
      'sighting_id': sightingId,
      'photo_type': photoType,
      'local_path': localPath,
      'cloud_url': cloudUrl,
      'thumbnail_url': thumbnailUrl,
      'is_primary_avatar': isPrimaryAvatar ? 1 : 0,
      'capture_context': captureContext,
      'markings_json': jsonEncode(markings.map((m) => m.toMap()).toList()),
      'exif_metadata': exifMetadata != null ? jsonEncode(exifMetadata) : null,
      'captured_at': capturedAt.toIso8601String(),
      'is_synced': isSynced ? 1 : 0,
    };
  }

  factory PhotoRecord.fromMap(Map<String, dynamic> map) {
    List<PhotoMarking> parsedMarkings = [];
    if (map['markings_json'] != null) {
      try {
        final decoded = jsonDecode(map['markings_json']) as List;
        parsedMarkings = decoded.map((item) => PhotoMarking.fromMap(item)).toList();
      } catch (_) {}
    }

    Map<String, dynamic>? parsedExif;
    if (map['exif_metadata'] != null) {
      try {
        parsedExif = jsonDecode(map['exif_metadata']);
      } catch (_) {}
    }

    return PhotoRecord(
      id: map['id'],
      specimenId: map['specimen_id'],
      inspectionId: map['inspection_id'],
      sightingId: map['sighting_id'],
      photoType: map['photo_type'] ?? 'Carapace',
      localPath: map['local_path'] ?? '',
      cloudUrl: map['cloud_url'],
      thumbnailUrl: map['thumbnail_url'],
      isPrimaryAvatar: (map['is_primary_avatar'] ?? 0) == 1,
      captureContext: map['capture_context'] ?? 'ResearchIntake',
      markings: parsedMarkings,
      exifMetadata: parsedExif,
      capturedAt: DateTime.parse(map['captured_at']),
      isSynced: (map['is_synced'] ?? 0) == 1,
    );
  }
}

class PhotoMarking {
  final String id;
  final String type; // V-Notch, U-Notch, Micro-Drill, Epoxy Tag, Predation Scar, Natural Scar
  final String scute;
  final String label;
  final double xPercent;
  final double yPercent;

  PhotoMarking({
    required this.id,
    required this.type,
    required this.scute,
    required this.label,
    required this.xPercent,
    required this.yPercent,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'type': type,
      'scute': scute,
      'label': label,
      'x': xPercent,
      'y': yPercent,
    };
  }

  factory PhotoMarking.fromMap(Map<String, dynamic> map) {
    return PhotoMarking(
      id: map['id'] ?? '',
      type: map['type'] ?? 'V-Notch',
      scute: map['scute'] ?? 'Unspecified',
      label: map['label'] ?? '',
      xPercent: (map['x'] as num?)?.toDouble() ?? 50.0,
      yPercent: (map['y'] as num?)?.toDouble() ?? 50.0,
    );
  }
}
