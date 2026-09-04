import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../manager/auto_reply_manager.dart';
import '../model/auto_reply_models.dart';

class ReplyHistoryScreen extends StatelessWidget {
  const ReplyHistoryScreen({super.key});

  String _formatTimestamp(DateTime dt) {
    final now = DateTime.now();
    final isToday =
        now.year == dt.year && now.month == dt.month && now.day == dt.day;
    final timeStr =
        "${dt.hour % 12 == 0 ? 12 : dt.hour % 12}:${dt.minute.toString().padLeft(2, '0')} ${dt.hour >= 12 ? 'PM' : 'AM'}";
    return isToday ? 'Today, $timeStr' : '${dt.month}/${dt.day}, $timeStr';
  }

  void _showFullMessageDialog(BuildContext context, ReplyHistoryItem item) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF141824),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            Icon(
              item.appName == 'WhatsApp'
                  ? Icons.chat
                  : item.appName == 'Instagram'
                      ? Icons.camera_alt
                      : Icons.send,
              color: const Color(0xFF00F2FE),
            ),
            const SizedBox(width: 10),
            Text(
              '${item.appName} → ${item.sender}',
              style: const TextStyle(color: Colors.white, fontSize: 16),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Status: ${item.status}',
              style: const TextStyle(
                color: Color(0xFF00C853),
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _formatTimestamp(item.timestamp),
              style: const TextStyle(color: Colors.white54, fontSize: 12),
            ),
            const Divider(color: Color(0xFF2E3650), height: 20),
            const Text(
              'Sent Message:',
              style: TextStyle(color: Colors.white70, fontSize: 13),
            ),
            const SizedBox(height: 6),
            Text(
              '"${item.sentMessage}"',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                height: 1.4,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('CLOSE',
                style: TextStyle(color: Color(0xFF00F2FE))),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final manager = Provider.of<AutoReplyManager>(context);
    final history = manager.history;

    return Scaffold(
      backgroundColor: const Color(0xFF0D0F18),
      appBar: AppBar(
        backgroundColor: const Color(0xFF141824),
        title: const Text(
          'AUTO-REPLY HISTORY',
          style: TextStyle(
            color: Color(0xFF00F2FE),
            fontWeight: FontWeight.bold,
            letterSpacing: 1.5,
            fontSize: 18,
          ),
        ),
        iconTheme: const IconThemeData(color: Color(0xFF00F2FE)),
        elevation: 0,
        actions: [
          if (history.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
              tooltip: 'Clear History',
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    backgroundColor: const Color(0xFF141824),
                    title: const Text('Clear History?',
                        style: TextStyle(color: Colors.white)),
                    content: const Text(
                      'Are you sure you want to clear all auto-reply history items?',
                      style: TextStyle(color: Colors.white70),
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(ctx),
                        child: const Text('CANCEL',
                            style: TextStyle(color: Colors.white54)),
                      ),
                      TextButton(
                        onPressed: () {
                          manager.clearHistory();
                          Navigator.pop(ctx);
                        },
                        child: const Text('CLEAR',
                            style: TextStyle(color: Colors.redAccent)),
                      ),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
      body: history.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Icon(Icons.history_toggle_off,
                      size: 64, color: Colors.white24),
                  SizedBox(height: 16),
                  Text(
                    'No Auto-Reply History Yet',
                    style: TextStyle(color: Colors.white54, fontSize: 16),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: history.length,
              itemBuilder: (context, index) {
                final item = history[index];
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF161B2B),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFF2E3650)),
                  ),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 8,
                    ),
                    leading: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E2638),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        item.appName == 'WhatsApp'
                            ? Icons.chat
                            : item.appName == 'Instagram'
                                ? Icons.camera_alt
                                : Icons.send,
                        color: const Color(0xFF00F2FE),
                        size: 22,
                      ),
                    ),
                    title: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          item.appName,
                          style: const TextStyle(
                            color: Color(0xFF00F2FE),
                            fontWeight: FontWeight.bold,
                            fontSize: 14,
                          ),
                        ),
                        Text(
                          _formatTimestamp(item.timestamp),
                          style: const TextStyle(
                            color: Colors.white38,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text(
                          item.sender,
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          '"${item.sentMessage}"',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 13,
                            height: 1.3,
                          ),
                        ),
                        const SizedBox(height: 8),
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
                    onTap: () => _showFullMessageDialog(context, item),
                  ),
                );
              },
            ),
    );
  }
}
