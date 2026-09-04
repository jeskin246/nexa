/// NEXA App Constants
class NexaConstants {
  static const String appName = 'NEXA';
  static const String appVersion = '0.1.0';
  static const String appTagline = 'Agentic AI Personal OS Assistant';

  // Global 24/7 Cloud Backend (Render HTTPS & WSS)
  static const String serverHost = 'nexa-backend-pqhw.onrender.com';
  static const String wsUrl = 'wss://$serverHost/ws';
  static const String apiBaseUrl = 'https://$serverHost';
  static const Duration wsReconnectDelay = Duration(seconds: 3);
  static const Duration wsPingInterval = Duration(seconds: 30);

  // Animation durations
  static const Duration animFast = Duration(milliseconds: 200);
  static const Duration animNormal = Duration(milliseconds: 400);
  static const Duration animSlow = Duration(milliseconds: 800);
  static const Duration animVerySlow = Duration(milliseconds: 1500);

  // Layout
  static const double minWindowWidth = 1024;
  static const double minWindowHeight = 700;
  static const double panelWidth = 320;
  static const double telemetryHeight = 48;
  static const double inputBarHeight = 72;

  // System monitor polling
  static const Duration systemPollInterval = Duration(seconds: 3);
}
