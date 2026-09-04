import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import '../core/websocket_service.dart';
import '../widgets/common/animated_gradient.dart';
import '../widgets/common/glass_container.dart';
import '../widgets/common/glow_button.dart';

/// NEXA Settings & Control Center Screen.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _wsUrlController;
  String _selectedProvider = 'gemini';
  String _mediumRiskPolicy = 'ask';

  @override
  void initState() {
    super.initState();
    _wsUrlController = TextEditingController(text: NexaConstants.wsUrl);
  }

  @override
  void dispose() {
    _wsUrlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ws = context.watch<WebSocketService>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('NEXA CONTROL CENTER'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 600),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Connection Settings
                    GlassContainer(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.wifi_rounded, color: NexaTheme.accentCyan),
                              SizedBox(width: 10),
                              Text(
                                'BACKEND CONNECTION',
                                style: TextStyle(
                                  color: NexaTheme.textPrimary,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.2,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          TextField(
                            controller: _wsUrlController,
                            decoration: const InputDecoration(
                              labelText: 'WebSocket Server URL',
                              hintText: 'ws://10.0.2.2:8000/ws (Android) or ws://localhost:8000/ws',
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Text(
                                'Status: ${ws.state.name.toUpperCase()}',
                                style: TextStyle(
                                  color: ws.isConnected
                                      ? NexaTheme.successGreen
                                      : NexaTheme.warningAmber,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              const Spacer(),
                              GlowButton(
                                text: 'Reconnect',
                                height: 36,
                                onPressed: () {
                                  ws.connect(url: _wsUrlController.text.trim());
                                },
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // AI Provider Configuration
                    GlassContainer(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.psychology_outlined, color: NexaTheme.accentPurple),
                              SizedBox(width: 10),
                              Text(
                                'AI PROVIDER',
                                style: TextStyle(
                                  color: NexaTheme.textPrimary,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.2,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          DropdownButtonFormField<String>(
                            initialValue: _selectedProvider,
                            dropdownColor: NexaTheme.bgPanel,
                            decoration: const InputDecoration(labelText: 'Default LLM Provider'),
                            items: const [
                              DropdownMenuItem(value: 'ollama', child: Text('Ollama (Free Local Agent - No API Key)')),
                              DropdownMenuItem(value: 'deepseek', child: Text('DeepSeek API')),
                              DropdownMenuItem(value: 'groq', child: Text('Groq (Fast Llama-3.3)')),
                              DropdownMenuItem(value: 'openai', child: Text('OpenAI (GPT-4o)')),
                              DropdownMenuItem(value: 'anthropic', child: Text('Anthropic Claude 3.5')),
                              DropdownMenuItem(value: 'gemini', child: Text('Google Gemini Pro')),
                              DropdownMenuItem(value: 'local_rules', child: Text('Offline Quick Rules')),
                            ],
                            onChanged: (val) {
                              if (val != null) setState(() => _selectedProvider = val);
                            },
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Security & Permissions
                    GlassContainer(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.security_outlined, color: NexaTheme.warningAmber),
                              SizedBox(width: 10),
                              Text(
                                'SECURITY & PERMISSIONS',
                                style: TextStyle(
                                  color: NexaTheme.textPrimary,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.2,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          DropdownButtonFormField<String>(
                            initialValue: _mediumRiskPolicy,
                            dropdownColor: NexaTheme.bgPanel,
                            decoration: const InputDecoration(
                              labelText: 'Medium Risk Tools (File creation, App launch)',
                            ),
                            items: const [
                              DropdownMenuItem(value: 'ask', child: Text('Ask every time')),
                              DropdownMenuItem(value: 'auto', child: Text('Auto-approve')),
                              DropdownMenuItem(value: 'blocked', child: Text('Block all')),
                            ],
                            onChanged: (val) {
                              if (val != null) setState(() => _mediumRiskPolicy = val);
                            },
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'High Risk tools (File deletion) will ALWAYS require explicit user confirmation.',
                            style: TextStyle(color: NexaTheme.textDim, fontSize: 12),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // App Info
                    GlassContainer(
                      child: Row(
                        children: [
                          const Icon(Icons.info_outline, color: NexaTheme.textDim),
                          const SizedBox(width: 12),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: const [
                              Text(
                                '${NexaConstants.appName} v${NexaConstants.appVersion}',
                                style: TextStyle(
                                  color: NexaTheme.textPrimary,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              Text(
                                'Agentic AI Personal OS Assistant (Desktop & Android)',
                                style: TextStyle(color: NexaTheme.textDim, fontSize: 12),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
