import 'dart:async';
import 'package:flutter/foundation.dart';
import '../core/websocket_service.dart';

/// Periodically requests telemetry data and maintains system status.
class SystemMonitorService extends ChangeNotifier {
  final WebSocketService _ws;
  StreamSubscription? _sub;
  Timer? _pollTimer;

  double _cpuPercent = 0.0;
  double _memoryPercent = 0.0;
  double _diskPercent = 0.0;
  int _processCount = 0;
  int _networkSent = 0;
  int _networkRecv = 0;
  String _activeWindow = '';
  double? _batteryPercent;
  bool? _batteryCharging;

  double get cpuPercent => _cpuPercent;
  double get memoryPercent => _memoryPercent;
  double get diskPercent => _diskPercent;
  int get processCount => _processCount;
  int get networkSent => _networkSent;
  int get networkRecv => _networkRecv;
  String get activeWindow => _activeWindow;
  double? get batteryPercent => _batteryPercent;
  bool? get batteryCharging => _batteryCharging;

  SystemMonitorService(this._ws) {
    _sub = _ws.messages.listen(_handleMessage);
    _startPolling();
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (_ws.isConnected) {
        _ws.requestSystemInfo();
      }
    });
  }

  void _handleMessage(Map<String, dynamic> msg) {
    if (msg['type'] == 'system_data' && msg['data'] != null) {
      final data = msg['data'] as Map<String, dynamic>;
      final newCpu = (data['cpu_percent'] as num?)?.toDouble() ?? 0.0;
      final newMem = (data['memory_percent'] as num?)?.toDouble() ?? 0.0;

      if ((newCpu - _cpuPercent).abs() > 0.01 || (newMem - _memoryPercent).abs() > 0.01) {
        _cpuPercent = newCpu;
        _memoryPercent = newMem;
        _diskPercent = (data['disk_percent'] as num?)?.toDouble() ?? 0.0;
        _processCount = (data['process_count'] as num?)?.toInt() ?? 0;
        _networkSent = (data['network_sent'] as num?)?.toInt() ?? 0;
        _networkRecv = (data['network_recv'] as num?)?.toInt() ?? 0;
        _activeWindow = data['active_window'] as String? ?? '';

        final battery = data['battery'] as Map<String, dynamic>?;
        if (battery != null) {
          _batteryPercent = (battery['percent'] as num?)?.toDouble();
          _batteryCharging = battery['charging'] as bool?;
        }

        notifyListeners();
      }
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _sub?.cancel();
    super.dispose();
  }
}
