import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../model/auto_reply_models.dart';

class NexoPreferences {
  static const String _keySettings = 'nexo_settings';
  static const String _keyHistory = 'nexo_reply_history';
  static const String _keyLogs = 'nexo_activity_logs';
  static const String _keyLastReplyTimes = 'nexo_last_reply_times';

  static Future<AutoReplySettings> loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString(_keySettings);
    if (jsonString != null && jsonString.isNotEmpty) {
      try {
        final map = jsonDecode(jsonString);
        return AutoReplySettings.fromJson(map);
      } catch (e) {
        // Fallback to default
      }
    }
    return AutoReplySettings();
  }

  static Future<void> saveSettings(AutoReplySettings settings) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = jsonEncode(settings.toJson());
    await prefs.setString(_keySettings, jsonString);
  }

  static Future<List<ReplyHistoryItem>> loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_keyHistory);
    if (list != null) {
      return list
          .map((item) => ReplyHistoryItem.fromJson(jsonDecode(item)))
          .toList();
    }
    return [];
  }

  static Future<void> saveHistory(List<ReplyHistoryItem> history) async {
    final prefs = await SharedPreferences.getInstance();
    final list = history.map((item) => jsonEncode(item.toJson())).toList();
    await prefs.setStringList(_keyHistory, list);
  }

  static Future<List<ActivityLogEntry>> loadLogs() async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_keyLogs);
    if (list != null) {
      return list
          .map((item) => ActivityLogEntry.fromJson(jsonDecode(item)))
          .toList();
    }
    return [];
  }

  static Future<void> saveLogs(List<ActivityLogEntry> logs) async {
    final prefs = await SharedPreferences.getInstance();
    // Keep max 100 recent activity logs
    final recentLogs = logs.take(100).toList();
    final list = recentLogs.map((item) => jsonEncode(item.toJson())).toList();
    await prefs.setStringList(_keyLogs, list);
  }

  static Future<Map<String, DateTime>> loadLastReplyTimes() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString(_keyLastReplyTimes);
    if (jsonString != null && jsonString.isNotEmpty) {
      try {
        final Map<String, dynamic> map = jsonDecode(jsonString);
        return map.map(
          (key, value) => MapEntry(key, DateTime.parse(value as String)),
        );
      } catch (e) {
        // Fallback
      }
    }
    return {};
  }

  static Future<void> saveLastReplyTimes(
      Map<String, DateTime> lastReplyTimes) async {
    final prefs = await SharedPreferences.getInstance();
    final map = lastReplyTimes.map(
      (key, value) => MapEntry(key, value.toIso8601String()),
    );
    await prefs.setString(_keyLastReplyTimes, jsonEncode(map));
  }
}
