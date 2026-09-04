import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// NEXA Futuristic Dark Theme
class NexaTheme {
  // ─── Colors ────────────────────────────────────────────────────
  static const Color bgDeep = Color(0xFF060610);
  static const Color bgPrimary = Color(0xFF0a0a14);
  static const Color bgSecondary = Color(0xFF10101e);
  static const Color bgPanel = Color(0xFF14142a);
  static const Color bgCard = Color(0xFF1a1a33);

  static const Color accentCyan = Color(0xFF00d4ff);
  static const Color accentBlue = Color(0xFF0099ff);
  static const Color accentPurple = Color(0xFF8b5cf6);
  static const Color accentPink = Color(0xFFe879f9);
  static const Color accentGreen = Color(0xFF22d3ee);

  static const Color neonCyan = accentCyan;
  static const Color neonPurple = accentPurple;
  static const Color surfaceColor = bgSecondary;
  static const Color backgroundColor = bgDeep;
  static const LinearGradient primaryGradient = coreGradient;

  static const Color successGreen = Color(0xFF10b981);
  static const Color warningAmber = Color(0xFFf59e0b);
  static const Color errorRed = Color(0xFFef4444);

  static const Color textPrimary = Color(0xFFe2e8f0);
  static const Color textSecondary = Color(0xFF94a3b8);
  static const Color textDim = Color(0xFF475569);

  static const Color glassBorder = Color(0x20ffffff);
  static const Color glassHighlight = Color(0x10ffffff);

  // ─── Gradients ─────────────────────────────────────────────────
  static const LinearGradient coreGradient = LinearGradient(
    colors: [accentCyan, accentBlue, accentPurple],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient bgGradient = LinearGradient(
    colors: [bgDeep, bgPrimary, Color(0xFF0d0d1a)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  static const LinearGradient panelGradient = LinearGradient(
    colors: [Color(0x15ffffff), Color(0x08ffffff)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // ─── Shadows ───────────────────────────────────────────────────
  static List<BoxShadow> glowShadow(Color color, {double blur = 20}) {
    return [
      BoxShadow(
        color: color.withValues(alpha: 0.3),
        blurRadius: blur,
        spreadRadius: 2,
      ),
    ];
  }

  static List<BoxShadow> cyanGlow = glowShadow(accentCyan);
  static List<BoxShadow> purpleGlow = glowShadow(accentPurple);

  // ─── Glass Decoration ─────────────────────────────────────────
  static BoxDecoration glassDecoration({
    double borderRadius = 16,
    Color? borderColor,
  }) {
    return BoxDecoration(
      color: const Color(0x15ffffff),
      borderRadius: BorderRadius.circular(borderRadius),
      border: Border.all(
        color: borderColor ?? glassBorder,
        width: 1,
      ),
      gradient: panelGradient,
    );
  }

  // ─── Theme Data ────────────────────────────────────────────────
  static ThemeData get darkTheme {
    final textTheme = GoogleFonts.interTextTheme(
      ThemeData.dark().textTheme,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bgDeep,
      colorScheme: const ColorScheme.dark(
        primary: accentCyan,
        secondary: accentPurple,
        surface: bgSecondary,
        error: errorRed,
        onPrimary: bgDeep,
        onSecondary: Colors.white,
        onSurface: textPrimary,
        onError: Colors.white,
      ),
      textTheme: textTheme.copyWith(
        headlineLarge: textTheme.headlineLarge?.copyWith(
          color: textPrimary,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.5,
        ),
        headlineMedium: textTheme.headlineMedium?.copyWith(
          color: textPrimary,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: textTheme.bodyLarge?.copyWith(color: textPrimary),
        bodyMedium: textTheme.bodyMedium?.copyWith(color: textSecondary),
        bodySmall: textTheme.bodySmall?.copyWith(color: textDim),
        labelLarge: textTheme.labelLarge?.copyWith(
          color: accentCyan,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.2,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      cardTheme: CardThemeData(
        color: bgCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: glassBorder),
        ),
      ),
      iconTheme: const IconThemeData(color: textSecondary, size: 20),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0x10ffffff),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: glassBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: glassBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: accentCyan, width: 1.5),
        ),
        hintStyle: const TextStyle(color: textDim),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 20,
          vertical: 16,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accentCyan,
          foregroundColor: bgDeep,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),
    );
  }
}
