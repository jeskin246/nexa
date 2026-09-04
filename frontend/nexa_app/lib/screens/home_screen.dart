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

    // 1. Direct On-Device App Launch Intent (e.g. "open instagram", "launch whatsapp", "open camera", "open youtube")
    if (lower.startsWith('open ') || lower.startsWith('launch ') || lower.startsWith('start ') || lower.startsWith('go to ')) {
      final appName = lower
          .replaceAll(RegExp(r'^(?:open|launch|start|go to)\s+', caseSensitive: false), '')
          .replaceAll(RegExp(r'\s+(?:app|on phone|on android|please)$', caseSensitive: false), '')
          .trim();

      if (appName.isNotEmpty && !appName.contains('whatsapp message')) {
        final success = await waService.launchNativeApp(appName);
        if (mounted && success) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Row(
                children: [
                  const Icon(Icons.rocket_launch_rounded, color: Color(0xFF00F2FE), size: 18),
                  const SizedBox(width: 8),
                  Text('Launched ${appName.toUpperCase()} ✓', style: const TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              backgroundColor: const Color(0xFF141824),
              behavior: SnackBarBehavior.floating,
              duration: const Duration(seconds: 2),
            ),
          );
        }
      }
    } else if (lower.startsWith('play ') && lower.contains('youtube')) {
      final query = lower
          .replaceAll('play ', '')
          .replaceAll('on youtube', '')
          .replaceAll('in youtube', '')
          .replaceAll('video of', '')
          .replaceAll('video', '')
          .trim();
      final url = 'https://www.youtube.com/results?search_query=${Uri.encodeComponent(query)}';
      await waService.launchNativeApp('youtube', url: url);
    }

    // 2. Submit to Agent Service for AI execution / activity telemetry
    agent.submitGoal(text);
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
