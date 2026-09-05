import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/scheduled_whatsapp_service.dart';

class AiKeyboardScreen extends StatefulWidget {
  const AiKeyboardScreen({super.key});

  @override
  State<AiKeyboardScreen> createState() => _AiKeyboardScreenState();
}

class _AiKeyboardScreenState extends State<AiKeyboardScreen> {
  final TextEditingController _inputController = TextEditingController(
    text: 'i will come tommorow for meting pls check docs',
  );
  String _selectedTone = 'professional';
  String? _selectedLanguage;
  String _outputResult = '';
  bool _isLoading = false;
  bool _floatingAiEnabled = true;

  final List<Map<String, dynamic>> _tones = [
    {'id': 'grammar_fix', 'label': 'Fix Grammar', 'icon': Icons.auto_fix_high, 'color': Color(0xFF00F2FE)},
    {'id': 'professional', 'label': 'Professional', 'icon': Icons.business_center_outlined, 'color': Color(0xFF4FACFE)},
    {'id': 'friendly', 'label': 'Friendly', 'icon': Icons.sentiment_satisfied_alt, 'color': Color(0xFF43E97B)},
    {'id': 'concise', 'label': 'Concise', 'icon': Icons.bolt, 'color': Color(0xFFFFB300)},
    {'id': 'casual', 'label': 'Casual', 'icon': Icons.chat_bubble_outline, 'color': Color(0xFFFA709A)},
  ];

  final List<Map<String, String>> _languages = [
    {'id': 'tamil', 'name': 'தமிழ் (Tamil)', 'flag': '🇮🇳'},
    {'id': 'hindi', 'name': 'हिंदी (Hindi)', 'flag': '🇮🇳'},
    {'id': 'spanish', 'name': 'Spanish', 'flag': '🇪🇸'},
    {'id': 'french', 'name': 'French', 'flag': '🇫🇷'},
    {'id': 'german', 'name': 'German', 'flag': '🇩🇪'},
  ];

  @override
  void initState() {
    super.initState();
    _checkInitialState();
  }

  Future<void> _checkInitialState() async {
    final service = Provider.of<ScheduledWhatsAppService>(context, listen: false);
    final enabled = await service.isFloatingAiEnabled();
    if (mounted) {
      setState(() {
        _floatingAiEnabled = enabled;
      });
    }
  }

  @override
  void dispose() {
    _inputController.dispose();
    super.dispose();
  }

  Future<void> _runEnhancement() async {
    final text = _inputController.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _isLoading = true;
      _outputResult = '';
    });

    final service = Provider.of<ScheduledWhatsAppService>(context, listen: false);
    final result = await service.enhanceText(
      text: text,
      tone: _selectedTone,
      targetLanguage: _selectedLanguage,
    );

    if (mounted) {
      setState(() {
        _isLoading = false;
        _outputResult = result;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E17),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111827),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white70, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF00F2FE), Color(0xFF4FACFE)],
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.keyboard, color: Colors.black, size: 18),
            ),
            const SizedBox(width: 10),
            const Text(
              'NEXA AI Keyboard & Enhancer',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ─── Header Card ────────────────────────────────────────────────
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFF00F2FE).withValues(alpha: 0.15),
                    const Color(0xFF4FACFE).withValues(alpha: 0.05),
                  ],
                ),
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
                      const Icon(Icons.auto_awesome, color: Color(0xFF00F2FE), size: 20),
                      const SizedBox(width: 8),
                      const Text(
                        'Universal In-Chatbox AI Helper',
                        style: TextStyle(
                          color: Color(0xFF00F2FE),
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF00F2FE).withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Text(
                          'ACTIVE',
                          style: TextStyle(
                            color: Color(0xFF00F2FE),
                            fontWeight: FontWeight.bold,
                            fontSize: 10,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Enhance text, fix grammar, rewrite in different tones, and translate live in WhatsApp, Instagram, Telegram, SMS, or any chat app without switching screens!',
                    style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13, height: 1.4),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // ─── Quick Controls Card ─────────────────────────────────────────
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF131C2E),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
              ),
              child: Column(
                children: [
                  // Floating Chatbox Pill Toggle
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0xFF4FACFE).withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.chat_bubble_outline, color: Color(0xFF4FACFE), size: 20),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Floating AI Chatbox Pill',
                              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14),
                            ),
                            Text(
                              'Shows ✨ NEXA AI overlay when typing in any app',
                              style: TextStyle(color: Color(0xFF64748B), fontSize: 11),
                            ),
                          ],
                        ),
                      ),
                      Switch(
                        value: _floatingAiEnabled,
                        activeThumbColor: const Color(0xFF00F2FE),
                        onChanged: (val) async {
                          final service = Provider.of<ScheduledWhatsAppService>(context, listen: false);
                          await service.toggleFloatingAiToolbar(val);
                          setState(() {
                            _floatingAiEnabled = val;
                          });
                        },
                      ),
                    ],
                  ),
                  const Divider(color: Colors.white10, height: 24),
                  // Enable NEXA AI Keyboard Button
                  InkWell(
                    onTap: () {
                      final service = Provider.of<ScheduledWhatsAppService>(context, listen: false);
                      service.openInputMethodSettings();
                    },
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF00F2FE).withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.settings_suggest, color: Color(0xFF00F2FE), size: 20),
                          const SizedBox(width: 10),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Set NEXA AI as Default Keyboard',
                                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                                ),
                                Text(
                                  'Enable in Android Language & Input Settings',
                                  style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11),
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.chevron_right, color: Color(0xFF00F2FE)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // ─── Interactive Playground / Testing Studio ─────────────────────
            const Text(
              'LIVE AI WRITING & TRANSLATION STUDIO',
              style: TextStyle(
                color: Color(0xFF64748B),
                fontSize: 12,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.1,
              ),
            ),
            const SizedBox(height: 10),

            // Input TextField
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF131C2E),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
              ),
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  TextField(
                    controller: _inputController,
                    maxLines: 3,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    decoration: const InputDecoration(
                      hintText: 'Type any message or draft here...',
                      hintStyle: TextStyle(color: Color(0xFF475569), fontSize: 14),
                      border: InputBorder.none,
                    ),
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton.icon(
                        onPressed: () => _inputController.clear(),
                        icon: const Icon(Icons.clear, size: 14, color: Color(0xFF64748B)),
                        label: const Text('Clear', style: TextStyle(color: Color(0xFF64748B), fontSize: 12)),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Tone Selection Chips
            const Text(
              'Select Tone / Style:',
              style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _tones.map((t) {
                  final isSelected = _selectedTone == t['id'] && _selectedLanguage == null;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      selected: isSelected,
                      label: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(t['icon'] as IconData, size: 14, color: isSelected ? Colors.black : t['color'] as Color),
                          const SizedBox(width: 6),
                          Text(
                            t['label'] as String,
                            style: TextStyle(
                              color: isSelected ? Colors.black : Colors.white,
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                      selectedColor: t['color'] as Color,
                      backgroundColor: const Color(0xFF1E293B),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                      onSelected: (selected) {
                        if (selected) {
                          setState(() {
                            _selectedTone = t['id'] as String;
                            _selectedLanguage = null;
                          });
                        }
                      },
                    ),
                  );
                }).toList(),
              ),
            ),

            const SizedBox(height: 12),

            // Language Translation Chips
            const Text(
              'Or Translate to Language:',
              style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _languages.map((l) {
                  final isSelected = _selectedLanguage == l['id'];
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      selected: isSelected,
                      label: Text(
                        '${l['flag']} ${l['name']}',
                        style: TextStyle(
                          color: isSelected ? Colors.black : Colors.white,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          fontSize: 12,
                        ),
                      ),
                      selectedColor: const Color(0xFF00F2FE),
                      backgroundColor: const Color(0xFF1E293B),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            _selectedLanguage = l['id'];
                            _selectedTone = 'translate';
                          } else {
                            _selectedLanguage = null;
                            _selectedTone = 'professional';
                          }
                        });
                      },
                    ),
                  );
                }).toList(),
              ),
            ),

            const SizedBox(height: 20),

            // Transform Action Button
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _runEnhancement,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00F2FE),
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 4,
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2),
                      )
                    : const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.auto_fix_high, size: 20),
                          SizedBox(width: 8),
                          Text(
                            'Enhance Text with NEXA AI',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                          ),
                        ],
                      ),
              ),
            ),

            if (_outputResult.isNotEmpty) ...[
              const SizedBox(height: 20),
              // Enhanced Output Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF00F2FE).withValues(alpha: 0.4)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.check_circle, color: Color(0xFF43E97B), size: 18),
                        const SizedBox(width: 6),
                        const Text(
                          'Enhanced Result:',
                          style: TextStyle(color: Color(0xFF43E97B), fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        const Spacer(),
                        IconButton(
                          icon: const Icon(Icons.copy, color: Color(0xFF00F2FE), size: 18),
                          tooltip: 'Copy to Clipboard',
                          onPressed: () {
                            Clipboard.setData(ClipboardData(text: _outputResult));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Copied enhanced text to clipboard!'),
                                duration: Duration(seconds: 2),
                              ),
                            );
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    SelectableText(
                      _outputResult,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 30),

            // How it works card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '💡 How to use in other apps:',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  SizedBox(height: 8),
                  Text(
                    '1. Open any chat app (WhatsApp, Instagram, Telegram, SMS, Gmail).\n'
                    '2. Tap the chatbox to start typing.\n'
                    '3. Tap the floating ✨ NEXA AI pill on the screen or use the top AI toolbar on the NEXA Keyboard.\n'
                    '4. Select your tone (Professional, Friendly, Concise) or language to auto-replace the text instantly!',
                    style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12, height: 1.5),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
