import 'dart:async';
import 'package:flutter/foundation.dart';
import '../model/auto_reply_models.dart';
import '../service/nexo_notification_service.dart';
import '../storage/nexo_preferences.dart';

class AutoReplyManager extends ChangeNotifier {
  AutoReplySettings settings = AutoReplySettings();
  List<ReplyHistoryItem> history = [];
  List<ActivityLogEntry> activityLogs = [];
  Map<String, DateTime> lastReplyTimes = {};

  NexoStatus nexoStatus = NexoStatus.active;
  bool isPermissionGranted = false;

  int waitingSecondsRemaining = 0;
  String pendingSender = '';
  String pendingAppName = '';
  String pendingNotificationKey = '';
  String pendingPreviewText = '';
  ReplyHistoryItem? lastAutoReplyItem;

  Timer? _countdownTimer;
  StreamSubscription? _notificationSubscription;

  AutoReplyManager() {
    _init();
  }

  Future<void> _init() async {
    settings = await NexoPreferences.loadSettings();
    history = await NexoPreferences.loadHistory();
    activityLogs = await NexoPreferences.loadLogs();
    lastReplyTimes = await NexoPreferences.loadLastReplyTimes();

    if (history.isNotEmpty) {
      lastAutoReplyItem = history.first;
    }

    if (!settings.autoReplyEnabled) {
      nexoStatus = NexoStatus.off;
    }

    await checkPermission();
    _startListeningNotifications();
    notifyListeners();
  }

  Future<void> checkPermission() async {
    isPermissionGranted =
        await NexoNotificationService.isNotificationPermissionGranted();
    notifyListeners();
  }

  Future<void> requestPermission() async {
    await NexoNotificationService.openNotificationPermissionSettings();
    await Future.delayed(const Duration(seconds: 1));
    await checkPermission();
  }

  void _startListeningNotifications() {
    _notificationSubscription?.cancel();
    _notificationSubscription =
        NexoNotificationService.notificationStream.listen((event) {
      _handleIncomingNotification(event);
    });
  }

  String replaceVariables(
    String template, {
    required String sender,
    required String appName,
    required String username,
  }) {
    String text = template;
    text = text.replaceAll('(username)', username);
    text = text.replaceAll('(sender)', sender);
    text = text.replaceAll('(app)', appName);
    // Also support bracket curly formats
    text = text.replaceAll('{username}', username);
    text = text.replaceAll('{sender}', sender);
    text = text.replaceAll('{app}', appName);
    return text;
  }

  void _handleIncomingNotification(Map<String, dynamic> event) {
    final String notificationKey = event['notificationKey'] ?? '';
    final String appName = event['appName'] ?? '';
    final String sender = event['sender'] ?? '';
    final bool hasDirectReply = event['hasDirectReply'] ?? false;

    // 1. Check Master Switch
    if (!settings.autoReplyEnabled) {
      _addLog(
        'Notification received from $sender ($appName), but Auto-Reply is OFF.',
        ActivityLogStatus.skipped,
        appName: appName,
        sender: sender,
      );
      return;
    }

    // 2. Check Supported Apps
    if (settings.enabledApps[appName] != true) {
      _addLog(
        'Notification received from $sender ($appName), but $appName is OFF in Supported Apps.',
        ActivityLogStatus.skipped,
        appName: appName,
        sender: sender,
      );
      return;
    }

    // 3. Check User Status
    if (settings.userStatus != UserStatus.away) {
      _addLog(
        'Notification from $sender ($appName) ignored. User Status is ${settings.userStatus.displayName} (must be AWAY).',
        ActivityLogStatus.skipped,
        appName: appName,
        sender: sender,
      );
      return;
    }

    // 4. Log Detection
    _addLog(
      '$appName message detected from $sender',
      ActivityLogStatus.detected,
      appName: appName,
      sender: sender,
    );

    // 5. Check Direct Reply Action Availability
    if (!hasDirectReply && !notificationKey.startsWith('sim_')) {
      _addLog(
        'Direct reply unavailable for this message ($appName → $sender)',
        ActivityLogStatus.unsupported,
        appName: appName,
        sender: sender,
      );
      return;
    }

    // 6. Check Cooldown (Default 10 minutes per conversation)
    final conversationKey = '$appName:$sender';
    final lastTime = lastReplyTimes[conversationKey];
    if (lastTime != null) {
      final difference = DateTime.now().difference(lastTime);
      if (difference < Duration(minutes: settings.cooldownMinutes)) {
        _addLog(
          'Cooldown active for $sender ($appName). Skipping auto-reply.',
          ActivityLogStatus.cooldown,
          appName: appName,
          sender: sender,
        );
        return;
      }
    }

    // 7. Start waiting period
    _startWaitingPeriod(
      notificationKey: notificationKey,
      appName: appName,
      sender: sender,
    );
  }

  void simulateIncomingMessage({String appName = 'WhatsApp', String sender = 'John'}) {
    final simKey = 'sim_${DateTime.now().millisecondsSinceEpoch}';
    _handleIncomingNotification({
      'notificationKey': simKey,
      'appName': appName,
      'packageName': appName == 'WhatsApp' ? 'com.whatsapp' : 'com.instagram.android',
      'sender': sender,
      'message': 'Hello, are you free to talk?',
      'hasDirectReply': true,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    });
  }

  void _startWaitingPeriod({
    required String notificationKey,
    required String appName,
    required String sender,
  }) {
    _countdownTimer?.cancel();

    pendingNotificationKey = notificationKey;
    pendingAppName = appName;
    pendingSender = sender;
    pendingPreviewText = replaceVariables(
      settings.replyTemplate,
      sender: sender,
      appName: appName,
      username: settings.username,
    );

    waitingSecondsRemaining = settings.replyDelaySeconds;
    nexoStatus = NexoStatus.waiting;

    _addLog(
      'Waiting ${settings.replyDelaySeconds}s before replying to $sender ($appName)...',
      ActivityLogStatus.waiting,
      appName: appName,
      sender: sender,
    );

    notifyListeners();

    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (settings.userStatus == UserStatus.available) {
        timer.cancel();
        _cancelReplyUserAvailable();
        return;
      }

      if (!settings.autoReplyEnabled) {
        timer.cancel();
        waitingSecondsRemaining = 0;
        nexoStatus = NexoStatus.off;
        notifyListeners();
        return;
      }

      waitingSecondsRemaining--;
      if (waitingSecondsRemaining <= 0) {
        timer.cancel();
        _executeAutoReply();
      } else {
        notifyListeners();
      }
    });
  }

  void _cancelReplyUserAvailable() {
    waitingSecondsRemaining = 0;
    nexoStatus = NexoStatus.active;
    _addLog(
      'AUTO-REPLY CANCELLED: User is available.',
      ActivityLogStatus.skipped,
      appName: pendingAppName,
      sender: pendingSender,
    );
    pendingNotificationKey = '';
    pendingSender = '';
    pendingAppName = '';
    pendingPreviewText = '';
    notifyListeners();
  }

  Future<void> _executeAutoReply() async {
    if (!settings.autoReplyEnabled ||
        settings.userStatus != UserStatus.away ||
        pendingNotificationKey.isEmpty) {
      nexoStatus =
          settings.autoReplyEnabled ? NexoStatus.active : NexoStatus.off;
      notifyListeners();
      return;
    }

    nexoStatus = NexoStatus.processing;
    _addLog(
      'Cooldown check passed. Sending direct reply to $pendingSender ($pendingAppName)...',
      ActivityLogStatus.waiting,
      appName: pendingAppName,
      sender: pendingSender,
    );
    notifyListeners();

    final String finalReplyText = pendingPreviewText;
    final String key = pendingNotificationKey;
    final String appName = pendingAppName;
    final String sender = pendingSender;

    final bool success = key.startsWith('sim_')
        ? true
        : await NexoNotificationService.sendDirectReply(key, finalReplyText);

    if (success) {
      final now = DateTime.now();
      lastReplyTimes['$appName:$sender'] = now;
      await NexoPreferences.saveLastReplyTimes(lastReplyTimes);

      final newItem = ReplyHistoryItem(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        appName: appName,
        sender: sender,
        templateMessage: settings.replyTemplate,
        sentMessage: finalReplyText,
        status: '✓ SENT',
        timestamp: now,
      );

      history.insert(0, newItem);
      lastAutoReplyItem = newItem;
      await NexoPreferences.saveHistory(history);

      nexoStatus = NexoStatus.success;
      _addLog(
        'Reply sent ✓ to $sender ($appName)',
        ActivityLogStatus.sent,
        appName: appName,
        sender: sender,
      );
    } else {
      nexoStatus = NexoStatus.error;
      _addLog(
        'AUTO-REPLY FAILED: NEXO could not send the reply.',
        ActivityLogStatus.failed,
        appName: appName,
        sender: sender,
      );
    }

    waitingSecondsRemaining = 0;
    pendingNotificationKey = '';
    pendingSender = '';
    pendingAppName = '';
    pendingPreviewText = '';
    notifyListeners();

    // Reset status back to active after 3 seconds
    Timer(const Duration(seconds: 3), () {
      if (nexoStatus == NexoStatus.success || nexoStatus == NexoStatus.error) {
        nexoStatus =
            settings.autoReplyEnabled ? NexoStatus.active : NexoStatus.off;
        notifyListeners();
      }
    });
  }

  void setMasterSwitch(bool value) {
    settings.autoReplyEnabled = value;
    if (!value) {
      _countdownTimer?.cancel();
      waitingSecondsRemaining = 0;
      nexoStatus = NexoStatus.off;
      _addLog('Auto-Reply master switch turned OFF', ActivityLogStatus.skipped);
    } else {
      nexoStatus = NexoStatus.active;
      _addLog('Auto-Reply master switch turned ON', ActivityLogStatus.detected);
    }
    NexoPreferences.saveSettings(settings);
    notifyListeners();
  }

  void cancelPendingReply() {
    _countdownTimer?.cancel();
    final appName = pendingAppName;
    final sender = pendingSender;

    waitingSecondsRemaining = 0;
    nexoStatus = settings.autoReplyEnabled ? NexoStatus.active : NexoStatus.off;

    _addLog(
      'AUTO-REPLY CANCELLED by user for $sender ($appName)',
      ActivityLogStatus.skipped,
      appName: appName,
      sender: sender,
    );

    pendingNotificationKey = '';
    pendingSender = '';
    pendingAppName = '';
    pendingPreviewText = '';
    notifyListeners();
  }

  bool updateReplyDelay(int totalSeconds) {
    if (totalSeconds <= 0) return false;
    settings.replyDelaySeconds = totalSeconds;
    NexoPreferences.saveSettings(settings);
    _addLog(
      'Reply delay updated to ${settings.formattedDelayText}',
      ActivityLogStatus.detected,
    );
    notifyListeners();
    return true;
  }

  void stopAutoReply() {
    settings.autoReplyEnabled = false;
    _countdownTimer?.cancel();
    waitingSecondsRemaining = 0;
    nexoStatus = NexoStatus.off;
    _addLog('AUTO-REPLY STOPPED', ActivityLogStatus.skipped);
    NexoPreferences.saveSettings(settings);
    notifyListeners();
  }

  void setUserStatus(UserStatus status) {
    settings.userStatus = status;
    if (status == UserStatus.available && _countdownTimer?.isActive == true) {
      _countdownTimer?.cancel();
      _cancelReplyUserAvailable();
    }
    NexoPreferences.saveSettings(settings);
    notifyListeners();
  }

  void toggleApp(String appName, bool enabled) {
    settings.enabledApps[appName] = enabled;
    NexoPreferences.saveSettings(settings);
    notifyListeners();
  }

  void updateTemplate(String newTemplate) {
    settings.replyTemplate = newTemplate;
    NexoPreferences.saveSettings(settings);
    notifyListeners();
  }

  void updateUsername(String newUsername) {
    settings.username = newUsername;
    NexoPreferences.saveSettings(settings);
    notifyListeners();
  }

  void clearHistory() {
    history.clear();
    lastAutoReplyItem = null;
    NexoPreferences.saveHistory(history);
    notifyListeners();
  }

  void _addLog(
    String text,
    ActivityLogStatus status, {
    String appName = '',
    String sender = '',
  }) {
    final entry = ActivityLogEntry(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      timestamp: DateTime.now(),
      text: text,
      status: status,
      appName: appName,
      sender: sender,
    );
    activityLogs.insert(0, entry);
    NexoPreferences.saveLogs(activityLogs);
    notifyListeners();
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _notificationSubscription?.cancel();
    super.dispose();
  }
}
