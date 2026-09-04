import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../model/system_automation_models.dart';

class AutomationPreferences {
  static const String _keyTasks = 'nexa_automation_tasks';
  static const String _keySecurity = 'nexa_automation_security';

  static Future<List<ScheduledAutomationTask>> loadTasks() async {
    final prefs = await SharedPreferences.getInstance();
    final String? jsonString = prefs.getString(_keyTasks);
    if (jsonString == null || jsonString.isEmpty) return [];

    try {
      final List<dynamic> list = jsonDecode(jsonString);
      return list.map((item) => ScheduledAutomationTask.fromJson(item)).toList();
    } catch (e) {
      return [];
    }
  }

  static Future<void> saveTasks(List<ScheduledAutomationTask> tasks) async {
    final prefs = await SharedPreferences.getInstance();
    final String jsonString =
        jsonEncode(tasks.map((t) => t.toJson()).toList());
    await prefs.setString(_keyTasks, jsonString);
  }

  static Future<AutomationSecuritySettings> loadSecuritySettings() async {
    final prefs = await SharedPreferences.getInstance();
    final String? jsonString = prefs.getString(_keySecurity);
    if (jsonString == null || jsonString.isEmpty) {
      return AutomationSecuritySettings();
    }

    try {
      final Map<String, dynamic> map = jsonDecode(jsonString);
      return AutomationSecuritySettings.fromJson(map);
    } catch (e) {
      return AutomationSecuritySettings();
    }
  }

  static Future<void> saveSecuritySettings(
      AutomationSecuritySettings settings) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keySecurity, jsonEncode(settings.toJson()));
  }
}
