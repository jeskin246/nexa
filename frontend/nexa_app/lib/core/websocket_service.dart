import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'constants.dart';

/// WebSocket connection states
enum WsConnectionState { disconnected, connecting, connected, error }

/// WebSocket service for real-time communication with NEXA backend.
class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  WsConnectionState _state = WsConnectionState.disconnected;
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  Timer? _reconnectTimer;
  Timer? _pingTimer;
  String _lastError = '';

  WsConnectionState get state => _state;
  String get lastError => _lastError;
  Stream<Map<String, dynamic>> get messages => _messageController.stream;
  bool get isConnected => _state == WsConnectionState.connected;

  /// Connect to the NEXA backend WebSocket
  Future<void> connect({String? url}) async {
    if (_state == WsConnectionState.connecting) return;
    
    _state = WsConnectionState.connecting;
    notifyListeners();

    final List<String> candidateUrls = [];
    if (url != null) {
      candidateUrls.add(url);
    } else {
      candidateUrls.addAll([
        NexaConstants.wsUrl,            // ws://192.168.43.128:8000/ws
        'ws://192.168.43.128:8000/ws',   // Active PC Wi-Fi IP
        'ws://127.0.0.1:8000/ws',
        'ws://10.0.2.2:8000/ws',        // Android emulator fallback
      ]);
    }


    for (final wsUrl in candidateUrls) {
      try {
        _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
        await _channel!.ready.timeout(const Duration(seconds: 4));
        
        _state = WsConnectionState.connected;
        _lastError = '';
        notifyListeners();

        _channel!.stream.listen(
          _onMessage,
          onError: _onError,
          onDone: _onDone,
        );

        // Start ping timer
        _pingTimer?.cancel();
        _pingTimer = Timer.periodic(
          NexaConstants.wsPingInterval,
          (_) => send({'type': 'ping'}),
        );

        debugPrint('[NEXA WS] Connected to $wsUrl');
        return;
      } catch (e) {
        debugPrint('[NEXA WS] Connection to $wsUrl failed: $e');
      }
    }

    _state = WsConnectionState.error;
    _lastError = 'Could not connect to backend server at 172.20.189.128:8000';
    notifyListeners();
    _scheduleReconnect();
  }

  void _onMessage(dynamic data) {
    try {
      final message = jsonDecode(data as String) as Map<String, dynamic>;
      if (message['type'] != 'pong') {
        debugPrint('[NEXA WS] ← ${message['type']}');
      }
      _messageController.add(message);
    } catch (e) {
      debugPrint('[NEXA WS] Parse error: $e');
    }
  }

  void _onError(dynamic error) {
    debugPrint('[NEXA WS] Error: $error');
    _state = WsConnectionState.error;
    _lastError = error.toString();
    notifyListeners();
    _scheduleReconnect();
  }

  void _onDone() {
    debugPrint('[NEXA WS] Connection closed');
    _state = WsConnectionState.disconnected;
    _pingTimer?.cancel();
    notifyListeners();
    _scheduleReconnect();
  }

  /// Send a message to the backend
  void send(Map<String, dynamic> message) {
    if (_channel != null && _state == WsConnectionState.connected) {
      _channel!.sink.add(jsonEncode(message));
      if (message['type'] != 'ping') {
        debugPrint('[NEXA WS] → ${message['type']}');
      }
    }
  }

  /// Send a goal to the agent
  void sendGoal(String goal) {
    send({'type': 'goal', 'content': goal});
  }

  /// Confirm a permission request
  void sendConfirm(String taskId) {
    send({'type': 'confirm', 'task_id': taskId});
  }

  /// Deny a permission request
  void sendDeny(String taskId) {
    send({'type': 'deny', 'task_id': taskId});
  }

  /// Emergency stop
  void sendStop({String? taskId}) {
    final msg = <String, dynamic>{'type': 'stop'};
    if (taskId != null) msg['task_id'] = taskId;
    send(msg);
  }

  /// Request system info
  void requestSystemInfo() {
    send({'type': 'system_info'});
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(NexaConstants.wsReconnectDelay, connect);
  }

  /// Disconnect from the backend
  void disconnect() {
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    _state = WsConnectionState.disconnected;
    notifyListeners();
  }

  @override
  void dispose() {
    disconnect();
    _messageController.close();
    super.dispose();
  }
}
