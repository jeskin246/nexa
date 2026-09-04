import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../manager/system_automation_manager.dart';
import '../services/scheduled_whatsapp_service.dart';

class SystemAutomationView extends StatefulWidget {
  const SystemAutomationView({super.key});

  @override
  State<SystemAutomationView> createState() => _SystemAutomationViewState();
}

class _SystemAutomationViewState extends State<SystemAutomationView> {
  final TextEditingController _recipientController =
      TextEditingController(text: 'John');
  final TextEditingController _messageController =
      TextEditingController(text: 'Hello, I will contact you tomorrow.');
  final TextEditingController _naturalCommandController =
      TextEditingController();

  String _selectedRecurrence = 'Once';
  String _selectedTone = 'Friendly';

  DateTime _selectedDate = DateTime.now().add(const Duration(hours: 1));
  TimeOfDay _selectedTime = TimeOfDay.now();

  @override
  void initState() {
    super.initState();
    final now = DateTime.now().add(const Duration(minutes: 30));
    _selectedDate = DateTime(now.year, now.month, now.day);
    _selectedTime = TimeOfDay(hour: now.hour, minute: now.minute);
  }

  String _formatDateTime(DateTime dt) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    final month = months[dt.month - 1];
    final day = dt.day.toString().padLeft(2, '0');
    final year = dt.year;

    final hour = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
    final min = dt.minute.toString().padLeft(2, '0');
    final ampm = dt.hour >= 12 ? 'PM' : 'AM';

    return '$day $month $year  $hour:$min $ampm';
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      builder: (context, child) {
        return Theme(
          data: ThemeData.dark().copyWith(
            colorScheme: const ColorScheme.dark(
              primary: Color(0xFF00F2FE),
              surface: Color(0xFF141824),
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) setState(() => _selectedDate = picked);
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _selectedTime,
      builder: (context, child) {
        return Theme(
          data: ThemeData.dark().copyWith(
            colorScheme: const ColorScheme.dark(
              primary: Color(0xFF00F2FE),
              surface: Color(0xFF141824),
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) setState(() => _selectedTime = picked);
  }

  @override
  Widget build(BuildContext context) {
    final manager = Provider.of<SystemAutomationManager>(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 1. Process Status Telemetry Card
          _buildHeaderTelemetryCard(manager),
          const SizedBox(height: 18),

          // 2. Process Requirement Step 1: System Permissions Checklist
          _buildPermissionsChecklistCard(context),
          const SizedBox(height: 18),

          // 3. Process Requirement Step 2: Screen Lock Preparation (Swipe / None Mode)
          _buildSwipeModeGuidanceCard(context),
          const SizedBox(height: 18),

          // 4. Process Requirement Step 3: Scheduled Message Form
          _buildSchedulerFormCard(context, manager),
          const SizedBox(height: 18),

          // 5. Process Requirement Step 4: Scheduled Tasks & Execution Log
          _buildScheduledTasksSection(context, manager),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildHeaderTelemetryCard(SystemAutomationManager manager) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF00F2FE).withValues(alpha: 0.4), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Expanded(
                child: Text(
                  'NEXA Automation Engine',
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1.2, fontSize: 15),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              SizedBox(width: 8),
              Icon(Icons.verified_user_rounded, color: Color(0xFF00F2FE), size: 20),
            ],
          ),
          const Divider(color: Color(0xFF2E3650), height: 22),
          _buildStatusRow('Scheduler Engine', '● Running', const Color(0xFF00C853)),
          const SizedBox(height: 8),
          _buildStatusRow('Screen-Off Mode', '● Enabled', const Color(0xFF00F2FE)),
          const SizedBox(height: 8),
          _buildStatusRow('Execution Mode', '● Swipe / None Mode', const Color(0xFF00C853)),
          const SizedBox(height: 14),
          Row(
            children: [
              _buildStateChip('SCREEN', manager.isScreenOn ? 'ON' : 'OFF', manager.isScreenOn ? const Color(0xFF00C853) : Colors.white38),
              const SizedBox(width: 8),
              _buildStateChip('LOCK', manager.isDeviceLocked ? 'LOCKED' : 'UNLOCKED', manager.isDeviceLocked ? Colors.amber : const Color(0xFF00C853)),
              const SizedBox(width: 8),
              _buildStateChip('AUTH', 'READY', const Color(0xFF00F2FE)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPermissionsChecklistCard(BuildContext context) {
    final service = context.watch<ScheduledWhatsAppService>();

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF00F2FE).withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.checklist_rounded, color: Color(0xFF00F2FE), size: 22),
              SizedBox(width: 10),
              Expanded(
                child: Text('Step 1: System Permissions Checklist', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text('For automatic background execution and gesture swiping, grant these required permissions:', style: TextStyle(color: Colors.white60, fontSize: 11, height: 1.3)),
          const SizedBox(height: 14),
          _buildPermissionItem(title: '1. NEXA Accessibility Service', subtitle: 'Required to swipe screen and click WhatsApp Send', icon: Icons.accessibility_new_rounded, onPressed: () => service.openAccessibilitySettings()),
          const SizedBox(height: 10),
          _buildPermissionItem(title: '2. Display Over Other Apps', subtitle: 'Allows NEXA to wake screen over keyguard', icon: Icons.layers_rounded, onPressed: () => service.openDisplayOverOtherAppsSettings()),
          const SizedBox(height: 10),
          _buildPermissionItem(title: '3. MIUI Background Pop-Up', subtitle: 'Required on Xiaomi/MIUI to launch popup in background', icon: Icons.window_rounded, onPressed: () => service.openMiuiPermissionEditor()),
          const SizedBox(height: 10),
          _buildPermissionItem(title: '4. Autostart & Battery Opt.', subtitle: 'Prevents phone from killing scheduled background alarms', icon: Icons.battery_saver_rounded, onPressed: () => service.openAppDetailsSettings()),
        ],
      ),
    );
  }

  Widget _buildPermissionItem({required String title, required String subtitle, required IconData icon, required VoidCallback onPressed}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(color: const Color(0xFF1E2638), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFF2E3650))),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF00F2FE), size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 2),
                Text(subtitle, style: const TextStyle(color: Colors.white54, fontSize: 10), maxLines: 2, overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          const SizedBox(width: 8),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00F2FE).withValues(alpha: 0.15),
              foregroundColor: const Color(0xFF00F2FE),
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8), side: const BorderSide(color: Color(0xFF00F2FE))),
            ),
            onPressed: onPressed,
            child: const Text('ENABLE', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 10)),
          ),
        ],
      ),
    );
  }

  Widget _buildSwipeModeGuidanceCard(BuildContext context) {
    final service = context.watch<ScheduledWhatsAppService>();
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: const Color(0xFF141824), borderRadius: BorderRadius.circular(18), border: Border.all(color: const Color(0xFF00F2FE).withValues(alpha: 0.5))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.shield_outlined, color: Color(0xFF00F2FE), size: 22),
              SizedBox(width: 10),
              Expanded(child: Text('Step 2: Screen Lock Preparation (Swipe Mode)', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14))),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.amber.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.amber.withValues(alpha: 0.4))),
            child: const Text('For automatic sending, ensure screen lock is set to Swipe or None.', style: TextStyle(color: Colors.amber, fontSize: 12)),
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            height: 42,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00F2FE), foregroundColor: Colors.black, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
              onPressed: () => service.openLockScreenSettings(),
              icon: const Icon(Icons.settings_suggest_rounded, size: 18),
              label: const Text('Open Lock Settings', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSchedulerFormCard(BuildContext context, SystemAutomationManager manager) {
    final scheduledDT = DateTime(_selectedDate.year, _selectedDate.month, _selectedDate.day, _selectedTime.hour, _selectedTime.minute);
    final waService = context.watch<ScheduledWhatsAppService>();

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: const Color(0xFF141824), borderRadius: BorderRadius.circular(18), border: Border.all(color: const Color(0xFF2E3650))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Expanded(
                child: Text(
                  'Step 3: Schedule WhatsApp Task',
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              SizedBox(width: 8),
              Icon(Icons.auto_awesome_rounded, color: Color(0xFF00F2FE), size: 20),
            ],
          ),
          const SizedBox(height: 14),

          // ─── Voice / Natural Language Scheduling Bar ──────────────────────────────
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF1E2638),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFF00F2FE).withValues(alpha: 0.3)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    InkWell(
                      onTap: () => _showVoiceInputModal(context, waService),
                      child: Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(color: const Color(0xFF00F2FE).withValues(alpha: 0.2), shape: BoxShape.circle),
                        child: const Icon(Icons.mic_rounded, color: Color(0xFF00F2FE), size: 16),
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        'Voice / Natural Command Scheduling',
                        style: TextStyle(color: Color(0xFF00F2FE), fontWeight: FontWeight.bold, fontSize: 12),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _naturalCommandController,
                        style: const TextStyle(color: Colors.white, fontSize: 12),
                        decoration: const InputDecoration(
                          hintText: 'e.g. Schedule to Sarah tomorrow...',
                          hintStyle: TextStyle(color: Colors.white38, fontSize: 11),
                          isDense: true,
                          border: InputBorder.none,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00F2FE).withValues(alpha: 0.2),
                        foregroundColor: const Color(0xFF00F2FE),
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: () async {
                        final cmd = _naturalCommandController.text.trim();
                        if (cmd.isEmpty) return;
                        final parsed = await waService.parseNaturalLanguageCommand(cmd);
                        setState(() {
                          _recipientController.text = parsed['contact'] ?? 'Contact';
                          _messageController.text = parsed['message'] ?? cmd;
                        });
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Parsed command into schedule form! ✓'), backgroundColor: Color(0xFF00C853)),
                          );
                        }
                      },
                      child: const Text('PARSE', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 10)),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // ─── Recipient & Message Fields ──────────────────────────────────────────
          TextField(controller: _recipientController, style: const TextStyle(color: Colors.white), decoration: InputDecoration(labelText: 'Recipient Name or Group (e.g. John, Sarah)', labelStyle: const TextStyle(color: Colors.white60), prefixIcon: const Icon(Icons.person_outline, color: Color(0xFF00F2FE)), filled: true, fillColor: const Color(0xFF1E2638), border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none))),
          const SizedBox(height: 12),
          
          TextField(
            controller: _messageController,
            maxLines: 2,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              labelText: 'Message',
              labelStyle: const TextStyle(color: Colors.white60),
              prefixIcon: const Icon(Icons.chat_bubble_outline_rounded, color: Color(0xFF00F2FE)),
              filled: true,
              fillColor: const Color(0xFF1E2638),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
            ),
          ),
          const SizedBox(height: 10),

          // ─── AI Personalization Bar ──────────────────────────────────────────────
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Text('AI Tone:', style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(width: 8),
                  InkWell(
                    onTap: () async {
                      final prompt = _messageController.text.trim();
                      final contact = _recipientController.text.trim();
                      if (prompt.isEmpty) return;
                      final gen = await waService.generatePersonalizedMessage(
                          contact: contact.isEmpty ? 'Friend' : contact,
                          prompt: prompt,
                          tone: _selectedTone);
                      setState(() => _messageController.text = gen);
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00F2FE),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.auto_fix_high_rounded, color: Colors.black, size: 14),
                          SizedBox(width: 4),
                          Text('AI Enhance', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 11)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: ['Friendly', 'Professional', 'Casual', 'Urgent'].map((tone) {
                  final isSel = _selectedTone == tone;
                  return InkWell(
                    onTap: () => setState(() => _selectedTone = tone),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: isSel ? const Color(0xFF00F2FE).withValues(alpha: 0.25) : const Color(0xFF1E2638),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: isSel ? const Color(0xFF00F2FE) : Colors.white12),
                      ),
                      child: Text(tone, style: TextStyle(color: isSel ? const Color(0xFF00F2FE) : Colors.white60, fontSize: 11, fontWeight: FontWeight.bold)),
                    ),
                  );
                }).toList(),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // ─── Recurrence Rules Selector ──────────────────────────────────────────
          const Text('Recurrence Schedule:', style: TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: ['Once', 'Daily', 'Weekly', 'Monthly'].map((rule) {
              final isSel = _selectedRecurrence == rule;
              return InkWell(
                onTap: () => setState(() => _selectedRecurrence = rule),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    color: isSel ? const Color(0xFF00C853).withValues(alpha: 0.25) : const Color(0xFF1E2638),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: isSel ? const Color(0xFF00C853) : Colors.white12),
                  ),
                  child: Text(rule, style: TextStyle(color: isSel ? const Color(0xFF00C853) : Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 14),

          // ─── Date & Time Pickers ────────────────────────────────────────────────
          Row(
            children: [
              Expanded(
                child: InkWell(
                  onTap: _pickDate,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                    decoration: BoxDecoration(color: const Color(0xFF1E2638), borderRadius: BorderRadius.circular(10)),
                    alignment: Alignment.center,
                    child: FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(
                        '${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: InkWell(
                  onTap: _pickTime,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                    decoration: BoxDecoration(color: const Color(0xFF1E2638), borderRadius: BorderRadius.circular(10)),
                    alignment: Alignment.center,
                    child: FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(
                        _selectedTime.format(context),
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          SizedBox(
            width: double.infinity,
            height: 44,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00F2FE),
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onPressed: () async {
                final recipient = _recipientController.text.trim();
                final message = _messageController.text.trim();

                if (recipient.isEmpty || message.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Please enter recipient and message.'),
                      backgroundColor: Colors.redAccent,
                    ),
                  );
                  return;
                }

                final dateStr = '${scheduledDT.year}-${scheduledDT.month.toString().padLeft(2, '0')}-${scheduledDT.day.toString().padLeft(2, '0')}';
                final timeStr = '${scheduledDT.hour.toString().padLeft(2, '0')}:${scheduledDT.minute.toString().padLeft(2, '0')}';

                await waService.createScheduledJob(
                  contact: recipient,
                  message: message,
                  date: dateStr,
                  time: timeStr,
                  scheduledTimestamp: scheduledDT.millisecondsSinceEpoch,
                );

                await manager.createTask(
                  recipient: recipient,
                  message: message,
                  scheduledDateTime: scheduledDT,
                );

                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                          'WhatsApp task scheduled for $recipient ($_selectedRecurrence)'),
                      backgroundColor: const Color(0xFF00C853),
                    ),
                  );
                }
              },
              icon: const Icon(Icons.send_rounded, size: 18),
              label: const Text(
                'Schedule WhatsApp Task',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScheduledTasksSection(
      BuildContext context, SystemAutomationManager manager) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF141824),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF2E3650)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Step 4: Active Task Telemetry',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF00F2FE).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  '${manager.tasks.length} Tasks',
                  style: const TextStyle(color: Color(0xFF00F2FE), fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          if (manager.tasks.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: const Color(0xFF1E2638),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                'No scheduled WhatsApp tasks pending.',
                style: TextStyle(color: Colors.white54, fontSize: 12),
              ),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: manager.tasks.length,
              separatorBuilder: (context, index) => const SizedBox(height: 10),
              itemBuilder: (context, index) {
                final task = manager.tasks[index];
                final statusStr = task.status.name.toUpperCase();
                final isSent = statusStr == 'SENT';
                final isWaiting = statusStr.contains('WAITING');

                return Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E2638),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isSent
                          ? const Color(0xFF00C853)
                          : isWaiting
                              ? Colors.amber
                              : const Color(0xFF2E3650),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              task.recipient,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: isSent
                                  ? const Color(0xFF00C853).withValues(alpha: 0.2)
                                  : isWaiting
                                      ? Colors.amber.withValues(alpha: 0.2)
                                      : const Color(0xFF00F2FE).withValues(alpha: 0.2),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              statusStr,
                              style: TextStyle(
                                color: isSent
                                    ? const Color(0xFF00C853)
                                    : isWaiting
                                        ? Colors.amber
                                        : const Color(0xFF00F2FE),
                                fontWeight: FontWeight.bold,
                                fontSize: 10,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        task.message,
                        style: const TextStyle(color: Colors.white70, fontSize: 12),
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              _formatDateTime(task.scheduledDateTime),
                              style: const TextStyle(
                                  color: Colors.white38, fontSize: 10),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline_rounded,
                                color: Colors.redAccent, size: 18),
                            onPressed: () {
                              manager.cancelTask(task.taskId);
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
    );
  }

  Widget _buildStatusRow(String label, String status, Color color) {
    return Row(
      children: [
        Expanded(
          child: Text(
            label,
            style: const TextStyle(color: Colors.white70, fontSize: 13),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        const SizedBox(width: 8),
        Text(
          status,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 13,
          ),
        ),
      ],
    );
  }

  Widget _buildStateChip(String label, String val, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
        decoration: BoxDecoration(
          color: const Color(0xFF1E2638),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withValues(alpha: 0.4)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(label,
                style: const TextStyle(color: Colors.white38, fontSize: 9)),
            const SizedBox(height: 2),
            FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(
                val,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                  fontSize: 10,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showVoiceInputModal(BuildContext context, ScheduledWhatsAppService waService) {
    bool isRecording = false;
    String selectedEngine = 'inbuilt';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF141824),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isGoogle = selectedEngine == 'google';

            return SingleChildScrollView(
              padding: EdgeInsets.only(
                left: 24,
                right: 24,
                top: 24,
                bottom: 24 + MediaQuery.of(context).viewInsets.bottom,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)),
                  ),
                  const SizedBox(height: 16),

                  // Engine Selector Tabs
                  Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: Colors.white10,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: GestureDetector(
                            onTap: () {
                              if (!isRecording) {
                                setModalState(() => selectedEngine = 'inbuilt');
                              }
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 8),
                              decoration: BoxDecoration(
                                color: !isGoogle ? const Color(0xFF00F2FE).withValues(alpha: 0.2) : Colors.transparent,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: !isGoogle ? const Color(0xFF00F2FE) : Colors.transparent,
                                ),
                              ),
                              child: Text(
                                '🎙️ In-Built (Offline)',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: !isGoogle ? const Color(0xFF00F2FE) : Colors.white60,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                        Expanded(
                          child: GestureDetector(
                            onTap: () {
                              if (!isRecording) {
                                setModalState(() => selectedEngine = 'google');
                              }
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 8),
                              decoration: BoxDecoration(
                                color: isGoogle ? const Color(0xFF4285F4).withValues(alpha: 0.2) : Colors.transparent,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: isGoogle ? const Color(0xFF4285F4) : Colors.transparent,
                                ),
                              ),
                              child: Text(
                                '🌐 Google Voice',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: isGoogle ? const Color(0xFF4285F4) : Colors.white60,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: isRecording
                          ? Colors.redAccent.withValues(alpha: 0.2)
                          : (isGoogle ? const Color(0xFF4285F4).withValues(alpha: 0.15) : const Color(0xFF00F2FE).withValues(alpha: 0.15)),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: isRecording
                            ? Colors.redAccent
                            : (isGoogle ? const Color(0xFF4285F4) : const Color(0xFF00F2FE)),
                      ),
                    ),
                    child: Icon(
                      isRecording ? Icons.fiber_manual_record : (isGoogle ? Icons.mic : Icons.mic_rounded),
                      color: isRecording
                          ? Colors.redAccent
                          : (isGoogle ? const Color(0xFF4285F4) : const Color(0xFF00F2FE)),
                      size: 40,
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    isRecording
                        ? '🔴 Recording Audio...'
                        : (isGoogle ? 'Google Voice to Text' : 'NEXO In-Built Voice Engine'),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    isRecording
                        ? 'Speak your command, then tap Stop & Process.'
                        : (isGoogle
                            ? 'Tap to speak scheduling command using Google Voice.'
                            : 'Tap "Start Speaking" (100% In-Built, Zero Cloud).'),
                    style: const TextStyle(color: Colors.white54, fontSize: 12),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    height: 44,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: isRecording
                            ? Colors.redAccent
                            : (isGoogle ? const Color(0xFF4285F4) : const Color(0xFF00F2FE)),
                        foregroundColor: isRecording || isGoogle ? Colors.white : Colors.black,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: () async {
                        if (isGoogle) {
                          // Google Voice Option
                          final text = await waService.startGoogleSpeechRecognition();
                          if (context.mounted) Navigator.pop(ctx);
                          if (text.isNotEmpty) {
                            _naturalCommandController.text = text;
                            final parsed = await waService.parseNaturalLanguageCommand(text);
                            setState(() {
                              _recipientController.text = parsed['contact'] ?? 'Contact';
                              _messageController.text = parsed['message'] ?? text;
                            });
                            if (!context.mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Google Voice: "$text" ✓'), backgroundColor: const Color(0xFF4285F4)),
                            );
                          }
                        } else {
                          // In-Built Offline Voice Option
                          if (!isRecording) {
                            setModalState(() => isRecording = true);
                            await waService.startAudioRecording();
                          } else {
                            setModalState(() => isRecording = false);
                            final text = await waService.stopAudioRecordingAndTranscribe();
                            if (context.mounted) Navigator.pop(ctx);
                            if (text.isNotEmpty) {
                              _naturalCommandController.text = text;
                              final parsed = await waService.parseNaturalLanguageCommand(text);
                              setState(() {
                                _recipientController.text = parsed['contact'] ?? 'Contact';
                                _messageController.text = parsed['message'] ?? text;
                              });
                              if (!context.mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('In-Built Voice: "$text" ✓'), backgroundColor: const Color(0xFF00C853)),
                              );
                            }
                          }
                        }
                      },
                      icon: Icon(isRecording ? Icons.stop : Icons.mic, size: 18),
                      label: Text(
                        isRecording
                            ? 'Stop & Process'
                            : (isGoogle ? 'Speak with Google Voice' : 'Start Speaking'),
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
