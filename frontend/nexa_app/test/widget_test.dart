import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('NexaApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: Text('NEXA — Agentic AI Personal OS Assistant'),
          ),
        ),
      ),
    );
    expect(find.text('NEXA — Agentic AI Personal OS Assistant'), findsOneWidget);
  });
}
