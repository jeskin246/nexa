enum ScheduledJobStatus {
  scheduled,
  preparing,
  waitingForUnlock,
  running,
  sent,
  failed,
  cancelled,
}

enum ScheduledRepeatRule {
  none,
  daily,
  weekly,
  custom,
}

class ScheduledWhatsAppJob {
  final String id;
  final String contact;
  final String message;
  final String date;
  final String time;
  final int scheduledTimestamp;
  final ScheduledRepeatRule repeatRule;
  bool enabled;
  ScheduledJobStatus status;
  String statusReason;
  final DateTime createdAt;

  ScheduledWhatsAppJob({
    required this.id,
    required this.contact,
    required this.message,
    required this.date,
    required this.time,
    required this.scheduledTimestamp,
    this.repeatRule = ScheduledRepeatRule.none,
    this.enabled = true,
    this.status = ScheduledJobStatus.scheduled,
    this.statusReason = 'Scheduled task created',
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  String get repeatRuleLabel {
    switch (repeatRule) {
      case ScheduledRepeatRule.none:
        return 'None';
      case ScheduledRepeatRule.daily:
        return 'Daily';
      case ScheduledRepeatRule.weekly:
        return 'Weekly';
      case ScheduledRepeatRule.custom:
        return 'Custom';
    }
  }

  String get statusLabel {
    switch (status) {
      case ScheduledJobStatus.scheduled:
        return 'SCHEDULED';
      case ScheduledJobStatus.preparing:
        return 'PREPARING';
      case ScheduledJobStatus.waitingForUnlock:
        return 'WAITING_FOR_UNLOCK';
      case ScheduledJobStatus.running:
        return 'RUNNING';
      case ScheduledJobStatus.sent:
        return 'SENT';
      case ScheduledJobStatus.failed:
        return 'FAILED';
      case ScheduledJobStatus.cancelled:
        return 'CANCELLED';
    }
  }

  ScheduledWhatsAppJob copyWith({
    String? id,
    String? contact,
    String? message,
    String? date,
    String? time,
    int? scheduledTimestamp,
    ScheduledRepeatRule? repeatRule,
    bool? enabled,
    ScheduledJobStatus? status,
    String? statusReason,
  }) {
    return ScheduledWhatsAppJob(
      id: id ?? this.id,
      contact: contact ?? this.contact,
      message: message ?? this.message,
      date: date ?? this.date,
      time: time ?? this.time,
      scheduledTimestamp: scheduledTimestamp ?? this.scheduledTimestamp,
      repeatRule: repeatRule ?? this.repeatRule,
      enabled: enabled ?? this.enabled,
      status: status ?? this.status,
      statusReason: statusReason ?? this.statusReason,
      createdAt: createdAt,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'contact': contact,
      'message': message,
      'date': date,
      'time': time,
      'scheduled_timestamp': scheduledTimestamp,
      'repeat_rule': repeatRuleLabel.toUpperCase(),
      'enabled': enabled,
      'status': statusLabel,
      'status_reason': statusReason,
      'created_at': createdAt.toIso8601String(),
    };
  }

  factory ScheduledWhatsAppJob.fromJson(Map<String, dynamic> json) {
    ScheduledJobStatus parsedStatus;
    switch ((json['status'] ?? 'SCHEDULED').toString().toUpperCase()) {
      case 'PREPARING':
        parsedStatus = ScheduledJobStatus.preparing;
        break;
      case 'WAITING_FOR_UNLOCK':
        parsedStatus = ScheduledJobStatus.waitingForUnlock;
        break;
      case 'RUNNING':
        parsedStatus = ScheduledJobStatus.running;
        break;
      case 'SENT':
        parsedStatus = ScheduledJobStatus.sent;
        break;
      case 'FAILED':
        parsedStatus = ScheduledJobStatus.failed;
        break;
      case 'CANCELLED':
        parsedStatus = ScheduledJobStatus.cancelled;
        break;
      case 'SCHEDULED':
      default:
        parsedStatus = ScheduledJobStatus.scheduled;
        break;
    }

    ScheduledRepeatRule parsedRepeat;
    switch ((json['repeat_rule'] ?? 'NONE').toString().toUpperCase()) {
      case 'DAILY':
        parsedRepeat = ScheduledRepeatRule.daily;
        break;
      case 'WEEKLY':
        parsedRepeat = ScheduledRepeatRule.weekly;
        break;
      case 'CUSTOM':
        parsedRepeat = ScheduledRepeatRule.custom;
        break;
      case 'NONE':
      default:
        parsedRepeat = ScheduledRepeatRule.none;
        break;
    }

    return ScheduledWhatsAppJob(
      id: json['id'] ?? 'job_wa_${DateTime.now().millisecondsSinceEpoch}',
      contact: json['contact'] ?? 'Unknown',
      message: json['message'] ?? '',
      date: json['date'] ?? '28 Aug 2026',
      time: json['time'] ?? '6:00 PM',
      scheduledTimestamp: json['scheduled_timestamp'] ?? DateTime.now().millisecondsSinceEpoch + 60000,
      repeatRule: parsedRepeat,
      enabled: json['enabled'] ?? true,
      status: parsedStatus,
      statusReason: json['status_reason'] ?? '',
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : DateTime.now(),
    );
  }
}
