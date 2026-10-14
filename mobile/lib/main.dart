import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/constants/colors.dart';
import 'features/specimens/presentation/specimen_list_screen.dart';
import 'features/sightings/presentation/log_sighting_screen.dart';
import 'features/health/presentation/health_inspection_screen.dart';
import 'features/breeding/presentation/breeding_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: SatraApp()));
}

class SatraApp extends StatefulWidget {
  const SatraApp({super.key});

  @override
  State<SatraApp> createState() => _SatraAppState();
}

class _SatraAppState extends State<SatraApp> {
  bool _highContrastFieldMode = false;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SATRA Tortoise Management',
      debugShowCheckedModeBanner: false,
      theme: _highContrastFieldMode
          ? ThemeData(
              brightness: Brightness.dark,
              scaffoldBackgroundColor: AppColors.fieldHighContrastBg,
              primaryColor: AppColors.fieldHighContrastYellow,
              cardColor: const Color(0xFF1A1A1A),
              colorScheme: const ColorScheme.dark(
                primary: AppColors.fieldHighContrastYellow,
                secondary: AppColors.fieldHighContrastYellow,
                surface: Color(0xFF1A1A1A),
              ),
              appBarTheme: const AppBarTheme(
                backgroundColor: Colors.black,
                foregroundColor: AppColors.fieldHighContrastYellow,
                elevation: 0,
              ),
            )
          : ThemeData(
              useMaterial3: true,
              colorScheme: ColorScheme.fromSeed(
                seedColor: AppColors.primaryGreen,
                primary: AppColors.primaryGreen,
                secondary: AppColors.accentGold,
              ),
              scaffoldBackgroundColor: AppColors.backgroundLight,
              appBarTheme: const AppBarTheme(
                backgroundColor: AppColors.primaryGreen,
                foregroundColor: Colors.white,
                elevation: 0,
              ),
            ),
      home: MainNavigationShell(
        isHighContrast: _highContrastFieldMode,
        onToggleContrast: () {
          setState(() => _highContrastFieldMode = !_highContrastFieldMode);
        },
      ),
    );
  }
}

class MainNavigationShell extends StatefulWidget {
  final bool isHighContrast;
  final VoidCallback onToggleContrast;

  const MainNavigationShell({
    super.key,
    required this.isHighContrast,
    required this.onToggleContrast,
  });

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    SpecimenListScreen(),
    LogSightingScreen(),
    HealthInspectionScreen(),
    BreedingScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() => _currentIndex = index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.cruelty_free),
            label: "Tortoises",
          ),
          NavigationDestination(
            icon: Icon(Icons.camera_alt),
            label: "Sighting",
          ),
          NavigationDestination(
            icon: Icon(Icons.medical_services),
            label: "Health",
          ),
          NavigationDestination(
            icon: Icon(Icons.egg),
            label: "Breeding",
          ),
        ],
      ),
    );
  }
}
