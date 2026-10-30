import 'dart:async';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('satra_offline.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future _createDB(Database db, int version) async {
    // Specimens Table
    await db.execute('''
      CREATE TABLE specimens (
        id TEXT PRIMARY KEY,
        custom_identifier TEXT NOT NULL UNIQUE,
        species TEXT NOT NULL,
        common_name TEXT NOT NULL,
        pit_tag_number TEXT,
        notch_code TEXT,
        sex TEXT NOT NULL,
        status TEXT NOT NULL,
        dam_id TEXT,
        sire_id TEXT,
        created_at TEXT NOT NULL,
        is_synced INTEGER NOT NULL DEFAULT 0
      )
    ''');

    // Sightings Table
    await db.execute('''
      CREATE TABLE sightings (
        id TEXT PRIMARY KEY,
        specimen_id TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        horizontal_accuracy REAL,
        habitat_type TEXT,
        ambient_temp_c REAL,
        photo_local_path TEXT,
        recorded_at TEXT NOT NULL,
        is_synced INTEGER NOT NULL DEFAULT 0
      )
    ''');

    // Health Inspections Table
    await db.execute('''
      CREATE TABLE health_inspections (
        id TEXT PRIMARY KEY,
        specimen_id TEXT NOT NULL,
        inspection_type TEXT NOT NULL,
        mass_grams REAL NOT NULL,
        straight_carapace_length_mm REAL NOT NULL,
        plastron_length_mm REAL,
        body_condition_score INTEGER NOT NULL,
        eggs_palpated INTEGER NOT NULL DEFAULT 0,
        estimated_egg_count INTEGER DEFAULT 0,
        jacksons_ratio REAL,
        shell_condition_notes TEXT,
        photo_local_path TEXT,
        inspected_at TEXT NOT NULL,
        is_synced INTEGER NOT NULL DEFAULT 0
      )
    ''');

    // Outbox Sync Queue for background sync
    await db.execute('''
      CREATE TABLE outbox_sync_queue (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        retry_count INTEGER NOT NULL DEFAULT 0,
        queued_at TEXT NOT NULL
      )
    ''');

    // Photo Records Table with Multi-Angle, Primary Avatar & Markings
    await db.execute('''
      CREATE TABLE photo_records (
        id TEXT PRIMARY KEY,
        specimen_id TEXT,
        inspection_id TEXT,
        sighting_id TEXT,
        photo_type TEXT NOT NULL,
        local_path TEXT NOT NULL,
        cloud_url TEXT,
        thumbnail_url TEXT,
        is_primary_avatar INTEGER NOT NULL DEFAULT 0,
        capture_context TEXT NOT NULL DEFAULT 'ResearchIntake',
        markings_json TEXT,
        exif_metadata TEXT,
        captured_at TEXT NOT NULL,
        is_synced INTEGER NOT NULL DEFAULT 0
      )
    ''');
  }

  Future close() async {
    final db = await instance.database;
    db.close();
  }
}
