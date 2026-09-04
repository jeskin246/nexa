import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../manager/auto_reply_manager.dart';

class EditMessageScreen extends StatefulWidget {
  const EditMessageScreen({super.key});

  @override
  State<EditMessageScreen> createState() => _EditMessageScreenState();
}

class _EditMessageScreenState extends State<EditMessageScreen> {
  late TextEditingController _templateController;
  late TextEditingController _usernameController;

  @override
  void initState() {
    super.initState();
    final manager = Provider.of<AutoReplyManager>(context, listen: false);
    _templateController =
        TextEditingController(text: manager.settings.replyTemplate);
    _usernameController =
        TextEditingController(text: manager.settings.username);
  }

  @override
  void dispose() {
    _templateController.dispose();
    _usernameController.dispose();
    super.dispose();
  }

  void _insertVariable(String variable) {
    final text = _templateController.text;
    final selection = _templateController.selection;
    final newText = text.replaceRange(
      selection.start < 0 ? text.length : selection.start,
      selection.end < 0 ? text.length : selection.end,
      variable,
    );
    _templateController.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(
        offset: (selection.start < 0 ? text.length : selection.start) +
            variable.length,
      ),
    );
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final manager = Provider.of<AutoReplyManager>(context);
    final String currentUsername = _usernameController.text.isNotEmpty
        ? _usernameController.text
        : manager.settings.username;

    final String livePreviewText = manager.replaceVariables(
      _templateController.text,
      sender: 'John',
      appName: 'WhatsApp',
      username: currentUsername,
    );

    return Scaffold(
      backgroundColor: const Color(0xFF0D0F18),
      appBar: AppBar(
        backgroundColor: const Color(0xFF141824),
        title: const Text(
          'EDIT AUTO-REPLY',
          style: TextStyle(
            color: Color(0xFF00F2FE),
            fontWeight: FontWeight.bold,
            letterSpacing: 1.5,
            fontSize: 18,
          ),
        ),
        iconTheme: const IconThemeData(color: Color(0xFF00F2FE)),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Username Field
            const Text(
              'Your Name / Username',
              style: TextStyle(
                color: Colors.white70,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF161B2B),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF2E3650)),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: TextField(
                controller: _usernameController,
                style: const TextStyle(color: Colors.white, fontSize: 16),
                decoration: const InputDecoration(
                  border: InputBorder.none,
                  hintText: 'e.g. Jeskin',
                  hintStyle: TextStyle(color: Colors.white38),
                ),
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(height: 24),

            // Reply Message Field
            const Text(
              'Message Template',
              style: TextStyle(
                color: Colors.white70,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF161B2B),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF2E3650)),
              ),
              padding: const EdgeInsets.all(12),
              child: TextField(
                controller: _templateController,
                maxLines: 5,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  height: 1.4,
                ),
                decoration: const InputDecoration(
                  border: InputBorder.none,
                  hintText: 'Enter auto-reply template...',
                  hintStyle: TextStyle(color: Colors.white38),
                ),
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(height: 16),

            // Variables Chips
            const Text(
              'Variables (Tap to Insert)',
              style: TextStyle(
                color: Colors.white70,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                _buildVariableChip('(username)', 'Your name'),
                _buildVariableChip('(sender)', 'Sender name'),
                _buildVariableChip('(app)', 'App name'),
              ],
            ),
            const SizedBox(height: 28),

            // Live Preview Card
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF121728),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: const Color(0xFF00F2FE).withValues(alpha: 0.4),
                  width: 1.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF00F2FE).withValues(alpha: 0.1),
                    blurRadius: 12,
                    spreadRadius: 2,
                  )
                ],
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.remove_red_eye_outlined,
                          color: Color(0xFF00F2FE), size: 18),
                      SizedBox(width: 8),
                      Text(
                        'LIVE PREVIEW',
                        style: TextStyle(
                          color: Color(0xFF00F2FE),
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                  const Divider(color: Color(0xFF2E3650), height: 20),
                  Text(
                    '"$livePreviewText"',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      height: 1.5,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // Save Button
            ElevatedButton(
              onPressed: () {
                manager.updateUsername(_usernameController.text.trim());
                manager.updateTemplate(_templateController.text.trim());

                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Auto-Reply Message Saved Successfully!'),
                    backgroundColor: Color(0xFF00C853),
                  ),
                );
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00F2FE),
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                elevation: 4,
              ),
              child: const Text(
                'SAVE MESSAGE',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                  fontSize: 16,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVariableChip(String code, String label) {
    return ActionChip(
      backgroundColor: const Color(0xFF1E2638),
      side: const BorderSide(color: Color(0xFF3B4666)),
      label: Text(
        '[ $code ]',
        style: const TextStyle(
          color: Color(0xFF00F2FE),
          fontWeight: FontWeight.bold,
          fontSize: 13,
        ),
      ),
      onPressed: () => _insertVariable(code),
    );
  }
}
