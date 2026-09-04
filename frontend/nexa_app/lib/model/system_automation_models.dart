enum AutomationTaskState {
  scheduled,
  triggered,
  checkingDevice,
  deviceLocked,
  waitingForUnlock,
  systemAuthentication,
  authenticated,
  ready,
  whatsappReady,
  composing,
  sending,
  verifying,
  executing,
  sent,
  waiting,
  waitingForAuthentication,
  whatsappUnavailable,
  networkError,
  sendFailed,
  verificationFailed,
  failed,
  cancelled,
}

extension AutomationTaskStateExtension on AutomationTaskState {
  String get displayName {
    switch (this) {
      case AutomationTaskState.scheduled:
        return 'Scheduled';
      case AutomationTaskState.triggered:
        return 'Triggered';
      case AutomationTaskState.checkingDevice:
        return 'Checking Device';
      case AutomationTaskState.deviceLocked:
        return 'Device Locked';
      case AutomationTaskState.waitingForUnlock:
        return 'Waiting for Unlock 🔒';
      case AutomationTaskState.systemAuthentication:
        return 'System Authentication';
      case AutomationTaskState.authenticated:
        return 'Authenticated';
      case AutomationTaskState.ready:
        return 'Ready';
      case AutomationTaskState.whatsappReady:
        return 'WhatsApp Ready';
      case AutomationTaskState.composing:
        return 'Composing';
      case AutomationTaskState.sending:
        return 'Sending';
      case AutomationTaskState.verifying:
        return 'Verifying Delivery';
      case AutomationTaskState.executing:
        return 'Executing';
      case AutomationTaskState.sent:
        return 'Sent ✓';
      case AutomationTaskState.waiting:
        return 'Waiting';
      case AutomationTaskState.waitingForAuthentication:
        return 'Waiting for System Auth';
      case AutomationTaskState.whatsappUnavailable:
        return 'WhatsApp Unavailable';
      case AutomationTaskState.networkError:
        return 'Network Error';
      case AutomationTaskState.sendFailed:
        return 'Send Failed';
      case AutomationTaskState.verificationFailed:
        return 'Verification Failed';
      case AutomationTaskState.failed:
        return 'Failed';
      case AutomationTaskState.cancelled:
        return 'Cancelled';
    }
  }
}

class ScheduledAutomationTask {
  final String taskId;
  final String executionId;
  final String recipient;
  final String message;
  final DateTime scheduledDateTime;
  final String timezone;
  AutomationTaskState status;
  int retryCount;
  final DateTime createdAt;
  bool isEnabled;
  String? lastError;

  ScheduledAutomationTask({
    required this.taskId,
    required this.executionId,
    required this.recipient,
    required this.message,
    required this.scheduledDateTime,
    required this.timezone,
    this.status = AutomationTaskState.scheduled,
    this.retryCount = 0,
    required this.createdAt,
    this.isEnabled = true,
    this.lastError,
  });

  Map<String, dynamic> toJson() => {
        'taskId': taskId,
        'executionId': executionId,
        'recipient': recipient,
        'message': message,
        'scheduledDateTime': scheduledDateTime.toIso8601String(),
        'timezone': timezone,
        'status': status.name,
        'retryCount': retryCount,
        'createdAt': createdAt.toIso8601String(),
        'isEnabled': isEnabled,
        'lastError': lastError,
      };

  factory ScheduledAutomationTask.fromJson(Map<String, dynamic> json) =>
      ScheduledAutomationTask(
        taskId: json['taskId'] ?? '',
        executionId: json['executionId'] ?? '',
        recipient: json['recipient'] ?? '',
        message: json['message'] ?? '',
        scheduledDateTime:
            DateTime.tryParse(json['scheduledDateTime'] ?? '') ?? DateTime.now(),
        timezone: json['timezone'] ?? 'UTC',
        status: AutomationTaskState.values.firstWhere(
          (e) => e.name == json['status'],
          orElse: () => AutomationTaskState.scheduled,
        ),
        retryCount: json['retryCount'] ?? 0,
        createdAt: DateTime.tryParse(json['createdAt'] ?? '') ?? DateTime.now(),
        isEnabled: json['isEnabled'] ?? true,
        lastError: json['lastError'],
      );
}

class AutomationSecuritySettings {
  bool systemAuthEnabled;
  bool screenOffAutomationEnabled;
  bool backgroundSchedulerEnabled;
  bool lockedStateTasksEnabled;
  bool secureTaskStorageEnabled;

  AutomationSecuritySettings({
    this.systemAuthEnabled = true,
    this.screenOffAutomationEnabled = true,
    this.backgroundSchedulerEnabled = true,
    this.lockedStateTasksEnabled = true,
    this.secureTaskStorageEnabled = true,
  });

  Map<String, dynamic> toJson() => {
        'systemAuthEnabled': systemAuthEnabled,
        'screenOffAutomationEnabled': screenOffAutomationEnabled,
        'backgroundSchedulerEnabled': backgroundSchedulerEnabled,
        'lockedStateTasksEnabled': lockedStateTasksEnabled,
        'secureTaskStorageEnabled': secureTaskStorageEnabled,
      };

  factory AutomationSecuritySettings.fromJson(Map<String, dynamic> json) =>
      AutomationSecuritySettings(
        systemAuthEnabled: json['systemAuthEnabled'] ?? true,
        screenOffAutomationEnabled: json['screenOffAutomationEnabled'] ?? true,
        backgroundSchedulerEnabled: json['backgroundSchedulerEnabled'] ?? true,
        lockedStateTasksEnabled: json['lockedStateTasksEnabled'] ?? true,
        secureTaskStorageEnabled: json['secureTaskStorageEnabled'] ?? true,
      );
}
