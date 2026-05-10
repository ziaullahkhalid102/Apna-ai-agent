import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/agent_provider.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const ApnaAIApp());
}

class ApnaAIApp extends StatelessWidget {
  const ApnaAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AgentProvider(),
      child: MaterialApp(
        title: 'Apna AI Agent',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.teal,
            brightness: Brightness.light,
          ),
          useMaterial3: true,
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.teal,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
        ),
        themeMode: ThemeMode.dark,
        home: const HomeScreen(),
      ),
    );
  }
}
