import 'dart:async';
import 'package:flutter/material.dart';
import '../models/log_entry.dart';
import '../services/api_service.dart';
import '../widgets/terminal_log.dart';
import '../widgets/command_input.dart';
import '../widgets/quick_commands.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with TickerProviderStateMixin {
  final TextEditingController _inputCtrl = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  final ScrollController _scrollCtrl = ScrollController();
  final List<LogEntry> _logs = [];

  bool _isProcessing = false;
  bool _isConnected = false;
  bool _isListening = false;

  // Voice mode OFF by default → starts only when user clicks mic
  bool _voiceMode = false;

  Timer? _retryTimer;
  Timer? _clockTimer;
  String _clockStr = '';

  late final AnimationController _glowCtrl;
  late final Animation<double> _glowAnim;

  @override
  void initState() {
    super.initState();

    _glowCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);

    _glowAnim = Tween<double>(
      begin: 0.4,
      end: 1.0,
    ).animate(_glowCtrl);

    _updateClock();

    _clockTimer = Timer.periodic(
      const Duration(seconds: 1),
      (_) => _updateClock(),
    );

    _checkConnection(isStartup: true);

    _retryTimer = Timer.periodic(
      const Duration(seconds: 5),
      (_) => _retryIfNeeded(),
    );
  }

  @override
  void dispose() {
    _glowCtrl.dispose();
    _inputCtrl.dispose();
    _focusNode.dispose();
    _scrollCtrl.dispose();
    _retryTimer?.cancel();
    _clockTimer?.cancel();
    super.dispose();
  }

  void _updateClock() {
    final now = DateTime.now();

    setState(() {
      _clockStr =
          '${now.hour.toString().padLeft(2, '0')}:'
          '${now.minute.toString().padLeft(2, '0')}:'
          '${now.second.toString().padLeft(2, '0')}';
    });
  }

  void _addLog(LogType type, String message) {
    setState(() {
      _logs.add(
        LogEntry.now(
          type: type,
          message: message,
        ),
      );
    });

    Future.delayed(
      const Duration(milliseconds: 60),
      _scrollToBottom,
    );
  }

  void _scrollToBottom() {
    if (_scrollCtrl.hasClients) {
      _scrollCtrl.animateTo(
        _scrollCtrl.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    }
  }

  Future<void> _checkConnection({bool isStartup = false}) async {
    final ok = await ApiService.checkConnection();
    final wasConnected = _isConnected;

    setState(() {
      _isConnected = ok;
    });

    if (isStartup) {
      _addLog(LogType.sys, '⚡ FlowForge AI initialized');

      if (ok) {
        _addLog(
          LogType.success,
          '🔗 Backend connected at 127.0.0.1:8000',
        );

        // Changed message → no auto listening
        _addLog(
          LogType.sys,
          '🎤 Tap mic button to start voice mode',
        );
      } else {
        _addLog(
          LogType.error,
          '🔴 Backend not reachable — retrying...',
        );
      }
    } else if (ok && !wasConnected) {
      _addLog(
        LogType.success,
        '✅ Backend reconnected',
      );
    }
  }

  void _retryIfNeeded() {
    if (!_isConnected) {
      _checkConnection();
    }
  }

  // Starts backend listening ONLY after mic click
  Future<void> _startListening() async {
    if (_isListening ||
        _isProcessing ||
        !_isConnected ||
        !_voiceMode) {
      return;
    }

    setState(() {
      _isListening = true;
      _inputCtrl.clear();
    });

    _addLog(LogType.sys, '🎤 Listening...');

    final response = await ApiService.listenAndExecute();

    final heard = response["heard"] ?? "";
    final result = response["result"] ?? "No response";
    final options = response["options"] ?? [];

    setState(() {
      _isListening = false;
    });

    if (heard.isEmpty) {
      _addLog(
        LogType.sys,
        '⏳ Nothing heard. Tap mic again to listen.',
      );
    } else {
      _addLog(LogType.cmd, '\$ $heard');

      final isError =
          result.toLowerCase().contains('not recognized') ||
              result.toLowerCase().contains('error') ||
              result.toLowerCase().startsWith('error:');

      _addLog(
        isError ? LogType.error : LogType.success,
        result,
      );

      if (options.isNotEmpty) {
        for (int i = 0; i < options.length; i++) {
          _addLog(
            LogType.sys,
            '  ${i + 1}. ${options[i]}',
          );
        }

        _addLog(
          LogType.sys,
          "👉 Say 'play 1', 'play 2'... to play",
        );
      }
    }

    // Removed auto restart
  }

  Future<void> _sendCommand(String cmd) async {
    cmd = cmd.trim();

    if (cmd.isEmpty || _isProcessing || !_isConnected) {
      return;
    }

    setState(() {
      _isProcessing = true;
      _inputCtrl.clear();
    });

    _addLog(LogType.cmd, '\$ $cmd');
    _addLog(LogType.sys, 'Executing command...');

    final response = await ApiService.sendCommand(cmd);

    String result = response["result"] ?? "No response";
    List options = response["options"] ?? [];

    final isError =
        result.toLowerCase().contains('not recognized') ||
            result.toLowerCase().contains('error') ||
            result.toLowerCase().startsWith('error:');

    _addLog(
      isError ? LogType.error : LogType.success,
      result,
    );

    if (options.isNotEmpty) {
      for (int i = 0; i < options.length; i++) {
        _addLog(
          LogType.sys,
          '  ${i + 1}. ${options[i]}',
        );
      }

      _addLog(
        LogType.sys,
        "👉 Say 'play 1', 'play 2'... to play",
      );
    }

    setState(() {
      _isProcessing = false;
    });

    _focusNode.requestFocus();
  }

  // Mic button controls listening manually
  Future<void> _toggleMic() async {
    if (_isListening) {
      setState(() {
        _isListening = false;
        _voiceMode = false;
      });

      _addLog(
        LogType.sys,
        '🔇 Voice mode stopped',
      );
    } else {
      setState(() {
        _voiceMode = true;
      });

      _addLog(
        LogType.sys,
        '🎤 Voice mode started',
      );

      _startListening();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(),

            Expanded(
              child: TerminalLog(
                logs: _logs,
                scrollController: _scrollCtrl,
              ),
            ),

            QuickCommands(
              onCommand: _sendCommand,
            ),

            CommandInput(
              controller: _inputCtrl,
              focusNode: _focusNode,
              isProcessing: _isProcessing,
              isConnected: _isConnected,
              isListening: _isListening,
              onSend: () => _sendCommand(_inputCtrl.text),
              onMicTap: _toggleMic,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    return AnimatedBuilder(
      animation: _glowAnim,
      builder: (_, __) => Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 10,
        ),
        decoration: BoxDecoration(
          color: AppColors.surface,
          border: const Border(
            bottom: BorderSide(
              color: AppColors.border,
            ),
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.accentBlue.withValues(
                alpha: 0.06 * _glowAnim.value,
              ),
              blurRadius: 12,
            ),
          ],
        ),
        child: Row(
          children: [
            _glowingDot(
              _isConnected
                  ? AppColors.successGreen
                  : AppColors.errorRed,
            ),

            const SizedBox(width: 10),

            const Text(
              '⚡ FlowForge AI',
              style: TextStyle(
                fontFamily: 'monospace',
                fontSize: 14,
                color: AppColors.accentBlue,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),

            const Spacer(),

            _statusPill(
              _isListening
                  ? '🎤 Listening'
                  : _voiceMode
                      ? '🎤 Voice On'
                      : '🔇 Voice Off',
              _voiceMode
                  ? AppColors.successGreen
                  : AppColors.textSecondary,
            ),

            const SizedBox(width: 8),

            _statusPill(
              _isConnected
                  ? '🟢 Connected'
                  : '🔴 Disconnected',
              _isConnected
                  ? AppColors.successGreen
                  : AppColors.errorRed,
            ),

            const SizedBox(width: 10),

            Text(
              _clockStr,
              style: TextStyle(
                fontFamily: 'monospace',
                fontSize: 11,
                color: AppColors.textSecondary.withValues(
                  alpha: 0.7,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _glowingDot(Color color) {
    return AnimatedBuilder(
      animation: _glowAnim,
      builder: (_, __) => Container(
        width: 8,
        height: 8,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: color,
          boxShadow: [
            BoxShadow(
              color: color.withValues(
                alpha: 0.6 * _glowAnim.value,
              ),
              blurRadius: 8,
              spreadRadius: 1,
            ),
          ],
        ),
      ),
    );
  }

  Widget _statusPill(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 3,
      ),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        color: color.withValues(alpha: 0.1),
        border: Border.all(
          color: color.withValues(alpha: 0.35),
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: 'monospace',
          fontSize: 10.5,
          color: color,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}