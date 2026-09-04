enum UserStatus {
  available,
  away,
  doNotDisturb,
}

extension UserStatusExtension on UserStatus {
  String get displayName {
    switch (this) {
      case UserStatus.available:
        return 'AVAILABLE';
      case UserStatus.away:
        return 'AWAY';
      case UserStatus.doNotDisturb:
        return 'DO NOT DISTURB';
    }
  }
}

enum NexoStatus {
  active,
  waiting,
  processing,
  success,
  error,
  off,
}

enum ActivityLogStatus {
  detected,
  waiting,
  sent,
  skipped,
  cooldown,
  unsupported,
  failed,
}

extension ActivityLogStatusExtension on ActivityLogStatus {
  String get displayName {
    switch (this) {
      case ActivityLogStatus.detected:
        return 'DETECTED';
      case ActivityLogStatus.waiting:
        return 'WAITING';
      case ActivityLogStatus.sent:
        return 'SENT';
      case ActivityLogStatus.skipped:
        return 'SKIPPED';
      case ActivityLogStatus.cooldown:
        return 'COOLDOWN';
      case ActivityLogStatus.unsupported:
        return 'UNSUPPORTED';
      case ActivityLogStatus.failed:
        return 'FAILED';
    }
  }
}

class ActivityLogEntry {
  final String id;
  final DateTime timestamp;
  final String text;
  final ActivityLogStatus status;
  final String appName;
  final String sender;

  ActivityLogEntry({
    required this.id,
    required this.timestamp,
    required this.text,
    required this.status,
    required this.appName,
    required this.sender,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'timestamp': timestamp.toIso8601String(),
        'text': text,
        'status': status.name,
        'appName': appName,
        'sender': sender,
      };

  factory ActivityLogEntry.fromJson(Map<String, dynamic> json) =>
      ActivityLogEntry(
        id: json['id'] ?? '',
        timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
        text: json['text'] ?? '',
        status: ActivityLogStatus.values.firstWhere(
          (e) => e.name == json['status'],
          orElse: () => ActivityLogStatus.detected,
        ),
        appName: json['appName'] ?? '',
        sender: json['sender'] ?? '',
      );
}

class ReplyHistoryItem {
  final String id;
  final String appName;
  final String sender;
  final String templateMessage;
  final String sentMessage;
  final String status;
  final DateTime timestamp;

  ReplyHistoryItem({
    required this.id,
    required this.appName,
    required this.sender,
    required this.templateMessage,
    required this.sentMessage,
    required this.status,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'appName': appName,
        'sender': sender,
        'templateMessage': templateMessage,
        'sentMessage': sentMessage,
        'status': status,
        'timestamp': timestamp.toIso8601String(),
      };

  factory ReplyHistoryItem.fromJson(Map<String, dynamic> json) =>
      ReplyHistoryItem(
        id: json['id'] ?? '',
        appName: json['appName'] ?? '',
        sender: json['sender'] ?? '',
        templateMessage: json['templateMessage'] ?? '',
        sentMessage: json['sentMessage'] ?? '',
        status: json['status'] ?? '✓ SENT',
        timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
      );
}

class AutoReplySettings {
  bool autoReplyEnabled;
  UserStatus userStatus;
  int replyDelaySeconds;
  int cooldownMinutes;
  String username;
  String replyTemplate;
  Map<String, bool> enabledApps;

  AutoReplySettings({
    this.autoReplyEnabled = true,
    this.userStatus = UserStatus.away,
    this.replyDelaySeconds = 60,
    this.cooldownMinutes = 10,
    this.username = "Jeskin",
    String? replyTemplate,
    Map<String, bool>? enabledApps,
  })  : replyTemplate = replyTemplate ??
            "Hello, I’m NEXO, (username)’s assistant. (username) is currently unavailable and may not be able to reply right now. They’ll respond when possible. Thank you for understanding.",
        enabledApps = enabledApps ??
            {
              "WhatsApp": true,
              "Instagram": true,
              "Telegram": false,
            };

  int get delayHours => replyDelaySeconds ~/ 3600;
  int get delayMinutes => (replyDelaySeconds % 3600) ~/ 60;
  int get delaySecs => replyDelaySeconds % 60;

  String get formattedDelayText {
    final h = delayHours;
    final m = delayMinutes;
    final s = delaySecs;

    final parts = <String>[];
    if (h > 0) parts.add('${h.toString().padLeft(2, '0')} ${h == 1 ? 'hour' : 'hours'}');
    if (m > 0) parts.add('${m.toString().padLeft(2, '0')} ${m == 1 ? 'minute' : 'minutes'}');
    if (s > 0 || parts.isEmpty) parts.add('${s.toString().padLeft(2, '0')} ${s == 1 ? 'second' : 'seconds'}');
    return parts.join(' ');
  }

  String get formattedDelayClock {
    final h = delayHours.toString().padLeft(2, '0');
    final m = delayMinutes.toString().padLeft(2, '0');
    final s = delaySecs.toString().padLeft(2, '0');
    if (delayHours > 0) {
      return '$h : $m : $s';
    }
    return '$m : $s';
  }

  Map<String, dynamic> toJson() => {
        'autoReplyEnabled': autoReplyEnabled,
        'userStatus': userStatus.name,
        'replyDelaySeconds': replyDelaySeconds,
        'cooldownMinutes': cooldownMinutes,
        'username': username,
        'replyTemplate': replyTemplate,
        'enabledApps': enabledApps,
      };

  factory AutoReplySettings.fromJson(Map<String, dynamic> json) =>
      AutoReplySettings(
        autoReplyEnabled: json['autoReplyEnabled'] ?? true,
        userStatus: UserStatus.values.firstWhere(
          (e) => e.name == json['userStatus'],
          orElse: () => UserStatus.away,
        ),
        replyDelaySeconds: json['replyDelaySeconds'] ?? 60,
        cooldownMinutes: json['cooldownMinutes'] ?? 10,
        username: json['username'] ?? 'Jeskin',
        replyTemplate: json['replyTemplate'],
        enabledApps: json['enabledApps'] != null
            ? Map<String, bool>.from(json['enabledApps'])
            : null,
      );
}
