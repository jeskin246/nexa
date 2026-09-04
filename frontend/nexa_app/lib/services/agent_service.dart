import 'dart:async';
import 'package:flutter/foundation.dart';
import '../core/websocket_service.dart';
import '../models/agent_state.dart';
import '../models/task.dart';

/// High-level service managing Agent state, active tasks, activity logs, and user confirmation dialogs.
class AgentService extends ChangeNotifier {
  final WebSocketService _ws;
  StreamSubscription? _sub;

  AgentState _state = AgentState.idle;
  String _statusMessage = 'NEXA is ready. What can I accomplish for you?';
  AgentTask? _activeTask;
  final List<Map<String, dynamic>> _activityFeed = [];
  Map<String, dynamic>? _pendingConfirmation;
  Map<String, dynamic>? _lastResult;

  AgentState get state => _state;
  String get statusMessage => _statusMessage;
  AgentTask? get activeTask => _activeTask;
  List<Map<String, dynamic>> get activityFeed => List.unmodifiable(_activityFeed);
  Map<String, dynamic>? get pendingConfirmation => _pendingConfirmation;
  Map<String, dynamic>? get lastResult => _lastResult;

  AgentService(this._ws) {
    _sub = _ws.messages.listen(_handleMessage);
  }

  void _handleMessage(Map<String, dynamic> msg) {
    final type = msg['type'] as String?;
    final taskId = msg['task_id'] as String?;
    final data = msg['data'] as Map<String, dynamic>?;

    switch (type) {
      case 'status':
        final stateStr = msg['state'] as String? ?? 'idle';
        _state = AgentState.fromString(stateStr);
        _statusMessage = msg['message'] as String? ?? _statusMessage;
        _logActivity('status', _statusMessage, data: msg);
        notifyListeners();
        break;

      case 'plan':
        if (data != null && taskId != null) {
          final stepsJson = (data['steps'] as List?)?.cast<Map<String, dynamic>>() ?? [];
          final steps = stepsJson.map((s) => TaskStep.fromJson(s)).toList();
          _activeTask = AgentTask(
            taskId: taskId,
            goal: data['understanding'] ?? 'Executing task',
            steps: steps,
            status: 'planning',
          );
          _logActivity('plan', 'Created execution plan with ${steps.length} steps');
          notifyListeners();
        }
        break;

      case 'step_update':
        if (data != null && _activeTask != null) {
          final stepIdx = data['step_index'] as int? ?? 0;
          final statusStr = data['status'] as String? ?? 'pending';
          final desc = data['description'] as String? ?? '';
          final pct = (data['percentage'] as num?)?.toDouble() ?? 0.0;

          _activeTask!.progress = pct / 100.0;
          if (stepIdx < _activeTask!.steps.length) {
            _activeTask!.steps[stepIdx].status = TaskStep.parseStatus(statusStr);
          }

          _logActivity('step', desc, data: data);
          notifyListeners();
        }
        break;

      case 'confirm_request':
        if (data != null) {
          _pendingConfirmation = {
            'task_id': taskId,
            'tool_name': data['tool_name'],
            'description': data['description'],
            'parameters': data['parameters'],
          };
          _state = AgentState.waiting;
          _logActivity('confirm_request', 'Confirmation required for: ${data['description']}');
          notifyListeners();
        }
        break;

      case 'task_complete':
        if (data != null) {
          final success = data['success'] as bool? ?? false;
          final summary = data['summary'] as String? ?? 'Task completed';
          _lastResult = data;
          if (_activeTask != null) {
            _activeTask!.status = success ? 'completed' : 'failed';
            _activeTask!.progress = 1.0;
            _activeTask!.summary = summary;
          }
          _logActivity('complete', summary, data: data);
          notifyListeners();
        }
        break;

      case 'error':
        _state = AgentState.error;
        _statusMessage = msg['message'] as String? ?? 'An error occurred';
        _logActivity('error', _statusMessage);
        notifyListeners();
        break;
    }
  }

  void submitGoal(String goal) {
    if (goal.trim().isEmpty) return;
    _activityFeed.clear();
    _lastResult = null;
    _pendingConfirmation = null;
    _activeTask = AgentTask(taskId: 'pending', goal: goal, status: 'starting');
    _ws.sendGoal(goal);
    _logActivity('user', goal);
  }

  void confirmAction(bool approved) {
    if (_pendingConfirmation != null) {
      final taskId = _pendingConfirmation!['task_id'] as String?;
      if (taskId != null) {
        if (approved) {
          _ws.sendConfirm(taskId);
        } else {
          _ws.sendDeny(taskId);
        }
      }
      _pendingConfirmation = null;
      notifyListeners();
    }
  }

  void stopAgent() {
    _ws.sendStop(taskId: _activeTask?.taskId);
    _state = AgentState.idle;
    _statusMessage = 'Emergency stop activated';
    _logActivity('stop', 'Emergency stop triggered by user');
    notifyListeners();
  }

  void _logActivity(String type, String message, {Map<String, dynamic>? data}) {
    _activityFeed.insert(0, {
      'timestamp': DateTime.now(),
      'type': type,
      'message': message,
      'data': data,
    });
    if (_activityFeed.length > 100) {
      _activityFeed.removeLast();
    }
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
