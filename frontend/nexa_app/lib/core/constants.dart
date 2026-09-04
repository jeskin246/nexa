/// NEXA App Constants
class NexaConstants {
  static const String appName = 'NEXA';
  static const String appVersion = '0.1.0';
  static const String appTagline = 'Agentic AI Personal OS Assistant';

  // WebSocket & Backend API (Wi-Fi IP for direct physical device connection)
  static const String serverHost = '10.69.218.128';
  static const String wsUrl = 'ws://$serverHost:8000/ws';
  static const String apiBaseUrl = 'http://$serverHost:8000';
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
