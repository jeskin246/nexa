import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import '../model/system_automation_models.dart';
import '../storage/automation_preferences.dart';

class SystemAutomationManager extends ChangeNotifier {
  static const MethodChannel _methodChannel =
      MethodChannel('com.nexa.nexa_app/automation');
  static const EventChannel _eventChannel =
      EventChannel('com.nexa.nexa_app/automation_events');

  List<ScheduledAutomationTask> tasks = [];
  AutomationSecuritySettings securitySettings = AutomationSecuritySettings();

  bool isScreenOn = true;
  bool isDeviceLocked = false;
  bool isDeviceAuthenticated = true;
  bool isUserUnlocked = true;

  StreamSubscription? _eventSubscription;

  SystemAutomationManager() {
    _init();
  }

  Future<void> _init() async {
    tasks = await AutomationPreferences.loadTasks();
    securitySettings = await AutomationPreferences.loadSecuritySettings();

    await fetchDeviceState();
    _startListeningEvents();
    notifyListeners();
  }

  void _startListeningEvents() {
    _eventSubscription?.cancel();
    try {
      _eventSubscription =
          _eventChannel.receiveBroadcastStream().listen((dynamic event) {
        if (event is Map) {
          final map = Map<String, dynamic>.from(event);
          _handleNativeAutomationEvent(map);
        }
      }, onError: (err) {
        debugPrint('[SystemAutomationManager] Event error: $err');
      });
    } catch (e) {
      debugPrint('[SystemAutomationManager] Could not subscribe to event channel: $e');
    }
  }

  void _handleNativeAutomationEvent(Map<String, dynamic> event) {
    final String taskId = event['taskId'] ?? '';
    final String statusStr = event['status'] ?? '';
    final String logText = event['log'] ?? '';

    debugPrint('[SystemAutomationManager] Native Event: $taskId status=$statusStr ($logText)');

    // Refresh device state
    fetchDeviceState();

    if (taskId.isEmpty) return;

    final index = tasks.indexWhere((t) => t.taskId == taskId);
    if (index != -1) {
      final task = tasks[index];

      // Duplicate prevention check: if already sent, ignore repeats
      if (task.status == AutomationTaskState.sent && statusStr != 'SENT') {
        return;
      }

      switch (statusStr) {
        case 'TRIGGERED':
          task.status = AutomationTaskState.triggered;
          break;
        case 'CHECKING_DEVICE':
          task.status = AutomationTaskState.checkingDevice;
          break;
        case 'DEVICE_LOCKED':
          task.status = AutomationTaskState.deviceLocked;
          break;
        case 'SYSTEM_AUTHENTICATION':
          task.status = AutomationTaskState.systemAuthentication;
          break;
        case 'AUTHENTICATED':
          task.status = AutomationTaskState.authenticated;
          break;
        case 'WHATSAPP_READY':
          task.status = AutomationTaskState.whatsappReady;
          break;
        case 'COMPOSING':
          task.status = AutomationTaskState.composing;
          break;
        case 'SENDING':
          task.status = AutomationTaskState.sending;
          break;
        case 'VERIFYING':
          task.status = AutomationTaskState.verifying;
          break;
        case 'SENT':
          task.status = AutomationTaskState.sent;
          break;
        case 'WAITING':
          task.status = AutomationTaskState.waiting;
          break;
        case 'WAITING_FOR_AUTHENTICATION':
          task.status = AutomationTaskState.waitingForAuthentication;
          break;
        case 'WAITING_FOR_UNLOCK':
          task.status = AutomationTaskState.waitingForUnlock;
          break;
        case 'WHATSAPP_UNAVAILABLE':
          task.status = AutomationTaskState.whatsappUnavailable;
          task.lastError = logText;
          break;
        case 'NETWORK_ERROR':
          task.status = AutomationTaskState.networkError;
          task.lastError = logText;
          break;
        case 'SEND_FAILED':
        case 'FAILED':
          task.status = AutomationTaskState.sendFailed;
          task.lastError = logText;
          break;
        case 'VERIFICATION_FAILED':
          task.status = AutomationTaskState.verificationFailed;
          task.lastError = logText;
          break;
        case 'CANCELLED':
          task.status = AutomationTaskState.cancelled;
          break;
      }

      AutomationPreferences.saveTasks(tasks);
      notifyListeners();
    }
  }

  Future<void> fetchDeviceState() async {
    try {
      final Map<dynamic, dynamic>? res =
          await _methodChannel.invokeMethod('getDeviceState');
      if (res != null) {
        isScreenOn = res['isScreenOn'] ?? true;
        isDeviceLocked = res['isDeviceLocked'] ?? false;
        isDeviceAuthenticated = res['isDeviceAuthenticated'] ?? true;
        isUserUnlocked = res['isUserUnlocked'] ?? true;
        notifyListeners();
      }
    } catch (e) {
      debugPrint('[SystemAutomationManager] Error fetching device state: $e');
    }
  }

  Future<bool> createTask({
    required String recipient,
    required String message,
    required DateTime scheduledDateTime,
  }) async {
    final now = DateTime.now();
    final rand = Random().nextInt(99999);
    final taskId = 'task_wa_${now.millisecondsSinceEpoch}';
    final executionId = 'exec_wa_${now.millisecondsSinceEpoch}_$rand';

    final newTask = ScheduledAutomationTask(
      taskId: taskId,
      executionId: executionId,
      recipient: recipient,
      message: message,
      scheduledDateTime: scheduledDateTime,
      timezone: DateTime.now().timeZoneName,
      status: AutomationTaskState.scheduled,
      createdAt: now,
      isEnabled: true,
    );

    tasks.insert(0, newTask);
    await AutomationPreferences.saveTasks(tasks);

    // Schedule native exact alarm
    try {
      await _methodChannel.invokeMethod('scheduleTask', {
        'taskId': taskId,
        'executionId': executionId,
        'recipient': recipient,
        'message': message,
        'timestamp': scheduledDateTime.millisecondsSinceEpoch,
      });
    } catch (e) {
      debugPrint('[SystemAutomationManager] Error calling native scheduleTask: $e');
    }

    notifyListeners();
    return true;
  }

  Future<void> toggleTask(String taskId, bool isEnabled) async {
    final index = tasks.indexWhere((t) => t.taskId == taskId);
    if (index != -1) {
      tasks[index].isEnabled = isEnabled;
      if (!isEnabled) {
        tasks[index].status = AutomationTaskState.cancelled;
        try {
          await _methodChannel.invokeMethod('cancelTask', {'taskId': taskId});
        } catch (_) {}
      } else {
        tasks[index].status = AutomationTaskState.scheduled;
        try {
          await _methodChannel.invokeMethod('scheduleTask', {
            'taskId': tasks[index].taskId,
            'executionId': tasks[index].executionId,
            'recipient': tasks[index].recipient,
            'message': tasks[index].message,
            'timestamp': tasks[index].scheduledDateTime.millisecondsSinceEpoch,
          });
        } catch (_) {}
      }
      await AutomationPreferences.saveTasks(tasks);
      notifyListeners();
    }
  }

  Future<void> cancelTask(String taskId) async {
    final index = tasks.indexWhere((t) => t.taskId == taskId);
    if (index != -1) {
      tasks[index].status = AutomationTaskState.cancelled;
      tasks[index].isEnabled = false;
      try {
        await _methodChannel.invokeMethod('cancelTask', {'taskId': taskId});
      } catch (_) {}
      await AutomationPreferences.saveTasks(tasks);
      notifyListeners();
    }
  }

  Future<void> deleteTask(String taskId) async {
    try {
      await _methodChannel.invokeMethod('cancelTask', {'taskId': taskId});
    } catch (_) {}
    tasks.removeWhere((t) => t.taskId == taskId);
    await AutomationPreferences.saveTasks(tasks);
    notifyListeners();
  }

  Future<void> updateSecuritySettings(
      AutomationSecuritySettings newSettings) async {
    securitySettings = newSettings;
    await AutomationPreferences.saveSecuritySettings(securitySettings);
    notifyListeners();
  }

  Future<void> openAutostartSettings() async {
    try {
      await _methodChannel.invokeMethod('openAutostartSettings');
    } catch (e) {
      debugPrint('[SystemAutomationManager] Error opening autostart settings: $e');
    }
  }

  Future<void> openBatteryOptimizationSettings() async {
    try {
      await _methodChannel.invokeMethod('openBatteryOptimizationSettings');
    } catch (e) {
      debugPrint('[SystemAutomationManager] Error opening battery optimization: $e');
    }
  }

  Future<bool> canScheduleExactAlarms() async {
    try {
      final bool? res = await _methodChannel.invokeMethod('canScheduleExactAlarms');
      return res ?? true;
    } catch (e) {
      return true;
    }
  }

  Future<void> openExactAlarmSettings() async {
    try {
      await _methodChannel.invokeMethod('openExactAlarmSettings');
    } catch (e) {
      debugPrint('[SystemAutomationManager] Error opening exact alarm settings: $e');
    }
  }

  Future<void> openAccessibilitySettings() async {
    try {
      await _methodChannel.invokeMethod('openAccessibilitySettings');
    } catch (e) {
      debugPrint('[SystemAutomationManager] Error opening accessibility settings: $e');
    }
  }

  @override
  void dispose() {
    _eventSubscription?.cancel();
    super.dispose();
  }
}
