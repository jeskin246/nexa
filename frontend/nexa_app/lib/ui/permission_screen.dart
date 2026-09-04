import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../manager/auto_reply_manager.dart';
import '../manager/system_automation_manager.dart';
import '../services/scheduled_whatsapp_service.dart';

class PermissionScreen extends StatelessWidget {
  const PermissionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final manager = Provider.of<AutoReplyManager>(context);
    final waService = Provider.of<ScheduledWhatsAppService>(context);
    final sysManager = Provider.of<SystemAutomationManager>(context, listen: false);

    return Scaffold(
      backgroundColor: const Color(0xFF0D0F18),
      appBar: AppBar(
        backgroundColor: const Color(0xFF141824),
        title: const Text(
          'DIRECT SYSTEM SETTINGS',
          style: TextStyle(
            color: Color(0xFF00F2FE),
            fontWeight: FontWeight.bold,
            letterSpacing: 1.2,
            fontSize: 16,
          ),
        ),
        iconTheme: const IconThemeData(color: Color(0xFF00F2FE)),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 1. Accessibility Service Permission Card
            _buildPermissionCard(
              title: '1. Accessibility Gesture Service',
              subtitle: 'Auto-unlocks lockscreen & clicks WhatsApp Send button',
              statusLabel: 'ACCESSIBILITY',
              isAllowed: true,
              buttonLabel: 'ALLOW IN SETTINGS',
              buttonIcon: Icons.accessibility_new_rounded,
              onTap: () => waService.openAccessibilitySettings(),
            ),
            const SizedBox(height: 14),

            // 2. NEXA App Info Settings (For 3-Dots Restricted Settings)
            _buildPermissionCard(
              title: '2. Allow Restricted Settings (NEXA App Info)',
              subtitle: 'Opens NEXA App Info directly for 3-dots menu',
              statusLabel: 'APP INFO',
              isAllowed: true,
              buttonLabel: 'OPEN APP SETTINGS',
              buttonIcon: Icons.settings_applications_rounded,
              onTap: () => waService.openAppDetailsSettings(),
            ),
            const SizedBox(height: 14),

            // 3. Notification Access Permission Card
            _buildPermissionCard(
              title: '3. Notification Listener Access',
              subtitle: 'Monitors incoming messages for auto-reply engine',
              statusLabel: manager.isPermissionGranted ? 'ALLOWED ✓' : 'NOT ALLOWED ⚠',
              isAllowed: manager.isPermissionGranted,
              buttonLabel: manager.isPermissionGranted ? 'ALLOWED' : 'ALLOW IN SETTINGS',
              buttonIcon: Icons.notifications_active_rounded,
              onTap: () => manager.requestPermission(),
            ),
            const SizedBox(height: 14),

            // 4. Battery Optimization Exemption Card
            _buildPermissionCard(
              title: '4. Unrestricted Battery Usage',
              subtitle: 'Permits background execution during screen-off',
              statusLabel: 'BATTERY',
              isAllowed: true,
              buttonLabel: 'OPEN BATTERY SETTINGS',
              buttonIcon: Icons.battery_charging_full_rounded,
              onTap: () => sysManager.openBatteryOptimizationSettings(),
            ),
            const SizedBox(height: 14),

            // 5. MIUI / Vendor Autostart Permission Card
            _buildPermissionCard(
              title: '5. MIUI / Vendor Autostart',
              subtitle: 'Allows NEXA background service auto-start',
              statusLabel: 'AUTOSTART',
              isAllowed: true,
              buttonLabel: 'OPEN AUTOSTART SETTINGS',
              buttonIcon: Icons.power_settings_new_rounded,
              onTap: () => sysManager.openAutostartSettings(),
            ),
            const SizedBox(height: 14),

            // 6. Exact Alarm Permission Card
            _buildPermissionCard(
              title: '6. Schedule Exact Alarms',
              subtitle: 'Precision alarm triggers for screen-off execution',
              statusLabel: 'EXACT ALARMS',
              isAllowed: true,
              buttonLabel: 'OPEN ALARM SETTINGS',
              buttonIcon: Icons.alarm_on_rounded,
              onTap: () => sysManager.openExactAlarmSettings(),
            ),
            const SizedBox(height: 14),

            // 7. MIUI / Redmi Pop-Up Windows in Background Permission Card
            _buildPermissionCard(
              title: '7. Display Pop-Up Windows in Background (MIUI / Redmi)',
              subtitle: 'Required on Xiaomi / Redmi to allow lockscreen gesture execution',
              statusLabel: 'MIUI POPUP',
              isAllowed: true,
              buttonLabel: 'OPEN MIUI PERMISSIONS',
              buttonIcon: Icons.layers_rounded,
              onTap: () => waService.openMiuiPermissionEditor(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPermissionCard({
    required String title,
    required String subtitle,
    required String statusLabel,
    required bool isAllowed,
    required String buttonLabel,
    required IconData buttonIcon,
    required VoidCallback onTap,
  }) {
    final accentColor = isAllowed ? const Color(0xFF00C853) : Colors.amber;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF00F2FE).withValues(alpha: 0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isAllowed ? Icons.check_circle_rounded : Icons.info_outline_rounded,
                color: accentColor,
                size: 22,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: accentColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: accentColor),
                ),
                child: Text(
                  statusLabel,
                  style: TextStyle(
                    color: accentColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 10,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            subtitle,
            style: const TextStyle(
              color: Colors.white54,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: ElevatedButton.icon(
              onPressed: onTap,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00F2FE),
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              icon: Icon(buttonIcon, size: 16),
              label: Text(
                buttonLabel,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
