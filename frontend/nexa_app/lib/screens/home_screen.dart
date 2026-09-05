import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/agent_service.dart';
import '../services/system_monitor_service.dart';
import '../widgets/ai_core/ai_core_widget.dart';
import '../widgets/common/animated_gradient.dart';
import '../widgets/panels/activity_panel.dart';
import '../widgets/panels/command_input.dart';
import '../widgets/panels/confirmation_dialog.dart';
import '../widgets/panels/system_telemetry.dart';
import '../widgets/panels/task_card.dart';
import '../ui/auto_reply_screen.dart';
import 'settings_screen.dart';
import 'ai_keyboard_screen.dart';

import '../services/scheduled_whatsapp_service.dart';
import '../core/theme.dart';

/// NEXA Main Futuristic OS Control Center Screen.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isListeningVoice = false;
  final TextEditingController _chatInputController = TextEditingController();

  @override
  void dispose() {
    _chatInputController.dispose();
    super.dispose();
  }

  void _toggleVoice() {
    final waService = context.read<ScheduledWhatsAppService>();
    bool isRecording = false;
    String selectedEngine = 'inbuilt'; // 'inbuilt' or 'google'

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF141824),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final isGoogle = selectedEngine == 'google';

            return Container(
              padding: const EdgeInsets.all(24),
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
                        ? '🔴 Listening (In-Built Offline)...'
                        : (isGoogle ? 'Google Voice to Text' : 'NEXO In-Built Voice Engine'),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    isRecording
                        ? 'Speak now, then tap Stop to insert text.'
                        : (isGoogle
                            ? 'Tap to speak using Google Speech Services.'
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
                          // Google Voice Recognition Option
                          final text = await waService.startGoogleSpeechRecognition();
                          if (context.mounted) Navigator.pop(ctx);
                          if (text.isNotEmpty) {
                            setState(() {
                              _chatInputController.text = text;
                            });
                            if (!context.mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Google Voice: "$text" ✓'),
                                backgroundColor: const Color(0xFF4285F4),
                              ),
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
                              setState(() {
                                _chatInputController.text = text;
                              });
                              if (!context.mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('In-Built Voice: "$text" ✓'),
                                  backgroundColor: const Color(0xFF00C853),
                                ),
                              );
                            }
                          }
                        }
                      },
                      icon: Icon(isRecording ? Icons.stop : Icons.mic, size: 18),
                      label: Text(
                        isRecording
                            ? 'Stop & Transcribe'
                            : (isGoogle ? 'Speak with Google Voice' : 'Start Speaking'),
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
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

  void _openSettings() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const SettingsScreen()),
    );
  }

  void _handleGoalSubmission(String goal) async {
    if (_isListeningVoice) setState(() => _isListeningVoice = false);
    final text = goal.trim();
    if (text.isEmpty) return;

    final lower = text.toLowerCase();
    final waService = context.read<ScheduledWhatsAppService>();
    final agent = context.read<AgentService>();

    // ─── 1. Cross-App Pipelines & Sharing (e.g. "share vj siddhu vlogs video youtube to saritha in whatsapp") ───
    final isShare = (lower.contains('share') || lower.contains('forward')) &&
        (lower.contains('youtube') || lower.contains('video') || lower.contains('vlogs') || lower.contains('vlog') || lower.contains('link') || lower.contains('http://') || lower.contains('https://')) &&
        (lower.contains('whatsapp') || lower.contains('to '));

    if (isShare) {
      // Extract direct URL if present
      final directUrlMatch = RegExp(r'(https?://[^\s]+)').firstMatch(text);
      final directUrl = directUrlMatch?.group(0) ?? '';

      // Extract Recipient
      final recMatch = RegExp(r'\bto\s+([a-zA-Z0-9_+\s]+?)(?:\s+in\s+whatsapp|\s+on\s+whatsapp|\s+via\s+whatsapp|\s+whatsapp|\s+at\s+\d+|\s+in\s+\d+|\s*$)', caseSensitive: false).firstMatch(text);
      var recipient = recMatch?.group(1)?.trim() ?? 'Contact';
      if (['whatsapp', 'youtube', 'video', 'vlogs', 'vlog', 'link'].contains(recipient.toLowerCase())) {
        recipient = 'Contact';
      }

      // Extract Delay if Scheduled
      final timeMatch = RegExp(r'\b(?:in\s+(\d+)\s*(sec|seconds|second|min|mins|minutes|minute|hour|hours)|at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))\b', caseSensitive: false).firstMatch(text);

      // Extract Topic / Query
      var topicText = text;
      if (directUrl.isNotEmpty) topicText = topicText.replaceAll(directUrl, '');
      final stripWords = ['share', 'send', 'forward', 'link', 'url', 'video of', 'video', 'youtube', 'in whatsapp', 'on whatsapp', 'via whatsapp', 'whatsapp', 'high view', 'highest view', 'most viewed', 'recent', 'latest', 'top'];
      for (final w in stripWords) {
        topicText = topicText.replaceAll(RegExp('\\b$w\\b', caseSensitive: false), '');
      }
      if (recMatch != null && recipient.isNotEmpty) {
        topicText = topicText.replaceAll(RegExp('to\\s+${RegExp.escape(recipient)}', caseSensitive: false), '');
      }
      if (timeMatch != null) {
        topicText = topicText.replaceAll(timeMatch.group(0)!, '');
      }
      var cleanTopic = topicText.replaceAll(RegExp(r'^(?:of|about|link|url|for)\s+', caseSensitive: false), '').trim();
      if (cleanTopic.isEmpty) cleanTopic = directUrl.isNotEmpty ? directUrl : 'vj siddhu vlogs';

      final videoUrl = directUrl.isNotEmpty
          ? directUrl
          : 'https://www.youtube.com/results?search_query=${Uri.encodeComponent(cleanTopic)}';
      final messageBody = directUrl.isNotEmpty
          ? 'Here is the link: $videoUrl'
          : 'Check out this YouTube video \'$cleanTopic\': $videoUrl';

      if (timeMatch != null) {
        // Scheduled Share
        final delaySeconds = _parseDelaySeconds(timeMatch.group(0) ?? 'in 10 seconds');
        final targetTime = DateTime.now().add(Duration(seconds: delaySeconds));
        final timeStr = '${targetTime.hour % 12 == 0 ? 12 : targetTime.hour % 12}:${targetTime.minute.toString().padLeft(2, '0')} ${targetTime.hour >= 12 ? 'PM' : 'AM'}';
        final dateStr = '${targetTime.day} ${_getMonthAbbr(targetTime.month)} ${targetTime.year}';

        await waService.createScheduledJob(
          contact: recipient,
          message: messageBody,
          date: dateStr,
          time: timeStr,
          scheduledTimestamp: targetTime.millisecondsSinceEpoch,
        );
        _showSuccessSnack('Scheduled Share: "$cleanTopic" to $recipient in ${delaySeconds}s ✓');
      } else {
        // Immediate Share
        await waService.sendWhatsAppDirect(contact: recipient, message: messageBody);
        _showSuccessSnack('Shared "$cleanTopic" to $recipient on WhatsApp ✓');
      }
    }
    // ─── 2. YouTube Play & Smart Filter Search ─────────────────────────────────
    else if (lower.startsWith('play ') || lower.startsWith('watch ') || lower.startsWith('stream ') || (lower.contains('youtube') && (lower.contains('play') || lower.contains('search')))) {
      var query = lower;
      final stripPatterns = [
        'play', 'watch', 'stream', 'video of', 'video', 'on youtube', 'in youtube', 'youtube',
        'on phone', 'on android', 'open', 'search for', 'search in', 'search',
        'high view', 'highest view', 'highest views', 'most viewed', 'most views',
        'most popular', 'popular', 'trending', 'recent', 'latest', 'newest', 'new',
        'top', 'best', 'relevant'
      ];
      for (final p in stripPatterns) {
        query = query.replaceAll(RegExp('\\b$p\\b', caseSensitive: false), '');
      }
      final cleanQuery = query.replaceAll(RegExp(r'^(?:for|about|search|of)\s+', caseSensitive: false), '').trim();
      final finalQuery = cleanQuery.isEmpty ? 'lofi beats' : cleanQuery;
      final url = 'https://www.youtube.com/results?search_query=${Uri.encodeComponent(finalQuery)}';

      await waService.launchNativeApp('youtube', url: url);
      _showSuccessSnack('Playing "$finalQuery" on YouTube ✓');
    }
    // ─── 3. Scheduled WhatsApp Messaging ──────────────────────────────────────
    else if (lower.contains('whatsapp') && (lower.contains(' in ') || lower.contains(' at ') || lower.contains('schedule'))) {
      final timeMatch = RegExp(r'\b(?:in\s+(\d+)\s*(sec|seconds|second|min|mins|minutes|minute|hour|hours)|at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))\b', caseSensitive: false).firstMatch(text);
      final delaySeconds = timeMatch != null ? _parseDelaySeconds(timeMatch.group(0)!) : 10;
      final targetTime = DateTime.now().add(Duration(seconds: delaySeconds));

      // Extract Recipient
      final recMatch = RegExp(r'\bto\s+([a-zA-Z0-9_+\s]+?)(?=\s+in\s+\d+|\s+at\s+\d+|\s*$)', caseSensitive: false).firstMatch(text);
      final recipient = recMatch?.group(1)?.trim() ?? 'Contact';

      // Extract Message
      var msg = 'Hello from NEXA';
      final quoted = RegExp('["\']([^"\']+)["\']').firstMatch(text);
      if (quoted != null) {
        msg = quoted.group(1)!;
      } else {
        final sayingMatch = RegExp(r'\bsaying\s+(.+)$', caseSensitive: false).firstMatch(text);
        if (sayingMatch != null) {
          msg = sayingMatch.group(1)!;
        } else {
          final hiMatch = RegExp(r'\b(?:message|send)\s+([a-zA-Z0-9_\s]+?)\s+to\b', caseSensitive: false).firstMatch(text);
          if (hiMatch != null) msg = hiMatch.group(1)!.trim();
        }
      }

      final timeStr = '${targetTime.hour % 12 == 0 ? 12 : targetTime.hour % 12}:${targetTime.minute.toString().padLeft(2, '0')} ${targetTime.hour >= 12 ? 'PM' : 'AM'}';
      final dateStr = '${targetTime.day} ${_getMonthAbbr(targetTime.month)} ${targetTime.year}';

      await waService.createScheduledJob(
        contact: recipient,
        message: msg,
        date: dateStr,
        time: timeStr,
        scheduledTimestamp: targetTime.millisecondsSinceEpoch,
      );
      _showSuccessSnack('Scheduled WhatsApp to $recipient in ${delaySeconds}s ✓');
    }
    // ─── 4. Direct WhatsApp Messaging (Single & Multi-Contact) ─────────────────
    else if (lower.contains('whatsapp') && (lower.contains('send') || lower.contains('message') || lower.contains('to '))) {
      // Check multi-recipient: 'to "hello" to jeskin and "hi" to anroe'
      final multiMatches = RegExp('(?:and\\s+)?(?:send\\s+)?(?:whatsapp\\s+)?(?:message\\s+)?(?:to\\s+)?["\']([^"\']+)["\']\\s+to\\s+([a-zA-Z0-9_+\\s]+?)(?=\\s+and\\s+send|\\s+and\\s+["\']|\\s*\$)', caseSensitive: false).allMatches(text).toList();

      if (multiMatches.isNotEmpty) {
        for (final m in multiMatches) {
          final msg = m.group(1)?.trim() ?? '';
          final contact = m.group(2)?.trim() ?? '';
          if (contact.isNotEmpty && msg.isNotEmpty) {
            await waService.sendWhatsAppDirect(contact: contact, message: msg);
          }
        }
        _showSuccessSnack('Dispatched WhatsApp to ${multiMatches.length} contacts ✓');
      } else {
        // Single Recipient
        final recMatch = RegExp(r'\bto\s+([a-zA-Z0-9_+\s]+?)(?:\s+in\s+whatsapp|\s+on\s+whatsapp|\s*$)', caseSensitive: false).firstMatch(text);
        final recipient = recMatch?.group(1)?.trim() ?? 'Contact';

        var msg = 'Hello from NEXA';
        final quoted = RegExp('["\']([^"\']+)["\']').firstMatch(text);
        if (quoted != null) {
          msg = quoted.group(1)!;
        } else {
          final sayingMatch = RegExp(r'\bsaying\s+(.+)$', caseSensitive: false).firstMatch(text);
          if (sayingMatch != null) {
            msg = sayingMatch.group(1)!;
          } else {
            final msgMatch = RegExp(r'\b(?:message|send)\s+([a-zA-Z0-9_\s]+?)\s+to\b', caseSensitive: false).firstMatch(text);
            if (msgMatch != null) msg = msgMatch.group(1)!.trim();
          }
        }

        await waService.sendWhatsAppDirect(contact: recipient, message: msg);
        _showSuccessSnack('Sent WhatsApp to $recipient: "$msg" ✓');
      }
    }
    // ─── 5. App & Process Scanning Commands ──────────────────────────────────
    else if ((lower.contains('scan') && (lower.contains('app') || lower.contains('installed') || lower.contains('device'))) || lower == 'list apps' || lower == 'show apps' || lower == 'all apps' || lower == 'installed apps') {
      _showInstalledAppsModal(context, waService);
      _showSuccessSnack('Scanning all installed apps on device...');
    }
    else if (lower.contains('process') || lower.contains('running app') || lower == 'list processes' || lower == 'show processes' || lower == 'system processes') {
      _showRunningProcessesModal(context, waService);
      _showSuccessSnack('Scanning active running processes on device...');
    }
    // ─── 6. AI Keyboard & Chatbox Enhancer ──────────────────────────────────
    else if (lower.contains('keyboard') || lower.contains('grammar') || lower.contains('chatbox') || lower.contains('enhance text') || lower.contains('enhancer')) {
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const AiKeyboardScreen()),
      );
      _showSuccessSnack('Opening NEXA AI Keyboard & Enhancer Studio ✓');
    }
    // ─── 7. Direct App Launch (e.g. "open instagram", "open camera", "open spotify") ──
    else if (lower.startsWith('open ') || lower.startsWith('launch ') || lower.startsWith('start ') || lower.startsWith('go to ')) {
      final appName = lower
          .replaceAll(RegExp(r'^(?:open|launch|start|go to)\s+', caseSensitive: false), '')
          .replaceAll(RegExp(r'\s+(?:app|on phone|on android|please)$', caseSensitive: false), '')
          .trim();

      if (appName.isNotEmpty && !appName.contains('whatsapp message')) {
        final success = await waService.launchNativeApp(appName);
        if (success) {
          _showSuccessSnack('Launched ${appName.toUpperCase()} ✓');
        }
      }
    }

    // ─── 7. Submit to Agent Service for AI telemetry & activity stream ─────────
    agent.submitGoal(text);
  }

  void _showInstalledAppsModal(BuildContext context, ScheduledWhatsAppService waService) async {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        String searchQuery = '';
        return StatefulBuilder(
          builder: (ctx, setModalState) {
            return FutureBuilder<List<Map<String, dynamic>>>(
              future: waService.scanInstalledApps(includeSystem: true),
              builder: (ctx, snapshot) {
                final allApps = snapshot.data ?? [];
                final filtered = searchQuery.isEmpty
                    ? allApps
                    : allApps.where((a) =>
                        (a['name'] ?? '').toString().toLowerCase().contains(searchQuery.toLowerCase()) ||
                        (a['packageName'] ?? '').toString().toLowerCase().contains(searchQuery.toLowerCase())).toList();

                return Container(
                  height: MediaQuery.of(context).size.height * 0.85,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F121C),
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                    border: Border.all(color: const Color(0xFF00F2FE).withValues(alpha: 0.3)),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF00F2FE).withValues(alpha: 0.15),
                        blurRadius: 30,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      // Top Handle
                      Container(
                        margin: const EdgeInsets.only(top: 12),
                        width: 44,
                        height: 4,
                        decoration: BoxDecoration(
                          color: Colors.white24,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: const Color(0xFF00F2FE).withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: const Icon(Icons.apps_rounded, color: Color(0xFF00F2FE), size: 22),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Installed Applications',
                                    style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                                  ),
                                  Text(
                                    '${allApps.length} packages discovered on device',
                                    style: const TextStyle(color: Colors.white54, fontSize: 12),
                                  ),
                                ],
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close_rounded, color: Colors.white70),
                              onPressed: () => Navigator.pop(ctx),
                            ),
                          ],
                        ),
                      ),
                      // Search Bar
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 4.0),
                        child: TextField(
                          onChanged: (val) => setModalState(() => searchQuery = val),
                          style: const TextStyle(color: Colors.white, fontSize: 14),
                          decoration: InputDecoration(
                            hintText: 'Search applications or packages...',
                            hintStyle: const TextStyle(color: Colors.white38, fontSize: 13),
                            prefixIcon: const Icon(Icons.search_rounded, color: Color(0xFF00F2FE), size: 20),
                            filled: true,
                            fillColor: const Color(0xFF181C2B),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      // App List
                      Expanded(
                        child: snapshot.connectionState == ConnectionState.waiting
                            ? const Center(child: CircularProgressIndicator(color: Color(0xFF00F2FE)))
                            : filtered.isEmpty
                                ? const Center(child: Text('No applications found', style: TextStyle(color: Colors.white54)))
                                : ListView.builder(
                                    itemCount: filtered.length,
                                    itemBuilder: (ctx, i) {
                                      final app = filtered[i];
                                      final name = app['name'] ?? 'App';
                                      final pkg = app['packageName'] ?? '';
                                      final isSys = app['isSystem'] == true;
                                      final hasLauncher = app['hasLauncher'] == true;

                                      return Container(
                                        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                                        padding: const EdgeInsets.all(12),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF141824),
                                          borderRadius: BorderRadius.circular(12),
                                          border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
                                        ),
                                        child: Row(
                                          children: [
                                            Container(
                                              width: 40,
                                              height: 40,
                                              decoration: BoxDecoration(
                                                color: (isSys ? Colors.purpleAccent : const Color(0xFF00F2FE)).withValues(alpha: 0.15),
                                                borderRadius: BorderRadius.circular(10),
                                              ),
                                              child: Icon(
                                                isSys ? Icons.settings_applications_rounded : Icons.android_rounded,
                                                color: isSys ? Colors.purpleAccent : const Color(0xFF00F2FE),
                                                size: 22,
                                              ),
                                            ),
                                            const SizedBox(width: 12),
                                            Expanded(
                                              child: Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                  Text(
                                                    name,
                                                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                                                    maxLines: 1,
                                                    overflow: TextOverflow.ellipsis,
                                                  ),
                                                  const SizedBox(height: 2),
                                                  Text(
                                                    pkg,
                                                    style: const TextStyle(color: Colors.white38, fontSize: 11),
                                                    maxLines: 1,
                                                    overflow: TextOverflow.ellipsis,
                                                  ),
                                                ],
                                              ),
                                            ),
                                            if (hasLauncher)
                                              ElevatedButton(
                                                style: ElevatedButton.styleFrom(
                                                  backgroundColor: const Color(0xFF00F2FE).withValues(alpha: 0.2),
                                                  foregroundColor: const Color(0xFF00F2FE),
                                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                                  elevation: 0,
                                                ),
                                                onPressed: () {
                                                  waService.launchNativeApp(pkg);
                                                  Navigator.pop(ctx);
                                                  _showSuccessSnack('Launching $name...');
                                                },
                                                child: const Text('Open', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                              ),
                                          ],
                                        ),
                                      );
                                    },
                                  ),
                      ),
                    ],
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  void _showRunningProcessesModal(BuildContext context, ScheduledWhatsAppService waService) async {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return FutureBuilder<Map<String, dynamic>>(
          future: waService.scanRunningProcesses(),
          builder: (ctx, snapshot) {
            final data = snapshot.data ?? {};
            final procs = (data['processes'] as List?)?.cast<Map<String, dynamic>>() ?? [];
            final totalRamMb = ((data['total_ram_bytes'] as num?)?.toDouble() ?? 0) / (1024 * 1024);
            final usedRamMb = ((data['used_ram_bytes'] as num?)?.toDouble() ?? 0) / (1024 * 1024);
            final ramPercent = (data['ram_percent'] as num?)?.toDouble() ?? 0.0;

            return Container(
              height: MediaQuery.of(context).size.height * 0.85,
              decoration: BoxDecoration(
                color: const Color(0xFF0F121C),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                border: Border.all(color: const Color(0xFF4FACFE).withValues(alpha: 0.3)),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF4FACFE).withValues(alpha: 0.15),
                    blurRadius: 30,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: Column(
                children: [
                  Container(
                    margin: const EdgeInsets.only(top: 12),
                    width: 44,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF4FACFE).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Icon(Icons.memory_rounded, color: Color(0xFF4FACFE), size: 22),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'System Process Monitor',
                                style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                              Text(
                                '${procs.length} active processes | RAM: ${usedRamMb.toStringAsFixed(0)} / ${totalRamMb.toStringAsFixed(0)} MB (${ramPercent.toStringAsFixed(1)}%)',
                                style: const TextStyle(color: Colors.white54, fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close_rounded, color: Colors.white70),
                          onPressed: () => Navigator.pop(ctx),
                        ),
                      ],
                    ),
                  ),
                  // RAM Progress Bar
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 4.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: (ramPercent / 100.0).clamp(0.0, 1.0),
                            backgroundColor: Colors.white12,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              ramPercent > 85 ? Colors.redAccent : const Color(0xFF4FACFE),
                            ),
                            minHeight: 6,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  // Process List
                  Expanded(
                    child: snapshot.connectionState == ConnectionState.waiting
                        ? const Center(child: CircularProgressIndicator(color: Color(0xFF4FACFE)))
                        : procs.isEmpty
                            ? const Center(child: Text('No active processes found', style: TextStyle(color: Colors.white54)))
                            : ListView.builder(
                                itemCount: procs.length,
                                itemBuilder: (ctx, i) {
                                  final p = procs[i];
                                  final name = p['name'] ?? 'Process';
                                  final pName = p['processName'] ?? '';
                                  final pid = p['pid'] ?? 0;
                                  final importance = p['importance'] ?? 'Active';
                                  final memMb = (p['memoryUsageMb'] as num?)?.toDouble() ?? 0.0;

                                  return Container(
                                    margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF141824),
                                      borderRadius: BorderRadius.circular(12),
                                      border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
                                    ),
                                    child: Row(
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: Colors.white10,
                                            borderRadius: BorderRadius.circular(6),
                                          ),
                                          child: Text(
                                            'PID $pid',
                                            style: const TextStyle(color: Color(0xFF00F2FE), fontSize: 11, fontWeight: FontWeight.bold),
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                name,
                                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                              const SizedBox(height: 2),
                                              Text(
                                                '$pName • $importance',
                                                style: const TextStyle(color: Colors.white38, fontSize: 11),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                            ],
                                          ),
                                        ),
                                        Text(
                                          '${memMb.toStringAsFixed(1)} MB',
                                          style: const TextStyle(color: Color(0xFF4FACFE), fontWeight: FontWeight.bold, fontSize: 12),
                                        ),
                                      ],
                                    ),
                                  );
                                },
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

  int _parseDelaySeconds(String timeStr) {
    final lower = timeStr.toLowerCase();
    final numMatch = RegExp(r'\d+').firstMatch(lower);
    final val = numMatch != null ? int.tryParse(numMatch.group(0)!) ?? 10 : 10;

    if (lower.contains('min')) return val * 60;
    if (lower.contains('hour')) return val * 3600;
    return val;
  }

  String _getMonthAbbr(int month) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return (month >= 1 && month <= 12) ? months[month - 1] : 'Jan';
  }

  void _showSuccessSnack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.check_circle_outline_rounded, color: Color(0xFF00F2FE), size: 18),
            const SizedBox(width: 8),
            Expanded(child: Text(message, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
          ],
        ),
        backgroundColor: const Color(0xFF141824),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final agent = context.watch<AgentService>();
    final sys = context.watch<SystemMonitorService>();
    final isMobile = MediaQuery.of(context).size.width < 800;

    return Scaffold(
      backgroundColor: NexaTheme.bgDeep,
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Stack(
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                child: Column(
                  children: [
                    // Top Telemetry Header
                    SystemTelemetryBar(
                      cpuPercent: sys.cpuPercent,
                      ramPercent: sys.memoryPercent,
                      diskPercent: sys.diskPercent,
                      activeWindow: sys.activeWindow,
                      isConnected: true,
                      onSettingsPressed: _openSettings,
                      onAiKeyboardPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                              builder: (context) => const AiKeyboardScreen()),
                        );
                      },
                      onAutoReplyPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                              builder: (context) => const AutoReplyScreen()),
                        );
                      },
                    ),

                    const SizedBox(height: 16),

                    // Main Content Body (Responsive)
                    Expanded(
                      child: isMobile
                          ? _buildMobileLayout(agent)
                          : _buildDesktopLayout(agent),
                    ),

                    const SizedBox(height: 16),

                    // Bottom Command Input Bar
                    CommandInputBar(
                      controller: _chatInputController,
                      onSubmit: _handleGoalSubmission,
                      onVoicePressed: _toggleVoice,
                      onStopPressed: agent.stopAgent,
                      isWorking: agent.state.isActive,
                      isListening: _isListeningVoice,
                    ),
                  ],
                ),
              ),

              // Confirmation Dialog Overlay if needed
              if (agent.pendingConfirmation != null)
                ConfirmationDialogWidget(
                  request: agent.pendingConfirmation!,
                  onRespond: (approved) => agent.confirmAction(approved),
                ),
            ],
          ),
        ),
      ),
    );
  }

  /// Desktop Layout (Side-by-side)
  Widget _buildDesktopLayout(AgentService agent) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Left / Center Area: AI Core & Task Card
        Expanded(
          flex: 6,
          child: Column(
            children: [
              // AI Core
              Expanded(
                child: Center(
                  child: SingleChildScrollView(
                    child: AICoreWidget(
                      state: agent.state,
                      message: agent.statusMessage,
                      size: 260,
                    ),
                  ),
                ),
              ),

              // Task Progress Card if active
              if (agent.activeTask != null) ...[
                const SizedBox(height: 16),
                TaskCardWidget(
                  task: agent.activeTask!,
                  onStopPressed: agent.stopAgent,
                ),
              ],
            ],
          ),
        ),

        const SizedBox(width: 16),

        // Right Area: Agent Activity Feed
        Expanded(
          flex: 4,
          child: ActivityPanel(activities: agent.activityFeed),
        ),
      ],
    );
  }

  /// Mobile / Android Layout (Stacked vertical view with Tab/Page scroll)
  Widget _buildMobileLayout(AgentService agent) {
    return SingleChildScrollView(
      child: Column(
        children: [
          const SizedBox(height: 20),

          // AI Core
          AICoreWidget(
            state: agent.state,
            message: agent.statusMessage,
            size: 200,
          ),

          const SizedBox(height: 20),

          // Active Task Card if present
          if (agent.activeTask != null) ...[
            TaskCardWidget(
              task: agent.activeTask!,
              onStopPressed: agent.stopAgent,
            ),
            const SizedBox(height: 16),
          ],

          // Activity Feed
          SizedBox(
            height: 280,
            child: ActivityPanel(activities: agent.activityFeed),
          ),
        ],
      ),
    );
  }
}
