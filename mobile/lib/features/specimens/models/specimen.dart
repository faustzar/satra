class Specimen {
  final String id;
  final String customIdentifier;
  final String species;
  final String commonName;
  final String? pitTagNumber;
  final String? notchCode;
  final String sex;
  final String status;
  final String? damId;
  final String? sireId;
  final DateTime createdAt;
  final bool isSynced;

  Specimen({
    required this.id,
    required this.customIdentifier,
    required this.species,
    required this.commonName,
    this.pitTagNumber,
    this.notchCode,
    required this.sex,
    required this.status,
    this.damId,
    this.sireId,
    required this.createdAt,
    this.isSynced = false,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'custom_identifier': customIdentifier,
      'species': species,
      'common_name': commonName,
      'pit_tag_number': pitTagNumber,
      'notch_code': notchCode,
      'sex': sex,
      'status': status,
      'dam_id': damId,
      'sire_id': sireId,
      'created_at': createdAt.toIso8601String(),
      'is_synced': isSynced ? 1 : 0,
    };
  }

  factory Specimen.fromMap(Map<String, dynamic> map) {
    return Specimen(
      id: map['id'],
      customIdentifier: map['custom_identifier'],
      species: map['species'],
      commonName: map['common_name'],
      pitTagNumber: map['pit_tag_number'],
      notchCode: map['notch_code'],
      sex: map['sex'],
      status: map['status'],
      damId: map['dam_id'],
      sireId: map['sire_id'],
      createdAt: DateTime.parse(map['created_at']),
      isSynced: (map['is_synced'] ?? 0) == 1,
    );
  }
}
