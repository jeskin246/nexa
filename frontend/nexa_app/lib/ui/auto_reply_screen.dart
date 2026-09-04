import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../manager/auto_reply_manager.dart';
import '../model/auto_reply_models.dart';
import 'edit_message_screen.dart';
import 'permission_screen.dart';
import 'reply_history_screen.dart';
import 'system_automation_view.dart';

class AutoReplyScreen extends StatefulWidget {
  const AutoReplyScreen({super.key});

  @override
  State<AutoReplyScreen> createState() => _AutoReplyScreenState();
}

class _AutoReplyScreenState extends State<AutoReplyScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  int _selectedPowerSubTab = 0; // 0: Auto-Reply Core, 1: System Automation, 2: WhatsApp Scheduler

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  String _formatTime(DateTime dt) {
    final hour = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
    final min = dt.minute.toString().padLeft(2, '0');
    final ampm = dt.hour >= 12 ? 'PM' : 'AM';
    return '$hour:$min $ampm';
  }

  String _formatSeconds(int sec) {
    final m = (sec ~/ 60).toString().padLeft(2, '0');
    final s = (sec % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    final manager = Provider.of<AutoReplyManager>(context);

    return Scaffold(
      backgroundColor: const Color(0xFF0D0F18),
      appBar: AppBar(
        backgroundColor: const Color(0xFF141824),
        elevation: 0,
        title: Column(
          children: const [
            Text(
              'N E X O',
              style: TextStyle(
                color: Color(0xFF00F2FE),
                fontWeight: FontWeight.w900,
                letterSpacing: 6.0,
                fontSize: 20,
              ),
            ),
            Text(
              'NEXA POWER',
              style: TextStyle(
                color: Colors.white54,
                fontWeight: FontWeight.w500,
                letterSpacing: 2.0,
                fontSize: 10,
              ),
            ),
          ],
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_note, color: Color(0xFF00F2FE)),
            tooltip: 'Edit Message',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (context) => const EditMessageScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.history, color: Color(0xFF00F2FE)),
            tooltip: 'History',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (context) => const ReplyHistoryScreen()),
              );
            },
          ),
          IconButton(
            icon: Icon(
              Icons.shield_outlined,
              color: manager.isPermissionGranted
                  ? const Color(0xFF00C853)
                  : Colors.amber,
            ),
            tooltip: 'Permissions',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (context) => const PermissionScreen()),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Sub-Tab Segment Switcher
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: const Color(0xFF141824),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFF2E3650)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () {
                      setState(() {
                        _selectedPowerSubTab = 0;
                      });
                    },
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      decoration: BoxDecoration(
                        color: _selectedPowerSubTab == 0
                            ? const Color(0xFF00F2FE)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      alignment: Alignment.center,
                      child: const FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Text(
                          '⚡ AUTO-REPLY',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: InkWell(
                    onTap: () {
                      setState(() {
                        _selectedPowerSubTab = 1;
                      });
                    },
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
                      decoration: BoxDecoration(
                        color: _selectedPowerSubTab == 1
                            ? const Color(0xFF00F2FE)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      alignment: Alignment.center,
                      child: const FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Text(
                          '🛡️ AUTOMATION & SCHEDULER',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Main View Body
          Expanded(
            child: _selectedPowerSubTab == 1
                ? const SystemAutomationView()
                : SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 20, vertical: 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
            // Permission Warning Banner if missing
            if (!manager.isPermissionGranted)
              GestureDetector(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const PermissionScreen()),
                  );
                },
                child: Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.amber.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.amber),
                  ),
                  child: Row(
                    children: const [
                      Icon(Icons.warning_amber_rounded, color: Colors.amber),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          '⚠ Notification Access Required. Tap to enable.',
                          style: TextStyle(
                              color: Colors.amber,
                              fontWeight: FontWeight.bold,
                              fontSize: 13),
                        ),
                      ),
                      Icon(Icons.arrow_forward_ios,
                          color: Colors.amber, size: 14),
                    ],
                  ),
                ),
              ),

            // Section 11: NEXO STATUS ANIMATION CORE CARD
            _buildNexoCoreCard(manager),
            const SizedBox(height: 18),

            // User Status Selector (AVAILABLE, AWAY, DO NOT DISTURB)
            _buildUserStatusSelector(manager),
            const SizedBox(height: 18),

            // Reply Delay Card
            _buildReplyDelayCard(context, manager),
            const SizedBox(height: 18),

            // Section 9: LIVE REPLY PREVIEW (When Waiting)
            if (manager.nexoStatus == NexoStatus.waiting ||
                manager.waitingSecondsRemaining > 0)
              _buildLiveWaitingPreviewCard(manager),

            // Section 7: LAST AUTO-REPLY CARD
            if (manager.lastAutoReplyItem != null)
              _buildLastAutoReplyCard(context, manager.lastAutoReplyItem!),
            const SizedBox(height: 18),

            // Section 3: SUPPORTED APPS SWITCHES
            _buildSupportedAppsCard(manager),
            const SizedBox(height: 18),

            // Section 14: LIVE ACTIVITY LOG
            _buildLiveActivityCard(manager),
            const SizedBox(height: 24),

            // TEST SIMULATION BUTTON
            _buildTestSimulationButton(manager),
            const SizedBox(height: 14),

            // Section 17: STOP AUTO-REPLY BUTTON
            _buildStopAutoReplyButton(manager),
                      ],
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  // Section 11 Core Indicator Animation
  Widget _buildNexoCoreCard(AutoReplyManager manager) {
    Color glowColor;
    String statusText;
    Widget statusIcon;

    switch (manager.nexoStatus) {
      case NexoStatus.active:
        glowColor = const Color(0xFF00F2FE);
        statusText = 'SYSTEM ACTIVE';
        statusIcon = const Text('◉',
            style: TextStyle(
                color: Color(0xFF00F2FE),
                fontSize: 28,
                fontWeight: FontWeight.bold));
        break;
      case NexoStatus.waiting:
        glowColor = Colors.amber;
        statusText =
            'WAITING (${_formatSeconds(manager.waitingSecondsRemaining)})';
        statusIcon = const Text('◉',
            style: TextStyle(
                color: Colors.amber,
                fontSize: 28,
                fontWeight: FontWeight.bold));
        break;
      case NexoStatus.processing:
        glowColor = Colors.orangeAccent;
        statusText = 'PROCESSING';
        statusIcon = const SizedBox(
          width: 26,
          height: 26,
          child: CircularProgressIndicator(
              strokeWidth: 3, color: Colors.orangeAccent),
        );
        break;
      case NexoStatus.success:
        glowColor = const Color(0xFF00C853);
        statusText = 'SUCCESS';
        statusIcon = const Text('✓',
            style: TextStyle(
                color: Color(0xFF00C853),
                fontSize: 32,
                fontWeight: FontWeight.bold));
        break;
      case NexoStatus.error:
        glowColor = Colors.redAccent;
        statusText = 'ERROR';
        statusIcon = const Text('!',
            style: TextStyle(
                color: Colors.redAccent,
                fontSize: 32,
                fontWeight: FontWeight.bold));
        break;
      case NexoStatus.off:
        glowColor = Colors.white24;
        statusText = 'AUTO-REPLY OFF';
        statusIcon = const Text('○',
            style: TextStyle(
                color: Colors.white38,
                fontSize: 28,
                fontWeight: FontWeight.bold));
        break;
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: glowColor.withValues(alpha: 0.4), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: glowColor.withValues(alpha: 0.15),
            blurRadius: 16,
            spreadRadius: 2,
          )
        ],
      ),
      child: Column(
        children: [
          // Pulse Indicator Icon
          AnimatedBuilder(
            animation: _pulseAnimation,
            builder: (context, child) {
              return Transform.scale(
                scale: manager.nexoStatus == NexoStatus.waiting ||
                        manager.nexoStatus == NexoStatus.active
                    ? _pulseAnimation.value
                    : 1.0,
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: glowColor.withValues(alpha: 0.15),
                    boxShadow: [
                      BoxShadow(
                        color: glowColor.withValues(alpha: 0.3),
                        blurRadius: 12,
                        spreadRadius: 2,
                      )
                    ],
                  ),
                  child: statusIcon,
                ),
              );
            },
          ),
          const SizedBox(height: 12),
          Text(
            statusText,
            style: TextStyle(
              color: glowColor,
              fontWeight: FontWeight.bold,
              letterSpacing: 2.0,
              fontSize: 14,
            ),
          ),
          const Divider(color: Color(0xFF2E3650), height: 24),

          // Master Switch Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'AUTO-REPLY',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                  fontSize: 15,
                ),
              ),
              Switch(
                value: manager.settings.autoReplyEnabled,
                activeThumbColor: const Color(0xFF00F2FE),
                activeTrackColor: const Color(0xFF00F2FE).withValues(alpha: 0.3),
                inactiveThumbColor: Colors.white38,
                inactiveTrackColor: const Color(0xFF2E3650),
                onChanged: (val) => manager.setMasterSwitch(val),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Status & Screen Monitor indicators
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('SCREEN MONITOR',
                  style: TextStyle(color: Colors.white60, fontSize: 13)),
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: Color(0xFF00C853),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  const Text('ACTIVE',
                      style: TextStyle(
                          color: Color(0xFF00C853),
                          fontWeight: FontWeight.bold,
                          fontSize: 12)),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  // Section 4 User Status Selector Chips
  Widget _buildUserStatusSelector(AutoReplyManager manager) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2E3650)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'USER STATUS',
                style: TextStyle(
                  color: Colors.white70,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                  fontSize: 13,
                ),
              ),
              Text(
                manager.settings.userStatus == UserStatus.away
                    ? '● REPLIES ACTIVE'
                    : '○ PAUSED',
                style: TextStyle(
                  color: manager.settings.userStatus == UserStatus.away
                      ? const Color(0xFF00F2FE)
                      : Colors.white38,
                  fontWeight: FontWeight.bold,
                  fontSize: 11,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: UserStatus.values.map((status) {
              final isSelected = manager.settings.userStatus == status;
              return Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 3),
                  child: InkWell(
                    onTap: () => manager.setUserStatus(status),
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? (status == UserStatus.away
                                ? const Color(0xFF00F2FE)
                                : const Color(0xFF2E3650))
                            : const Color(0xFF1A2030),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: isSelected
                              ? const Color(0xFF00F2FE)
                              : const Color(0xFF2E3650),
                        ),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        status.displayName,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: isSelected
                              ? (status == UserStatus.away
                                  ? Colors.black
                                  : Colors.white)
                              : Colors.white54,
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  String _formatCountdownClock(int totalSec) {
    final h = (totalSec ~/ 3600).toString().padLeft(2, '0');
    final m = ((totalSec % 3600) ~/ 60).toString().padLeft(2, '0');
    final s = (totalSec % 60).toString().padLeft(2, '0');
    return '$h:$m:$s';
  }

  void _showCustomDelayDialog(BuildContext context, AutoReplyManager manager) {
    final s = manager.settings;
    final hoursController =
        TextEditingController(text: s.delayHours.toString());
    final minutesController =
        TextEditingController(text: s.delayMinutes.toString());
    final secondsController =
        TextEditingController(text: s.delaySecs.toString());
    String? errorMessage;

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: const Color(0xFF141824),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
                side: const BorderSide(color: Color(0xFF00F2FE), width: 1.5),
              ),
              title: Row(
                children: const [
                  Icon(Icons.timer, color: Color(0xFF00F2FE)),
                  SizedBox(width: 10),
                  Text(
                    'CUSTOM DELAY',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.5,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (errorMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.all(8),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.redAccent.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.redAccent),
                        ),
                        child: Text(
                          errorMessage!,
                          style: const TextStyle(
                            color: Colors.redAccent,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                    _buildTimeInputField('Hours:', hoursController),
                    const SizedBox(height: 10),
                    _buildTimeInputField('Minutes:', minutesController),
                    const SizedBox(height: 10),
                    _buildTimeInputField('Seconds:', secondsController),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('CANCEL',
                      style: TextStyle(color: Colors.white54)),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00F2FE),
                    foregroundColor: Colors.black,
                  ),
                  onPressed: () {
                    final h = int.tryParse(hoursController.text.trim()) ?? 0;
                    final m = int.tryParse(minutesController.text.trim()) ?? 0;
                    final sec =
                        int.tryParse(secondsController.text.trim()) ?? 0;

                    final total = (h * 3600) + (m * 60) + sec;

                    if (total <= 0) {
                      setDialogState(() {
                        errorMessage =
                            '⚠ Delay must be greater than 0 seconds';
                      });
                      return;
                    }

                    manager.updateReplyDelay(total);
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(
                            'Reply delay set to ${manager.settings.formattedDelayText}'),
                        backgroundColor: const Color(0xFF00C853),
                      ),
                    );
                  },
                  child: const Text('SAVE',
                      style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Widget _buildTimeInputField(
      String label, TextEditingController controller) {
    return Row(
      children: [
        SizedBox(
          width: 80,
          child: Text(
            label,
            style: const TextStyle(
              color: Colors.white70,
              fontWeight: FontWeight.bold,
              fontSize: 13,
            ),
          ),
        ),
        Expanded(
          child: TextField(
            controller: controller,
            keyboardType: TextInputType.number,
            style: const TextStyle(
                color: Colors.white, fontWeight: FontWeight.bold),
            decoration: InputDecoration(
              isDense: true,
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              filled: true,
              fillColor: const Color(0xFF1E2638),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFF2E3650)),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFF00F2FE)),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // Custom Reply Delay Card matching prompt specification
  Widget _buildReplyDelayCard(
      BuildContext context, AutoReplyManager manager) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2E3650)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text(
                'REPLY DELAY',
                style: TextStyle(
                  color: Colors.white70,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                  fontSize: 13,
                ),
              ),
              Icon(Icons.timer_outlined, color: Color(0xFF00F2FE), size: 18),
            ],
          ),
          const SizedBox(height: 14),

          // Clock Display 01 : 00
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFF1E2638),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                  color: const Color(0xFF00F2FE).withValues(alpha: 0.4)),
            ),
            child: Text(
              manager.settings.formattedDelayClock,
              style: const TextStyle(
                color: Color(0xFF00F2FE),
                fontWeight: FontWeight.bold,
                fontSize: 26,
                letterSpacing: 2.0,
                fontFamily: 'monospace',
              ),
            ),
          ),
          const SizedBox(height: 14),

          // [ - ] [ + ] Buttons
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    final curr = manager.settings.replyDelaySeconds;
                    final step = curr > 60 ? 30 : 10;
                    final next = curr - step;
                    if (next <= 0) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content:
                              Text('Delay must be greater than 0 seconds'),
                          backgroundColor: Colors.redAccent,
                          duration: Duration(seconds: 1),
                        ),
                      );
                      return;
                    }
                    manager.updateReplyDelay(next);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1E2638),
                    foregroundColor: const Color(0xFF00F2FE),
                    side: const BorderSide(color: Color(0xFF2E3650)),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: const Text('[ - ]',
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    final curr = manager.settings.replyDelaySeconds;
                    final step = curr >= 60 ? 30 : 10;
                    manager.updateReplyDelay(curr + step);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1E2638),
                    foregroundColor: const Color(0xFF00F2FE),
                    side: const BorderSide(color: Color(0xFF2E3650)),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: const Text('[ + ]',
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // [ CUSTOM DELAY ] Button
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _showCustomDelayDialog(context, manager),
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFF00F2FE),
                side: const BorderSide(color: Color(0xFF00F2FE), width: 1.2),
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              icon: const Icon(Icons.edit_calendar, size: 16),
              label: const Text(
                '[ CUSTOM DELAY ]',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                  fontSize: 13,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Divider(color: Color(0xFF2E3650)),

          // Current Delay Display Text (e.g. 01 minute 30 seconds)
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Current Delay',
                style: TextStyle(color: Colors.white54, fontSize: 11),
              ),
              const SizedBox(height: 2),
              Text(
                manager.settings.formattedDelayText,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // Live Waiting Preview & Real-Time Countdown Card with Cancel Button
  Widget _buildLiveWaitingPreviewCard(AutoReplyManager manager) {
    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1B10),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.amber, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.amber.withValues(alpha: 0.15),
            blurRadius: 14,
            spreadRadius: 1,
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: const [
                  Icon(Icons.hourglass_top_rounded,
                      color: Colors.amber, size: 20),
                  SizedBox(width: 8),
                  Text(
                    'NEXO IS WAITING',
                    style: TextStyle(
                      color: Colors.amber,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            '${manager.pendingAppName}\n${manager.pendingSender} sent a message',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w600,
              fontSize: 14,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Reply in:',
            style: TextStyle(
              color: Colors.white54,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            _formatCountdownClock(manager.waitingSecondsRemaining),
            style: const TextStyle(
              color: Colors.amber,
              fontWeight: FontWeight.bold,
              fontSize: 24,
              letterSpacing: 2.0,
              fontFamily: 'monospace',
            ),
          ),
          const Divider(color: Colors.white24, height: 20),
          const Text(
            'REPLY PREVIEW',
            style: TextStyle(
              color: Colors.white54,
              fontWeight: FontWeight.bold,
              fontSize: 11,
              letterSpacing: 1.0,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '"${manager.pendingPreviewText}"',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              height: 1.4,
              fontStyle: FontStyle.italic,
            ),
          ),
          const SizedBox(height: 16),

          // [ CANCEL ] Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () {
                manager.cancelPendingReply();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Auto-reply cancelled'),
                    backgroundColor: Colors.amber,
                  ),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.redAccent.withValues(alpha: 0.2),
                foregroundColor: Colors.redAccent,
                side: const BorderSide(color: Colors.redAccent, width: 1.5),
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              icon: const Icon(Icons.cancel_outlined, size: 18),
              label: const Text(
                '[ CANCEL ]',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // Section 7: Last Auto-Reply Card
  Widget _buildLastAutoReplyCard(BuildContext context, ReplyHistoryItem item) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2E3650)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'LAST AUTO-REPLY',
                style: TextStyle(
                  color: Colors.white70,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                  fontSize: 13,
                ),
              ),
              Text(
                _formatTime(item.timestamp),
                style: const TextStyle(color: Colors.white38, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Icon(
                item.appName == 'WhatsApp'
                    ? Icons.chat
                    : item.appName == 'Instagram'
                        ? Icons.camera_alt
                        : Icons.send,
                color: const Color(0xFF00F2FE),
                size: 18,
              ),
              const SizedBox(width: 8),
              Text(
                '${item.appName} → ${item.sender}',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          const Text(
            'NEXO replied:',
            style: TextStyle(color: Colors.white54, fontSize: 12),
          ),
          const SizedBox(height: 6),
          Text(
            '"${item.sentMessage}"',
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.check, color: Color(0xFF00C853), size: 16),
                  const SizedBox(width: 4),
                  Text(
                    item.status,
                    style: const TextStyle(
                      color: Color(0xFF00C853),
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
              TextButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const ReplyHistoryScreen()),
                  );
                },
                child: const Text(
                  '[ VIEW FULL MESSAGE ]',
                  style: TextStyle(
                    color: Color(0xFF00F2FE),
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // Section 3: Supported Apps Card
  Widget _buildSupportedAppsCard(AutoReplyManager manager) {
    final apps = ['WhatsApp', 'Instagram', 'Telegram'];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2E3650)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'SUPPORTED APPS',
            style: TextStyle(
              color: Colors.white70,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.2,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 12),
          Column(
            children: apps.map((app) {
              final isEnabled = manager.settings.enabledApps[app] ?? false;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Text(
                          isEnabled ? '●' : '○',
                          style: TextStyle(
                            color: isEnabled
                                ? const Color(0xFF00F2FE)
                                : Colors.white38,
                            fontSize: 14,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Text(
                          app,
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                    Switch(
                      value: isEnabled,
                      activeThumbColor: const Color(0xFF00F2FE),
                      activeTrackColor: const Color(0xFF00F2FE).withValues(alpha: 0.3),
                      inactiveThumbColor: Colors.white38,
                      inactiveTrackColor: const Color(0xFF2E3650),
                      onChanged: (val) => manager.toggleApp(app, val),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  // Section 14: Live Activity Card
  Widget _buildLiveActivityCard(AutoReplyManager manager) {
    final logs = manager.activityLogs.take(5).toList();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2E3650)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text(
                'LIVE ACTIVITY',
                style: TextStyle(
                  color: Colors.white70,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                  fontSize: 13,
                ),
              ),
              Icon(Icons.graphic_eq, color: Color(0xFF00F2FE), size: 18),
            ],
          ),
          const SizedBox(height: 12),
          logs.isEmpty
              ? const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    'No activity detected yet',
                    style: TextStyle(color: Colors.white38, fontSize: 13),
                  ),
                )
              : Column(
                  children: logs.map((log) {
                    Color badgeColor;
                    switch (log.status) {
                      case ActivityLogStatus.sent:
                        badgeColor = const Color(0xFF00C853);
                        break;
                      case ActivityLogStatus.waiting:
                      case ActivityLogStatus.detected:
                        badgeColor = const Color(0xFF00F2FE);
                        break;
                      case ActivityLogStatus.cooldown:
                      case ActivityLogStatus.skipped:
                        badgeColor = Colors.amber;
                        break;
                      case ActivityLogStatus.unsupported:
                      case ActivityLogStatus.failed:
                        badgeColor = Colors.redAccent;
                        break;
                    }

                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _formatTime(log.timestamp),
                            style: const TextStyle(
                              color: Colors.white38,
                              fontSize: 11,
                              fontFamily: 'monospace',
                            ),
                          ),
                          const SizedBox(width: 10),
                          Container(
                            width: 6,
                            height: 6,
                            margin: const EdgeInsets.only(top: 5),
                            decoration: BoxDecoration(
                              color: badgeColor,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              log.text,
                              style: const TextStyle(
                                color: Colors.white70,
                                fontSize: 12,
                                height: 1.3,
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
        ],
      ),
    );
  }

  // Section 17: Stop Auto-Reply Button
  Widget _buildStopAutoReplyButton(AutoReplyManager manager) {
    return ElevatedButton(
      onPressed: () {
        manager.stopAutoReply();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('AUTO-REPLY STOPPED'),
            backgroundColor: Colors.redAccent,
          ),
        );
      },
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.redAccent.withValues(alpha: 0.2),
        foregroundColor: Colors.redAccent,
        side: const BorderSide(color: Colors.redAccent, width: 1.5),
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        elevation: 0,
      ),
      child: const Text(
        'STOP AUTO-REPLY',
        style: TextStyle(
          fontWeight: FontWeight.bold,
          letterSpacing: 2.0,
          fontSize: 15,
        ),
      ),
    );
  }

  Widget _buildTestSimulationButton(AutoReplyManager manager) {
    return OutlinedButton.icon(
      onPressed: () {
        if (!manager.settings.autoReplyEnabled) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Please turn AUTO-REPLY ON first!'),
              backgroundColor: Colors.amber,
            ),
          );
          return;
        }
        if (manager.settings.userStatus != UserStatus.away) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Please set User Status to AWAY to test auto-reply!'),
              backgroundColor: Colors.amber,
            ),
          );
          return;
        }
        manager.simulateIncomingMessage(appName: 'WhatsApp', sender: 'Test Contact');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Simulated WhatsApp message received! Auto-reply timer started.'),
            backgroundColor: Color(0xFF00C853),
          ),
        );
      },
      style: OutlinedButton.styleFrom(
        foregroundColor: const Color(0xFF00F2FE),
        side: const BorderSide(color: Color(0xFF00F2FE), width: 1.5),
        padding: const EdgeInsets.symmetric(vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
      icon: const Icon(Icons.play_circle_fill, size: 20),
      label: const Text(
        'TEST AUTO-REPLY SIMULATION',
        style: TextStyle(
          fontWeight: FontWeight.bold,
          letterSpacing: 1.5,
          fontSize: 13,
        ),
      ),
    );
  }
}
